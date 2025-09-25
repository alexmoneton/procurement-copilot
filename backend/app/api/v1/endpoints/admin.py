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
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f8f9fa;">
            <div style="background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin: 20px; overflow: hidden;">
                <div style="padding: 30px 20px; text-align: center; border-bottom: 1px solid #e9ecef;">
                    <h1 style="margin: 0; color: #003399; font-size: 24px; font-weight: 600;">TenderPulse</h1>
                    <p style="margin: 5px 0 0 0; color: #6c757d; font-size: 14px;">Real-time signals for European public contracts</p>
                </div>
                <div style="padding: 30px 20px;">
                    <h2 style="margin: 0 0 20px 0; color: #212529; font-size: 20px; font-weight: 500;">Email Test Successful!</h2>
                    <p style="margin: 0 0 15px 0; color: #495057; line-height: 1.5;">{message}</p>
                    <p style="margin: 0 0 20px 0; color: #495057; line-height: 1.5;">If you received this email, your TenderPulse email system is working correctly.</p>
                    <div style="background: #e3f2fd; border-left: 4px solid #003399; padding: 15px; margin: 20px 0; border-radius: 4px;">
                        <p style="margin: 0; color: #003399; font-size: 14px; font-weight: 500;">✅ Email delivery confirmed</p>
                    </div>
                </div>
                <div style="padding: 20px; background: #f8f9fa; border-top: 1px solid #e9ecef; text-align: center;">
                    <p style="margin: 0; color: #6c757d; font-size: 12px;">
                        TenderPulse - Independent EU procurement monitoring service
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        payload = {
            "from": "onboarding@resend.dev",
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
