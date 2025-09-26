"""
Outbound pipeline API endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.session import get_db
from ....core.config import settings
from ....outbound.pipeline import OutboundPipeline
from ....outbound.mailer import ResendMailer
from ....db.models_outbound import Suppression

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/run", summary="Run outbound pipeline manually")
async def run_outbound_pipeline(
    days: int = Query(1, description="Number of days to look back for discovery"),
    limit_leads: Optional[int] = Query(None, description="Maximum number of leads to process"),
    limit_sends: Optional[int] = Query(None, description="Maximum number of emails to send"),
    token: str = Header(..., description="Authorization token"),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger the outbound pipeline.
    Requires authorization token.
    """
    try:
        # Verify authorization token
        if token != settings.secret_key:
            raise HTTPException(status_code=401, detail="Invalid authorization token")
        
        # Check if outbound is enabled
        if not settings.outbound_enabled:
            raise HTTPException(status_code=403, detail="Outbound pipeline is disabled")
        
        # Run pipeline
        pipeline = OutboundPipeline(db)
        result = await pipeline.run_outbound(
            days=days,
            limit_leads=limit_leads,
            limit_sends=limit_sends
        )
        
        if result.get("success"):
            return {
                "status": "success",
                "message": "Outbound pipeline executed successfully",
                "result": result
            }
        else:
            raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {result.get('error')}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running outbound pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/summary", summary="Get outbound pipeline summary")
async def get_outbound_summary(
    since: Optional[str] = Query(None, description="Date to get summary since (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary of outbound pipeline activity.
    """
    try:
        pipeline = OutboundPipeline(db)
        status = await pipeline.get_pipeline_status()
        
        # Filter by date if specified
        if since:
            try:
                since_date = datetime.fromisoformat(since).date()
                filtered_metrics = [
                    metric for metric in status.get("recent_metrics", [])
                    if datetime.fromisoformat(metric["date"]).date() >= since_date
                ]
                status["recent_metrics"] = filtered_metrics
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        return {
            "status": "success",
            "summary": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting outbound summary: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/pause", summary="Pause outbound pipeline")
async def pause_outbound_pipeline(
    token: str = Header(..., description="Authorization token"),
    db: AsyncSession = Depends(get_db)
):
    """
    Pause the outbound pipeline.
    """
    try:
        # Verify authorization token
        if token != settings.secret_key:
            raise HTTPException(status_code=401, detail="Invalid authorization token")
        
        pipeline = OutboundPipeline(db)
        success = await pipeline.pause_pipeline()
        
        if success:
            return {
                "status": "success",
                "message": "Outbound pipeline paused"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to pause pipeline")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing outbound pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/resume", summary="Resume outbound pipeline")
async def resume_outbound_pipeline(
    token: str = Header(..., description="Authorization token"),
    db: AsyncSession = Depends(get_db)
):
    """
    Resume the outbound pipeline.
    """
    try:
        # Verify authorization token
        if token != settings.secret_key:
            raise HTTPException(status_code=401, detail="Invalid authorization token")
        
        pipeline = OutboundPipeline(db)
        success = await pipeline.resume_pipeline()
        
        if success:
            return {
                "status": "success",
                "message": "Outbound pipeline resumed"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to resume pipeline")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming outbound pipeline: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/webhook", summary="Resend webhook endpoint")
async def resend_webhook(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Resend webhook events (opens, clicks, bounces, etc.).
    """
    try:
        event_type = payload.get("type")
        email = payload.get("data", {}).get("to")
        
        if not email:
            logger.warning("Webhook received without email address")
            return {"status": "ignored", "message": "No email address in payload"}
        
        # Handle different event types
        if event_type == "email.bounced":
            await _handle_bounce(db, email, payload)
        elif event_type == "email.complained":
            await _handle_complaint(db, email, payload)
        elif event_type == "email.opened":
            await _handle_open(db, email, payload)
        elif event_type == "email.clicked":
            await _handle_click(db, email, payload)
        elif event_type == "email.replied":
            await _handle_reply(db, email, payload)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
        
        return {"status": "success", "message": f"Processed {event_type} event"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/unsubscribe", summary="Unsubscribe endpoint")
async def unsubscribe(
    e: str = Query(..., description="Base64 encoded email"),
    t: str = Query(..., description="Unsubscribe token"),
    db: AsyncSession = Depends(get_db)
):
    """
    Handle unsubscribe requests.
    """
    try:
        import base64
        from ....outbound.utils import verify_unsub_token
        
        # Decode email
        try:
            email = base64.urlsafe_b64decode(e).decode('utf-8')
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid email encoding")
        
        # Verify token
        if not verify_unsub_token(email, t, settings.secret_key):
            raise HTTPException(status_code=400, detail="Invalid unsubscribe token")
        
        # Add to suppression list
        existing_suppression = await db.execute(
            db.query(Suppression).filter(Suppression.email == email).first()
        )
        
        if not existing_suppression:
            suppression = Suppression(
                email=email,
                reason="user_unsubscribed"
            )
            db.add(suppression)
            await db.commit()
        
        # Return success page
        return {
            "status": "success",
            "message": "You have been successfully unsubscribed",
            "email": email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing unsubscribe: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


async def _handle_bounce(db: AsyncSession, email: str, payload: Dict[str, Any]):
    """Handle email bounce event."""
    try:
        # Add to suppression list
        existing_suppression = await db.execute(
            db.query(Suppression).filter(Suppression.email == email).first()
        )
        
        if not existing_suppression:
            suppression = Suppression(
                email=email,
                reason="bounced"
            )
            db.add(suppression)
            await db.commit()
        
        logger.info(f"Email bounced: {email}")
        
    except Exception as e:
        logger.error(f"Error handling bounce: {e}")


async def _handle_complaint(db: AsyncSession, email: str, payload: Dict[str, Any]):
    """Handle email complaint event."""
    try:
        # Add to suppression list
        existing_suppression = await db.execute(
            db.query(Suppression).filter(Suppression.email == email).first()
        )
        
        if not existing_suppression:
            suppression = Suppression(
                email=email,
                reason="complained"
            )
            db.add(suppression)
            await db.commit()
        
        logger.info(f"Email complained: {email}")
        
    except Exception as e:
        logger.error(f"Error handling complaint: {e}")


async def _handle_open(db: AsyncSession, email: str, payload: Dict[str, Any]):
    """Handle email open event."""
    try:
        # Log open event
        logger.info(f"Email opened: {email}")
        
    except Exception as e:
        logger.error(f"Error handling open: {e}")


async def _handle_click(db: AsyncSession, email: str, payload: Dict[str, Any]):
    """Handle email click event."""
    try:
        # Log click event
        logger.info(f"Email clicked: {email}")
        
    except Exception as e:
        logger.error(f"Error handling click: {e}")


async def _handle_reply(db: AsyncSession, email: str, payload: Dict[str, Any]):
    """Handle email reply event."""
    try:
        # Log reply event
        logger.info(f"Email replied: {email}")
        
    except Exception as e:
        logger.error(f"Error handling reply: {e}")
