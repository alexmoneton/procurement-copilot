"""API v1 router configuration."""

from fastapi import APIRouter

from .endpoints import health, tenders, filters, profiles, admin

# Import billing with error handling
try:
    from .endpoints import billing
    print("✅ Billing module imported successfully")
except Exception as e:
    print(f"❌ Error importing billing module: {e}")
    import traceback
    traceback.print_exc()

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(tenders.router, prefix="/tenders", tags=["tenders"])
api_router.include_router(filters.router, prefix="/filters", tags=["filters"])

# Include billing router with error handling
try:
    api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
    print("✅ Billing router included successfully")
except Exception as e:
    print(f"❌ Error including billing router: {e}")
    import traceback
    traceback.print_exc()

api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
