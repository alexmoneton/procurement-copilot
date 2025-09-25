"""Background job definitions."""

import asyncio
import sys
from typing import Any, Dict

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import AsyncSessionLocal
from ..services.alerts import alert_service
from ..services.ingest import ingest_service


async def run_ingest_job(
    ted_limit: int = 200, boamp_limit: int = 200
) -> Dict[str, Any]:
    """Run the tender ingestion job."""
    job_logger = logger.bind(job="ingest")
    job_logger.info("Starting tender ingestion job")

    try:
        async with AsyncSessionLocal() as db:
            results = await ingest_service.run_ingest(db, ted_limit, boamp_limit)

            job_logger.info(
                f"Ingestion job completed: {results['inserted']} inserted, "
                f"{results['updated']} updated, {results['skipped']} skipped, "
                f"{results['errors']} errors"
            )

            return {
                "status": "success",
                "results": results,
                "message": "Ingestion completed successfully",
            }

    except Exception as e:
        job_logger.error(f"Ingestion job failed: {e}")
        return {"status": "error", "error": str(e), "message": "Ingestion failed"}


async def run_ted_ingest_job(limit: int = 200) -> Dict[str, Any]:
    """Run TED-only ingestion job."""
    job_logger = logger.bind(job="ted_ingest")
    job_logger.info(f"Starting TED ingestion job (limit: {limit})")

    try:
        async with AsyncSessionLocal() as db:
            results = await ingest_service.ingest_single_source(db, "TED", limit)

            job_logger.info(
                f"TED ingestion job completed: {results['inserted']} inserted, "
                f"{results['updated']} updated, {results['skipped']} skipped, "
                f"{results['errors']} errors"
            )

            return {
                "status": "success",
                "results": results,
                "message": "TED ingestion completed successfully",
            }

    except Exception as e:
        job_logger.error(f"TED ingestion job failed: {e}")
        return {"status": "error", "error": str(e), "message": "TED ingestion failed"}


async def run_boamp_ingest_job(limit: int = 200) -> Dict[str, Any]:
    """Run BOAMP-only ingestion job."""
    job_logger = logger.bind(job="boamp_ingest")
    job_logger.info(f"Starting BOAMP ingestion job (limit: {limit})")

    try:
        async with AsyncSessionLocal() as db:
            results = await ingest_service.ingest_single_source(db, "BOAMP_FR", limit)

            job_logger.info(
                f"BOAMP ingestion job completed: {results['inserted']} inserted, "
                f"{results['updated']} updated, {results['skipped']} skipped, "
                f"{results['errors']} errors"
            )

            return {
                "status": "success",
                "results": results,
                "message": "BOAMP ingestion completed successfully",
            }

    except Exception as e:
        job_logger.error(f"BOAMP ingestion job failed: {e}")
        return {"status": "error", "error": str(e), "message": "BOAMP ingestion failed"}


async def cleanup_old_tenders_job(days_old: int = 365) -> Dict[str, Any]:
    """Clean up old tenders (optional maintenance job)."""
    job_logger = logger.bind(job="cleanup")
    job_logger.info(
        f"Starting cleanup job (removing tenders older than {days_old} days)"
    )

    try:
        from datetime import date, timedelta

        from sqlalchemy import delete

        from ..db.models import Tender

        cutoff_date = date.today() - timedelta(days=days_old)

        async with AsyncSessionLocal() as db:
            # Count tenders to be deleted
            from sqlalchemy import func, select

            count_result = await db.execute(
                select(func.count(Tender.id)).where(
                    Tender.publication_date < cutoff_date
                )
            )
            count = count_result.scalar()

            if count > 0:
                # Delete old tenders
                await db.execute(
                    delete(Tender).where(Tender.publication_date < cutoff_date)
                )
                await db.commit()

                job_logger.info(f"Cleanup job completed: {count} old tenders removed")

                return {
                    "status": "success",
                    "deleted_count": count,
                    "message": f"Cleaned up {count} old tenders",
                }
            else:
                job_logger.info("Cleanup job completed: no old tenders to remove")

                return {
                    "status": "success",
                    "deleted_count": 0,
                    "message": "No old tenders to clean up",
                }

    except Exception as e:
        job_logger.error(f"Cleanup job failed: {e}")
        return {"status": "error", "error": str(e), "message": "Cleanup failed"}


async def run_alerts_job() -> Dict[str, Any]:
    """Run the alerts job."""
    job_logger = logger.bind(job="alerts")
    job_logger.info("Starting alerts job")

    try:
        async with AsyncSessionLocal() as db:
            results = await alert_service.run_alerts_pipeline(db)

            job_logger.info(
                f"Alerts job completed: {results['emails_sent']} sent, "
                f"{results['emails_skipped']} skipped, {results['errors']} errors"
            )

            return {
                "status": "success",
                "results": results,
                "message": "Alerts completed successfully",
            }

    except Exception as e:
        job_logger.error(f"Alerts job failed: {e}")
        return {"status": "error", "error": str(e), "message": "Alerts failed"}


async def send_alerts_for_filter_job(filter_id: str) -> Dict[str, Any]:
    """Send alerts for a specific filter."""
    job_logger = logger.bind(job="alerts_filter")
    job_logger.info(f"Starting alerts job for filter: {filter_id}")

    try:
        async with AsyncSessionLocal() as db:
            result = await alert_service.send_alerts_for_filter(db, filter_id)

            job_logger.info(f"Filter alerts job completed: {result['status']}")

            return {
                "status": "success",
                "result": result,
                "message": "Filter alerts completed",
            }

    except Exception as e:
        job_logger.error(f"Filter alerts job failed: {e}")
        return {"status": "error", "error": str(e), "message": "Filter alerts failed"}


# CLI interface for running jobs manually
async def main():
    """CLI interface for running jobs."""
    if len(sys.argv) < 2:
        print("Usage: python -m app.tasks.jobs <job_name> [args...]")
        print("Available jobs:")
        print("  run_ingest [ted_limit] [boamp_limit]")
        print("  run_ted_ingest [limit]")
        print("  run_boamp_ingest [limit]")
        print("  cleanup [days_old]")
        print("  send_alerts")
        print("  send_alerts_filter <filter_id>")
        sys.exit(1)

    job_name = sys.argv[1]

    try:
        if job_name == "run_ingest":
            ted_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 200
            boamp_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 200
            result = await run_ingest_job(ted_limit, boamp_limit)

        elif job_name == "run_ted_ingest":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 200
            result = await run_ted_ingest_job(limit)

        elif job_name == "run_boamp_ingest":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 200
            result = await run_boamp_ingest_job(limit)

        elif job_name == "cleanup":
            days_old = int(sys.argv[2]) if len(sys.argv) > 2 else 365
            result = await cleanup_old_tenders_job(days_old)

        elif job_name == "send_alerts":
            result = await run_alerts_job()

        elif job_name == "send_alerts_filter":
            if len(sys.argv) < 3:
                print("Error: filter_id required for send_alerts_filter")
                sys.exit(1)
            filter_id = sys.argv[2]
            result = await send_alerts_for_filter_job(filter_id)

        else:
            print(f"Unknown job: {job_name}")
            sys.exit(1)

        print(f"Job result: {result}")

    except Exception as e:
        print(f"Job failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
