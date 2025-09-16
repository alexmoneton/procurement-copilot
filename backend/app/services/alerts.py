"""Alert service for matching tenders to saved filters and sending notifications."""

import uuid
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, select

from ..db.models import Tender, SavedFilter, User, EmailLog, NotifyFrequency
from ..db.crud import SavedFilterCRUD, EmailLogCRUD
from ..db.schemas import EmailLogCreate
from .email import email_service


class AlertService:
    """Service for processing alerts and sending notifications."""
    
    def __init__(self):
        self.logger = logger.bind(service="alerts")
    
    async def run_alerts_pipeline(self, db: AsyncSession) -> Dict[str, Any]:
        """Run the complete alerts pipeline."""
        self.logger.info("Starting alerts pipeline")
        
        try:
            # Get all daily filters
            daily_filters = await SavedFilterCRUD.get_daily_filters(db)
            self.logger.info(f"Found {len(daily_filters)} daily filters to process")
            
            results = {
                "processed_filters": 0,
                "emails_sent": 0,
                "emails_skipped": 0,
                "errors": 0,
                "details": []
            }
            
            for saved_filter in daily_filters:
                try:
                    filter_result = await self._process_filter(db, saved_filter)
                    results["processed_filters"] += 1
                    
                    if filter_result["status"] == "sent":
                        results["emails_sent"] += 1
                    elif filter_result["status"] == "skipped":
                        results["emails_skipped"] += 1
                    else:
                        results["errors"] += 1
                    
                    results["details"].append(filter_result)
                    
                except Exception as e:
                    self.logger.error(f"Error processing filter {saved_filter.id}: {e}")
                    results["errors"] += 1
                    results["details"].append({
                        "filter_id": str(saved_filter.id),
                        "filter_name": saved_filter.name,
                        "status": "error",
                        "error": str(e)
                    })
            
            self.logger.info(
                f"Alerts pipeline completed: {results['emails_sent']} sent, "
                f"{results['emails_skipped']} skipped, {results['errors']} errors"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Alerts pipeline failed: {e}")
            raise
    
    async def _process_filter(self, db: AsyncSession, saved_filter: SavedFilter) -> Dict[str, Any]:
        """Process a single saved filter."""
        self.logger.info(f"Processing filter: {saved_filter.name} (ID: {saved_filter.id})")
        
        # Get user for this filter
        user = await db.get(User, saved_filter.user_id)
        if not user:
            return {
                "filter_id": str(saved_filter.id),
                "filter_name": saved_filter.name,
                "status": "error",
                "error": "User not found"
            }
        
        # Find matching tenders
        matching_tenders = await self._find_matching_tenders(db, saved_filter)
        
        if not matching_tenders:
            self.logger.info(f"No matching tenders for filter '{saved_filter.name}'")
            return {
                "filter_id": str(saved_filter.id),
                "filter_name": saved_filter.name,
                "status": "skipped",
                "reason": "no_matching_tenders",
                "tender_count": 0
            }
        
        # Send email
        email_result = await email_service.send_tender_digest(
            user_email=user.email,
            filter_name=saved_filter.name,
            tenders=matching_tenders
        )
        
        if email_result["status"] == "sent":
            # Log the email
            await self._log_email(db, saved_filter, user, email_result, matching_tenders)
            
            # Update filter's last_notified_at
            saved_filter.last_notified_at = datetime.now()
            await db.commit()
            
            return {
                "filter_id": str(saved_filter.id),
                "filter_name": saved_filter.name,
                "status": "sent",
                "tender_count": len(matching_tenders),
                "email_id": email_result.get("email_id")
            }
        else:
            return {
                "filter_id": str(saved_filter.id),
                "filter_name": saved_filter.name,
                "status": "error",
                "error": email_result.get("error", "Unknown error"),
                "tender_count": len(matching_tenders)
            }
    
    async def _find_matching_tenders(self, db: AsyncSession, saved_filter: SavedFilter) -> List[Dict[str, Any]]:
        """Find tenders matching the saved filter criteria."""
        # Calculate date range (last 24 hours)
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # Build query conditions
        conditions = [
            Tender.publication_date >= yesterday.date(),
        ]
        
        # Keyword matching (ILIKE on title or summary)
        if saved_filter.keywords:
            keyword_conditions = []
            for keyword in saved_filter.keywords:
                if keyword.strip():
                    keyword_conditions.append(
                        or_(
                            func.lower(Tender.title).like(f"%{keyword.lower()}%"),
                            func.lower(Tender.summary).like(f"%{keyword.lower()}%")
                        )
                    )
            
            if keyword_conditions:
                conditions.append(or_(*keyword_conditions))
        
        # CPV codes overlap
        if saved_filter.cpv_codes:
            cpv_conditions = []
            for cpv_code in saved_filter.cpv_codes:
                if cpv_code.strip():
                    cpv_conditions.append(Tender.cpv_codes.contains([cpv_code.strip()]))
            
            if cpv_conditions:
                conditions.append(or_(*cpv_conditions))
        
        # Countries overlap
        if saved_filter.countries:
            country_conditions = []
            for country in saved_filter.countries:
                if country.strip():
                    country_conditions.append(Tender.buyer_country == country.strip().upper())
            
            if country_conditions:
                conditions.append(or_(*country_conditions))
        
        # Value range filtering
        if saved_filter.min_value is not None:
            conditions.append(Tender.value_amount >= saved_filter.min_value)
        
        if saved_filter.max_value is not None:
            conditions.append(Tender.value_amount <= saved_filter.max_value)
        
        # Execute query
        query = select(Tender).where(and_(*conditions)).order_by(Tender.publication_date.desc())
        result = await db.execute(query)
        tenders = result.scalars().all()
        
        # Convert to dictionaries and deduplicate by tender_ref
        tender_dicts = []
        seen_refs = set()
        
        for tender in tenders:
            if tender.tender_ref not in seen_refs:
                tender_dicts.append({
                    "tender_ref": tender.tender_ref,
                    "title": tender.title,
                    "summary": tender.summary,
                    "publication_date": tender.publication_date,
                    "deadline_date": tender.deadline_date,
                    "cpv_codes": tender.cpv_codes,
                    "buyer_name": tender.buyer_name,
                    "buyer_country": tender.buyer_country,
                    "value_amount": tender.value_amount,
                    "currency": tender.currency,
                    "url": tender.url,
                    "source": tender.source.value,
                })
                seen_refs.add(tender.tender_ref)
        
        self.logger.info(f"Found {len(tender_dicts)} matching tenders for filter '{saved_filter.name}'")
        return tender_dicts
    
    async def _log_email(
        self,
        db: AsyncSession,
        saved_filter: SavedFilter,
        user: User,
        email_result: Dict[str, Any],
        tenders: List[Dict[str, Any]]
    ) -> None:
        """Log sent email to database."""
        subject = f"[Procurement Copilot] New tenders for: {saved_filter.name} ({len(tenders)})"
        body_preview = email_service.get_body_preview(tenders)
        
        email_log = EmailLogCreate(
            user_id=user.id,
            saved_filter_id=saved_filter.id,
            subject=subject,
            body_preview=body_preview
        )
        
        await EmailLogCRUD.create(db, email_log)
        self.logger.info(f"Logged email for filter '{saved_filter.name}' to {user.email}")
    
    async def send_alerts_for_filter(
        self,
        db: AsyncSession,
        filter_id: str
    ) -> Dict[str, Any]:
        """Send alerts for a specific filter (for testing)."""
        try:
            filter_uuid = uuid.UUID(filter_id)
            saved_filter = await SavedFilterCRUD.get_by_id(db, filter_uuid)
            
            if not saved_filter:
                return {
                    "status": "error",
                    "error": f"Filter not found: {filter_id}"
                }
            
            return await self._process_filter(db, saved_filter)
            
        except ValueError:
            return {
                "status": "error",
                "error": f"Invalid filter ID: {filter_id}"
            }
        except Exception as e:
            self.logger.error(f"Error sending alerts for filter {filter_id}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Global alert service instance
alert_service = AlertService()
