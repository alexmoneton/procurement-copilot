"""Admin endpoints for system management."""

import asyncio
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.session import get_db
from ....core.logging import logger

router = APIRouter()

@router.post("/test-email")
async def test_email(
    to: str,
    subject: str = "Test Email from TenderPulse",
    message: str = "This is a test email to verify email delivery is working."
):
    """Test email delivery."""
    try:
        # Simple direct test using Resend API
        import httpx
        from ....core.config import settings
        
        resend_api_key = getattr(settings, 'resend_api_key', None)
        if not resend_api_key:
            return {
                "status": "error",
                "message": "No Resend API key configured",
                "result": None
            }
        
        headers = {
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json",
        }
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Test Email</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="padding: 20px 0;">
                <p style="font-size: 16px; margin: 0 0 20px 0;">{message}</p>
                <p style="font-size: 14px; color: #666; margin: 0;">If you received this email, your email system is working correctly.</p>
            </div>
        </body>
        </html>
        """
        
        payload = {
            "from": "alerts@tenderpulse.eu",
            "to": [to],
            "subject": subject,
            "html": html_content,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers=headers,
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            result = response.json()
        
        logger.info(f"Test email sent successfully to {to}: {result}")
        return {
            "status": "success",
            "message": f"Test email sent to {to}",
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send test email: {str(e)}")

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
