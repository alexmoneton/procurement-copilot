"""
CLI commands for outbound pipeline management.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

import click
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..outbound.pipeline import OutboundPipeline
from ..core.config import settings

logger = logging.getLogger(__name__)


@click.group()
def outbound():
    """Outbound pipeline management commands."""
    pass


@outbound.command()
@click.option("--days", default=1, help="Number of days to look back for discovery")
@click.option("--limit-leads", type=int, help="Maximum number of leads to process")
@click.option("--limit-sends", type=int, help="Maximum number of emails to send")
@click.option("--dry-run", is_flag=True, help="Run in dry-run mode (no actual sending)")
def run(days: int, limit_leads: Optional[int], limit_sends: Optional[int], dry_run: bool):
    """Run the outbound pipeline."""
    asyncio.run(_run_pipeline(days, limit_leads, limit_sends, dry_run))


@outbound.command()
def status():
    """Get outbound pipeline status."""
    asyncio.run(_get_status())


@outbound.command()
def pause():
    """Pause the outbound pipeline."""
    asyncio.run(_pause_pipeline())


@outbound.command()
def resume():
    """Resume the outbound pipeline."""
    asyncio.run(_resume_pipeline())


async def _run_pipeline(
    days: int, 
    limit_leads: Optional[int], 
    limit_sends: Optional[int], 
    dry_run: bool
):
    """Run the outbound pipeline."""
    try:
        print(f"🚀 Starting outbound pipeline...")
        print(f"   Days: {days}")
        print(f"   Limit leads: {limit_leads or 'default'}")
        print(f"   Limit sends: {limit_sends or 'default'}")
        print(f"   Dry run: {dry_run}")
        
        if dry_run:
            print("⚠️  DRY RUN MODE - No emails will be sent")
        
        # Get database session
        async for db in get_db():
            pipeline = OutboundPipeline(db)
            
            # Run pipeline
            result = await pipeline.run_outbound(
                days=days,
                limit_leads=limit_leads,
                limit_sends=limit_sends
            )
            
            # Print results
            print("\n📊 Pipeline Results:")
            print(f"   Success: {result.get('success', False)}")
            
            if result.get('success'):
                discovery = result.get('discovery', {})
                enrichment = result.get('enrichment', {})
                sending = result.get('sending', {})
                
                print(f"   Awards processed: {discovery.get('awards_processed', 0)}")
                print(f"   Lost bidders found: {discovery.get('lost_bidders_found', 0)}")
                print(f"   Prospects upserted: {discovery.get('prospects_upserted', 0)}")
                print(f"   Contacts enriched: {enrichment.get('enriched', 0)}")
                print(f"   Emails sent: {sending.get('emails_sent', 0)}")
                print(f"   Errors: {sending.get('errors', 0)}")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
            
            break
        
        print("\n✅ Pipeline execution completed")
        
    except Exception as e:
        print(f"❌ Error running pipeline: {e}")
        logger.error(f"Error running pipeline: {e}")


async def _get_status():
    """Get outbound pipeline status."""
    try:
        print("📊 Outbound Pipeline Status")
        print("=" * 50)
        
        # Get database session
        async for db in get_db():
            pipeline = OutboundPipeline(db)
            status = await pipeline.get_pipeline_status()
            
            print(f"Total prospects: {status.get('total_prospects', 0)}")
            print(f"Ready to process: {status.get('ready_to_process', 0)}")
            
            print("\nProspect counts by status:")
            prospect_counts = status.get('prospect_counts', {})
            for status_name, count in prospect_counts.items():
                print(f"  {status_name}: {count}")
            
            print("\nRecent metrics (last 7 days):")
            recent_metrics = status.get('recent_metrics', [])
            for metric in recent_metrics:
                date = metric['date'][:10]  # Just the date part
                print(f"  {date}: {metric['emails_sent']} sent, {metric['contacts_enriched']} enriched")
            
            break
        
        print("\n✅ Status retrieved successfully")
        
    except Exception as e:
        print(f"❌ Error getting status: {e}")
        logger.error(f"Error getting status: {e}")


async def _pause_pipeline():
    """Pause the outbound pipeline."""
    try:
        print("⏸️  Pausing outbound pipeline...")
        
        # Get database session
        async for db in get_db():
            pipeline = OutboundPipeline(db)
            success = await pipeline.pause_pipeline()
            
            if success:
                print("✅ Pipeline paused successfully")
            else:
                print("❌ Failed to pause pipeline")
            
            break
        
    except Exception as e:
        print(f"❌ Error pausing pipeline: {e}")
        logger.error(f"Error pausing pipeline: {e}")


async def _resume_pipeline():
    """Resume the outbound pipeline."""
    try:
        print("▶️  Resuming outbound pipeline...")
        
        # Get database session
        async for db in get_db():
            pipeline = OutboundPipeline(db)
            success = await pipeline.resume_pipeline()
            
            if success:
                print("✅ Pipeline resumed successfully")
            else:
                print("❌ Failed to resume pipeline")
            
            break
        
    except Exception as e:
        print(f"❌ Error resuming pipeline: {e}")
        logger.error(f"Error resuming pipeline: {e}")


if __name__ == "__main__":
    outbound()
