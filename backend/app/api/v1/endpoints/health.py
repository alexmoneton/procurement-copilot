"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.config import settings
from ....db.session import get_db
from ....db.schemas import HealthResponse
from ....core.metrics import metrics_collector

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(),
        version=settings.app_version,
    )


@router.get("/health-simple")
async def health_check_simple():
    """Simple health check that doesn't require database."""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": settings.app_version,
    }


@router.get("/ping")
async def ping():
    """Simple ping endpoint for Railway health checks."""
    return {"status": "ok", "message": "pong"}


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus-style metrics endpoint."""
    return metrics_collector.get_metrics()


@router.post("/init-db")
async def init_database():
    """Initialize database tables (run migrations)."""
    try:
        from ....db.session import engine
        from ....db.models import Base
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        return {"status": "success", "message": "Database tables created successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
