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
        from ...services.email import EmailService
        
        email_service = EmailService()
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #003399; color: white; padding: 20px; text-align: center;">
                <h1>🎯 TenderPulse</h1>
            </div>
            <div style="padding: 20px;">
                <h2>Email Test Successful!</h2>
                <p>{message}</p>
                <p>If you received this email, your TenderPulse email system is working correctly.</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    TenderPulse - Real-time signals for European public contracts
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        TenderPulse Email Test
        
        {message}
        
        If you received this email, your TenderPulse email system is working correctly.
        
        --
        TenderPulse - Real-time signals for European public contracts
        """
        
        result = await email_service.send_email(
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=text_content
        )
        
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
