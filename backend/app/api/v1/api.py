"""API v1 router configuration."""

from fastapi import APIRouter

from .endpoints import health, tenders, filters, billing, profiles

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(tenders.router, prefix="/tenders", tags=["tenders"])
api_router.include_router(filters.router, prefix="/filters", tags=["filters"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
