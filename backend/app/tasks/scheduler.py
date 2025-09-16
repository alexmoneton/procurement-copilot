"""APScheduler configuration and management."""

import asyncio
from datetime import datetime
from typing import Dict, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from ..core.config import settings
from .jobs import run_ingest_job, run_cleanup_old_tenders_job, run_alerts_job


class SchedulerManager:
    """Manages the APScheduler instance and job scheduling."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            timezone=settings.scheduler_timezone,
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 300,  # 5 minutes
            }
        )
        self.logger = logger.bind(service="scheduler")
    
    def start(self) -> None:
        """Start the scheduler."""
        try:
            self.scheduler.start()
            self.logger.info("Scheduler started successfully")
            self._schedule_jobs()
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def stop(self) -> None:
        """Stop the scheduler."""
        try:
            self.scheduler.shutdown(wait=True)
            self.logger.info("Scheduler stopped successfully")
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}")
    
    def _schedule_jobs(self) -> None:
        """Schedule all background jobs."""
        # Schedule ingestion job every 6 hours
        self.scheduler.add_job(
            func=self._run_ingest_job_wrapper,
            trigger=IntervalTrigger(hours=settings.ingest_interval_hours),
            id="ingest_tenders",
            name="Tender Ingestion Job",
            replace_existing=True,
            next_run_time=datetime.now(),  # Run immediately on startup
        )
        
        # Schedule cleanup job daily at 2 AM
        self.scheduler.add_job(
            func=self._run_cleanup_job_wrapper,
            trigger=CronTrigger(hour=2, minute=0),
            id="cleanup_old_tenders",
            name="Cleanup Old Tenders Job",
            replace_existing=True,
        )
        
        # Schedule alerts job daily at 7:30 AM
        self.scheduler.add_job(
            func=self._run_alerts_job_wrapper,
            trigger=CronTrigger(hour=7, minute=30),
            id="send_alerts",
            name="Send Daily Alerts Job",
            replace_existing=True,
        )
        
        self.logger.info("All jobs scheduled successfully")
    
    async def _run_ingest_job_wrapper(self) -> None:
        """Wrapper for the ingest job to handle logging."""
        job_logger = self.logger.bind(job="scheduled_ingest")
        job_logger.info("Starting scheduled tender ingestion")
        
        try:
            result = await run_ingest_job()
            if result["status"] == "success":
                job_logger.info("Scheduled ingestion completed successfully")
            else:
                job_logger.error(f"Scheduled ingestion failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            job_logger.error(f"Scheduled ingestion job failed: {e}")
    
    async def _run_cleanup_job_wrapper(self) -> None:
        """Wrapper for the cleanup job to handle logging."""
        job_logger = self.logger.bind(job="scheduled_cleanup")
        job_logger.info("Starting scheduled cleanup")
        
        try:
            result = await run_cleanup_old_tenders_job()
            if result["status"] == "success":
                job_logger.info("Scheduled cleanup completed successfully")
            else:
                job_logger.error(f"Scheduled cleanup failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            job_logger.error(f"Scheduled cleanup job failed: {e}")
    
    async def _run_alerts_job_wrapper(self) -> None:
        """Wrapper for the alerts job to handle logging."""
        job_logger = self.logger.bind(job="scheduled_alerts")
        job_logger.info("Starting scheduled alerts job")
        
        try:
            result = await run_alerts_job()
            if result["status"] == "success":
                job_logger.info("Scheduled alerts job completed successfully")
            else:
                job_logger.error(f"Scheduled alerts job failed: {result.get('error', 'Unknown error')}")
        except Exception as e:
            job_logger.error(f"Scheduled alerts job failed: {e}")
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs."""
        jobs = []
        
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            })
        
        return {
            "scheduler_running": self.scheduler.running,
            "jobs": jobs,
        }
    
    def trigger_job(self, job_id: str) -> bool:
        """Manually trigger a job."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                self.logger.info(f"Manually triggered job: {job_id}")
                return True
            else:
                self.logger.warning(f"Job not found: {job_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error triggering job {job_id}: {e}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """Pause a job."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.pause()
                self.logger.info(f"Paused job: {job_id}")
                return True
            else:
                self.logger.warning(f"Job not found: {job_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error pausing job {job_id}: {e}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """Resume a job."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.resume()
                self.logger.info(f"Resumed job: {job_id}")
                return True
            else:
                self.logger.warning(f"Job not found: {job_id}")
                return False
        except Exception as e:
            self.logger.error(f"Error resuming job {job_id}: {e}")
            return False


# Global scheduler instance
scheduler_manager = SchedulerManager()


async def start_scheduler() -> None:
    """Start the scheduler (for use in application startup)."""
    scheduler_manager.start()


async def stop_scheduler() -> None:
    """Stop the scheduler (for use in application shutdown)."""
    scheduler_manager.stop()


# Standalone scheduler runner for development/testing
async def run_scheduler_standalone() -> None:
    """Run the scheduler as a standalone process."""
    logger.info("Starting scheduler in standalone mode")
    
    try:
        scheduler_manager.start()
        
        # Keep the scheduler running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down scheduler")
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
    finally:
        scheduler_manager.stop()
        logger.info("Scheduler stopped")


if __name__ == "__main__":
    asyncio.run(run_scheduler_standalone())
