"""Simple billing endpoints for testing."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/test")
async def billing_test():
    """Test endpoint to verify billing module is loaded."""
    return {"status": "billing module loaded successfully"}


@router.get("/health")
async def billing_health():
    """Billing health check."""
    return {"status": "ok", "service": "billing"}
