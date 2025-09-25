"""Main outreach engine for sending targeted emails to SME bidders."""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.crud import CompanyCRUD, EmailLogCRUD
from ..db.schemas import EmailLogCreate
from ..services.company_resolution import company_resolution_service
from ..services.email import email_service
from ..services.outreach import outreach_targeting_service
from ..services.outreach_templates import outreach_templates


class OutreachEngine:
    """Main engine for managing outreach campaigns."""

    def __init__(self):
        self.logger = logger.bind(service="outreach_engine")
        self.rate_limit_delay = 1.0  # Delay between emails in seconds
        self.max_emails_per_hour = 50  # Rate limiting

    async def build_lead_list(
        self,
        db: AsyncSession,
        strategy: str,
        cpv_codes: Optional[List[str]] = None,
        country: Optional[str] = None,
        limit: int = 200,
    ) -> List[Dict[str, Any]]:
        """
        Build a lead list based on the specified strategy.

        Strategies:
        - lost_bidders: Active but losing SMEs
        - cross_border: Single-country bidders with cross-border potential
        - lapsed: Lapsed bidders
        """
        self.logger.info(f"Building lead list with strategy: {strategy}")

        if strategy == "lost_bidders":
            leads = await outreach_targeting_service.get_active_but_losing_smes(
                db, cpv_codes, country, limit
            )
        elif strategy == "cross_border":
            leads = await outreach_targeting_service.get_single_country_bidders_with_cross_border_potential(
                db, cpv_codes, limit
            )
        elif strategy == "lapsed":
            leads = await outreach_targeting_service.get_lapsed_bidders(
                db, cpv_codes, country, limit
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        self.logger.info(f"Built lead list with {len(leads)} leads")
        return leads

    async def send_campaign(
        self,
        db: AsyncSession,
        campaign_type: str,
        leads: List[Dict[str, Any]],
        cpv_codes: Optional[List[str]] = None,
        country: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Send outreach campaign to leads.

        Campaign types:
        - missed_opportunities
        - cross_border_expansion
        - reactivation
        """
        self.logger.info(f"Sending {campaign_type} campaign to {len(leads)} leads")

        results = {
            "sent": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "campaign_type": campaign_type,
            "total_leads": len(leads),
        }

        # Limit the number of emails to send
        leads_to_process = leads[:limit]

        for i, lead in enumerate(leads_to_process):
            try:
                # Rate limiting
                if i > 0 and i % self.max_emails_per_hour == 0:
                    self.logger.info(f"Rate limiting: waiting {self.rate_limit_delay}s")
                    import asyncio

                    await asyncio.sleep(self.rate_limit_delay)

                # Process lead
                result = await self._process_lead(
                    db, campaign_type, lead, cpv_codes, country
                )

                if result["status"] == "sent":
                    results["sent"] += 1
                elif result["status"] == "skipped":
                    results["skipped"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append(result.get("error", "Unknown error"))

            except Exception as e:
                self.logger.error(f"Error processing lead {i}: {e}")
                results["failed"] += 1
                results["errors"].append(str(e))

        self.logger.info(
            f"Campaign completed: {results['sent']} sent, "
            f"{results['failed']} failed, {results['skipped']} skipped"
        )

        return results

    async def _process_lead(
        self,
        db: AsyncSession,
        campaign_type: str,
        lead: Dict[str, Any],
        cpv_codes: Optional[List[str]] = None,
        country: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a single lead for outreach."""
        company_name = lead.get("name", "")

        if not company_name:
            return {"status": "skipped", "reason": "No company name"}

        # Determine country for company resolution
        lead_country = country or lead.get("country", "FR")  # Default to France

        # Resolve company information
        company_info = await company_resolution_service.resolve_company_from_name(
            db, company_name, lead_country
        )

        if not company_info:
            return {"status": "skipped", "reason": "Could not resolve company"}

        # Check if company is suppressed
        if company_info.get("is_suppressed", False):
            return {"status": "skipped", "reason": "Company is suppressed"}

        # Check if we have contact information
        email = company_info.get("email")
        if not email:
            return {"status": "skipped", "reason": "No email address"}

        # Check rate limiting (don't contact too frequently)
        last_contacted = company_info.get("last_contacted")
        if last_contacted:
            days_since_contact = (datetime.now() - last_contacted).days
            if days_since_contact < 7:  # Don't contact more than once per week
                return {"status": "skipped", "reason": "Contacted recently"}

        # Get upcoming tenders for personalization
        upcoming_tenders = (
            await outreach_targeting_service.get_upcoming_tenders_for_company(
                db, company_name, cpv_codes, country, limit=3
            )
        )

        # Generate email content
        email_content = await self._generate_email_content(
            campaign_type, lead, company_info, upcoming_tenders
        )

        if not email_content:
            return {"status": "skipped", "reason": "Could not generate email content"}

        # Send email
        try:
            email_result = await email_service.send_alert_email(
                to_email=email,
                subject=email_content["subject"],
                html_content=email_content["html_content"],
                text_content=email_content["text_content"],
                tags=[
                    {"name": "campaign", "value": campaign_type},
                    {"name": "company", "value": company_name},
                    {"name": "country", "value": lead_country},
                ],
            )

            # Log email
            email_log = EmailLogCreate(
                user_id=uuid.uuid4(),  # Placeholder for system user
                saved_filter_id=uuid.uuid4(),  # Placeholder for system filter
                subject=email_content["subject"],
                body_preview=email_content["text_content"][:200],
            )

            await EmailLogCRUD.create(db, email_log)

            # Update last contacted timestamp
            await CompanyCRUD.update_last_contacted(db, company_info["id"])

            return {"status": "sent", "email_id": email_result.get("id")}

        except Exception as e:
            self.logger.error(f"Error sending email to {email}: {e}")
            return {"status": "failed", "error": str(e)}

    async def _generate_email_content(
        self,
        campaign_type: str,
        lead: Dict[str, Any],
        company_info: Dict[str, Any],
        upcoming_tenders: List[Dict[str, Any]],
    ) -> Optional[Dict[str, str]]:
        """Generate email content based on campaign type."""
        company_name = company_info.get("name", "")

        if campaign_type == "missed_opportunities":
            # For missed opportunities, we need to get missed tenders
            # This is a simplified version - in production, you'd query actual missed tenders
            missed_tenders = []  # Placeholder
            sector = "your sector"  # Would be determined from CPV codes

            return outreach_templates.generate_missed_opportunities_email(
                company_name, sector, missed_tenders, upcoming_tenders
            )

        elif campaign_type == "cross_border_expansion":
            home_country = lead.get("strong_country", "your country")
            adjacent_country = lead.get("neighbor_countries", ["neighboring country"])[
                0
            ]

            return outreach_templates.generate_cross_border_expansion_email(
                company_name, home_country, adjacent_country, upcoming_tenders
            )

        elif campaign_type == "reactivation":
            sector = "your sector"  # Would be determined from CPV codes

            return outreach_templates.generate_reactivation_email(
                company_name, sector, upcoming_tenders
            )

        else:
            self.logger.error(f"Unknown campaign type: {campaign_type}")
            return None

    async def get_campaign_stats(
        self, db: AsyncSession, campaign_type: str, days: int = 30
    ) -> Dict[str, Any]:
        """Get statistics for a campaign type."""
        # This would query email logs to get actual stats
        # For now, return placeholder data

        return {
            "campaign_type": campaign_type,
            "period_days": days,
            "emails_sent": 0,  # Would be calculated from email logs
            "open_rate": 0.0,  # Would be calculated from tracking pixels
            "click_rate": 0.0,  # Would be calculated from link clicks
            "unsubscribe_rate": 0.0,  # Would be calculated from unsubscribes
            "conversion_rate": 0.0,  # Would be calculated from signups
        }

    async def handle_unsubscribe(
        self, db: AsyncSession, company_id: str, email: str
    ) -> bool:
        """Handle unsubscribe request."""
        try:
            # Add company to suppression list
            success = await CompanyCRUD.suppress_company(db, uuid.UUID(company_id))

            if success:
                # Send unsubscribe confirmation email
                company_info = await CompanyCRUD.get_by_id(db, uuid.UUID(company_id))
                if company_info:
                    unsubscribe_email = outreach_templates.generate_unsubscribe_email(
                        company_info.name, "#"  # Placeholder unsubscribe link
                    )

                    await email_service.send_alert_email(
                        to_email=email,
                        subject=unsubscribe_email["subject"],
                        html_content=unsubscribe_email["html_content"],
                        text_content=unsubscribe_email["text_content"],
                    )

            return success

        except Exception as e:
            self.logger.error(f"Error handling unsubscribe: {e}")
            return False


# Global engine instance
outreach_engine = OutreachEngine()
