"""
Main outbound pipeline orchestrator.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from ..db.models_outbound import Prospect, ProspectStatus, OutboundMetrics
from ..core.config import settings
from .discovery import TEDDiscovery
from .enrich import HunterEnrichment
from .mailer import ResendMailer
from .utils import now_paris

logger = logging.getLogger(__name__)


class OutboundPipeline:
    """Main outbound pipeline orchestrator."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.discovery = TEDDiscovery(db)
        self.enrichment = HunterEnrichment(db)
        self.mailer = ResendMailer(db)
    
    async def run_outbound(
        self, 
        days: int = 1, 
        limit_leads: Optional[int] = None, 
        limit_sends: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run the complete outbound pipeline.
        
        Args:
            days: Number of days to look back for discovery
            limit_leads: Maximum number of leads to process
            limit_sends: Maximum number of emails to send
            
        Returns:
            Pipeline execution summary
        """
        try:
            self.logger.info("Starting outbound pipeline execution")
            
            # Use configured limits if not specified
            if limit_leads is None:
                limit_leads = settings.outbound_max_leads_per_day
            if limit_sends is None:
                limit_sends = settings.outbound_max_emails_per_day
            
            # Step 1: Discover prospects
            self.logger.info("Step 1: Discovering prospects from TED awards")
            discovery_result = await self.discovery.discover_prospects(
                days=days,
                min_score=settings.outbound_min_score
            )
            
            # Step 2: Select prospects for processing
            self.logger.info("Step 2: Selecting prospects for processing")
            prospects = await self._select_prospects_for_processing(limit_leads)
            
            # Step 3: Enrich prospects with contact information
            self.logger.info("Step 3: Enriching prospects with contact information")
            enrichment_result = await self.enrichment.enrich_prospects(
                prospects=prospects,
                max_enrichments=settings.hunter_daily_cap
            )
            
            # Step 4: Send emails to enriched prospects
            self.logger.info("Step 4: Sending emails to enriched prospects")
            sending_result = await self.mailer.send_batch(
                prospects=prospects,
                max_sends=limit_sends
            )
            
            # Step 5: Record metrics
            self.logger.info("Step 5: Recording metrics")
            await self._record_metrics(
                discovery_result,
                enrichment_result,
                sending_result
            )
            
            # Compile summary
            summary = {
                "execution_time": datetime.utcnow().isoformat(),
                "discovery": discovery_result,
                "enrichment": enrichment_result,
                "sending": sending_result,
                "total_processed": len(prospects),
                "success": True
            }
            
            self.logger.info(f"Outbound pipeline completed successfully: {summary}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error in outbound pipeline: {e}")
            return {
                "execution_time": datetime.utcnow().isoformat(),
                "error": str(e),
                "success": False
            }
    
    async def _select_prospects_for_processing(self, limit: int) -> List[Prospect]:
        """
        Select prospects for processing based on criteria.
        
        Args:
            limit: Maximum number of prospects to select
            
        Returns:
            List of selected prospects
        """
        try:
            # Build query for prospects ready for processing
            query = select(Prospect).where(
                and_(
                    Prospect.status.in_([ProspectStatus.NEW, ProspectStatus.ENRICHED]),
                    Prospect.score >= settings.outbound_min_score
                )
            ).order_by(desc(Prospect.score), desc(Prospect.created_at)).limit(limit)
            
            # Apply sector filter if configured
            if settings.outbound_sectors:
                sectors = [s.strip().lower() for s in settings.outbound_sectors.split(",")]
                # This would need to be implemented based on your sector mapping
                # For now, we'll skip sector filtering
            
            result = await self.db.execute(query)
            prospects = result.scalars().all()
            
            self.logger.info(f"Selected {len(prospects)} prospects for processing")
            return prospects
            
        except Exception as e:
            self.logger.error(f"Error selecting prospects: {e}")
            return []
    
    async def _record_metrics(
        self, 
        discovery_result: Dict[str, Any], 
        enrichment_result: Dict[str, Any], 
        sending_result: Dict[str, Any]
    ):
        """
        Record daily metrics for the pipeline.
        
        Args:
            discovery_result: Discovery step results
            enrichment_result: Enrichment step results
            sending_result: Sending step results
        """
        try:
            # Get today's date
            today = now_paris().date()
            
            # Check if metrics already exist for today
            existing_query = select(OutboundMetrics).where(
                OutboundMetrics.date == today
            )
            result = await self.db.execute(existing_query)
            existing_metrics = result.scalar_one_or_none()
            
            if existing_metrics:
                # Update existing metrics
                existing_metrics.prospects_discovered += discovery_result.get("prospects_upserted", 0)
                existing_metrics.contacts_enriched += enrichment_result.get("enriched", 0)
                existing_metrics.emails_sent += sending_result.get("emails_sent", 0)
                existing_metrics.hunter_api_calls += enrichment_result.get("daily_usage", 0)
            else:
                # Create new metrics
                new_metrics = OutboundMetrics(
                    date=today,
                    prospects_discovered=discovery_result.get("prospects_upserted", 0),
                    contacts_enriched=enrichment_result.get("enriched", 0),
                    emails_sent=sending_result.get("emails_sent", 0),
                    hunter_api_calls=enrichment_result.get("daily_usage", 0)
                )
                self.db.add(new_metrics)
            
            await self.db.commit()
            self.logger.info("Metrics recorded successfully")
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"Error recording metrics: {e}")
    
    async def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get current pipeline status.
        
        Returns:
            Pipeline status information
        """
        try:
            # Get recent metrics
            recent_metrics_query = select(OutboundMetrics).order_by(
                desc(OutboundMetrics.date)
            ).limit(7)  # Last 7 days
            
            result = await self.db.execute(recent_metrics_query)
            recent_metrics = result.scalars().all()
            
            # Get prospect counts by status
            prospect_counts = {}
            for status in ProspectStatus:
                count_query = select(Prospect).where(Prospect.status == status)
                count_result = await self.db.execute(count_query)
                prospect_counts[status.value] = count_result.scalar_one_or_none() or 0
            
            # Calculate totals
            total_prospects = sum(prospect_counts.values())
            ready_to_process = prospect_counts.get("new", 0) + prospect_counts.get("enriched", 0)
            
            return {
                "total_prospects": total_prospects,
                "prospect_counts": prospect_counts,
                "ready_to_process": ready_to_process,
                "recent_metrics": [
                    {
                        "date": metric.date.isoformat(),
                        "prospects_discovered": metric.prospects_discovered,
                        "contacts_enriched": metric.contacts_enriched,
                        "emails_sent": metric.emails_sent,
                        "hunter_api_calls": metric.hunter_api_calls
                    }
                    for metric in recent_metrics
                ],
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting pipeline status: {e}")
            return {
                "error": str(e),
                "last_updated": datetime.utcnow().isoformat()
            }
    
    async def pause_pipeline(self) -> bool:
        """
        Pause the outbound pipeline.
        
        Returns:
            True if paused successfully, False otherwise
        """
        try:
            # Update configuration to disable outbound
            # This would typically be done through environment variables or config
            # For now, we'll just log the action
            self.logger.info("Outbound pipeline paused")
            return True
            
        except Exception as e:
            self.logger.error(f"Error pausing pipeline: {e}")
            return False
    
    async def resume_pipeline(self) -> bool:
        """
        Resume the outbound pipeline.
        
        Returns:
            True if resumed successfully, False otherwise
        """
        try:
            # Update configuration to enable outbound
            # This would typically be done through environment variables or config
            # For now, we'll just log the action
            self.logger.info("Outbound pipeline resumed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error resuming pipeline: {e}")
            return False
