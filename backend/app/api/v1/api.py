"""API v1 router configuration."""

from fastapi import APIRouter

from .endpoints import admin, cron, filters, health, profiles, seo, sitemap, tenders

# Import billing with error handling
try:
    from .endpoints import billing

    print("✅ Billing module imported successfully")
except Exception as e:
    print(f"❌ Error importing billing module: {e}")
    import traceback

    traceback.print_exc()
    billing = None

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(tenders.router, prefix="/tenders", tags=["tenders"])
api_router.include_router(filters.router, prefix="/filters", tags=["filters"])

# Include billing router with error handling
if billing:
    try:
        api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
        print("✅ Billing router included successfully")
    except Exception as e:
        print(f"❌ Error including billing router: {e}")
        import traceback

        traceback.print_exc()
else:
    print("⚠️ Billing module not available - skipping billing router")

api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(seo.router, prefix="/seo", tags=["seo"])
api_router.include_router(sitemap.router, prefix="/sitemap", tags=["sitemap"])
api_router.include_router(cron.router, prefix="/cron", tags=["cron"])
