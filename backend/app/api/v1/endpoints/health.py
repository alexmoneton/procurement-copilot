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


@router.get("/ping")
async def ping():
    """Simple ping endpoint for Railway health checks."""
    return {"status": "ok", "message": "pong"}


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus-style metrics endpoint."""
    return metrics_collector.get_metrics()
