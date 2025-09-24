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
        from sqlalchemy import text
        
        # Check if raw_blob column exists
        result = await db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'tenders' AND column_name = 'raw_blob'
        """))
        
        if result.fetchone() is None:
            # Add the missing raw_blob column
            await db.execute(text("ALTER TABLE tenders ADD COLUMN raw_blob TEXT"))
            await db.commit()
            logger.info("Added raw_blob column to tenders table")
            return {"status": "success", "message": "Added missing raw_blob column"}
        else:
            logger.info("raw_blob column already exists")
            return {"status": "success", "message": "raw_blob column already exists"}
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@router.get("/health")
async def admin_health():
    """Admin health check."""
    return {"status": "ok", "service": "admin"}
