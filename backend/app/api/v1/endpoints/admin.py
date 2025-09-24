"""Admin endpoints for system management."""

import asyncio
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.session import get_db
from ....core.logging import logger

router = APIRouter()

@router.post("/run-migrations")
async def run_migrations(db: AsyncSession = Depends(get_db)):
    """Run database migrations."""
    try:
        from alembic.config import Config
        from alembic import command
        import os
        
        # Set up Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        
        logger.info("Database migrations completed successfully")
        return {"status": "success", "message": "Database migrations completed successfully"}
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@router.get("/health")
async def admin_health():
    """Admin health check."""
    return {"status": "ok", "service": "admin"}
