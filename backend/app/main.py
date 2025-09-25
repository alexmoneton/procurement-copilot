"""FastAPI application main module."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.api import api_router
from .core.config import settings
from .core.logging import get_logger
from .db.session import close_db, init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting up Procurement Copilot API")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        logger.info("Continuing without database connection")

    yield

    # Shutdown
    logger.info("Shutting down Procurement Copilot API")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Error closing database connections: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered procurement tender monitoring system",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
async def root():
    """Root endpoint."""
    try:
        return {
            "message": "Procurement Copilot API",
            "version": settings.app_version,
            "docs": f"{settings.api_v1_prefix}/docs",
        }
    except Exception as e:
        return {
            "message": "Procurement Copilot API",
            "version": "0.1.0",
            "error": str(e),
            "docs": "/api/v1/docs",
        }


@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {"status": "ok", "message": "API is running"}


@app.get("/ping")
async def ping():
    """Ultra simple ping endpoint."""
    return "pong"
