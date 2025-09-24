"""API endpoints for billing and subscription management."""

# Force deployment refresh

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

# Import with error handling
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    stripe = None
    STRIPE_AVAILABLE = False

try:
    from ....db.session import get_db
    from ....db.crud import UserCRUD
    from ....core.config import settings
    from ....core.logging import logger
    DB_AVAILABLE = True
except ImportError as e:
    print(f"Database imports failed: {e}")
    get_db = None
    UserCRUD = None
    settings = None
    logger = None
    DB_AVAILABLE = False

# Initialize Stripe early
if stripe and settings:
    stripe_secret_key = getattr(settings, 'stripe_secret_key', None)
    if stripe_secret_key:
        stripe.api_key = stripe_secret_key
        print(f"DEBUG: Stripe secret key configured: {bool(stripe.api_key)}")
        print(f"DEBUG: Stripe secret key starts with: {stripe.api_key[:10] if stripe.api_key else 'None'}")
    else:
        print("DEBUG: No Stripe secret key found in settings")
        logger.warning("Stripe secret key not configured - billing endpoints will be disabled")
        # Don't fail the module load, just disable Stripe functionality

router = APIRouter()

# Helper functions
async def get_current_user_email(
    x_user_email: Optional[str] = Header(None, alias="X-User-Email")
) -> str:
    """Get current user email from header and ensure user exists."""
    if not x_user_email:
        raise HTTPException(status_code=401, detail="X-User-Email header required")
    
    return x_user_email

# Test endpoint to verify billing module is loaded
@router.get("/test")
async def billing_test():
    """Test endpoint to verify billing module is loaded."""
    return {
        "status": "billing module loaded successfully",
        "stripe_available": STRIPE_AVAILABLE,
        "db_available": DB_AVAILABLE,
        "stripe_configured": bool(stripe and hasattr(settings, 'stripe_secret_key') and settings.stripe_secret_key) if settings else False
    }

@router.post("/test-checkout")
async def test_checkout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_email: str = Depends(get_current_user_email)
):
    """Test endpoint to debug checkout session creation."""
    try:
        if not stripe.api_key:
            return {"error": "Stripe not configured", "stripe_configured": False}
        
        body = await request.json()
        price_id = body.get("price_id", "price_starter")
        
        # Test Stripe connection
        try:
            # Try to retrieve the price to see if it exists
            price = stripe.Price.retrieve(price_id)
            return {
                "status": "success",
                "stripe_configured": True,
                "price_exists": True,
                "price_id": price_id,
                "price_details": {
                    "id": price.id,
                    "active": price.active,
                    "unit_amount": price.unit_amount,
                    "currency": price.currency
                }
            }
        except stripe.error.InvalidRequestError as e:
            return {
                "status": "error",
                "stripe_configured": True,
                "price_exists": False,
                "price_id": price_id,
                "error": str(e)
            }
        except Exception as e:
            return {
                "status": "error",
                "stripe_configured": True,
                "error": str(e)
            }
            
    except Exception as e:
        return {"error": f"Test failed: {str(e)}"}

async def ensure_user_exists(db: AsyncSession, email: str) -> uuid.UUID:
    """Ensure user exists in database, create if not."""
    user = await UserCRUD.get_by_email(db, email)
    if not user:
        from ....db.schemas import UserCreate
        user = await UserCRUD.create(db, UserCreate(email=email))
        logger.info(f"Created new user: {email}")
    
    return user.id


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user_email: str = Depends(get_current_user_email)
):
    """Create a Stripe checkout session for subscription."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    user_id = await ensure_user_exists(db, user_email)
    
    try:
        body = await request.json()
        price_id = body.get("price_id")
        
        if not price_id:
            raise HTTPException(status_code=400, detail="price_id is required")
        
        # Create or get Stripe customer
        customer = await get_or_create_stripe_customer(user_email, user_id)
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                }
            ],
            mode='subscription',
            success_url=f"{request.base_url}account?success=true",
            cancel_url=f"{request.base_url}pricing?canceled=true",
            metadata={
                'user_id': str(user_id),
                'user_email': user_email,
            }
        )
        
        logger.info(f"Created checkout session for user {user_email}: {session.id}")
        return {"url": session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating checkout session: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.get("/portal")
async def get_billing_portal(
    db: AsyncSession = Depends(get_db),
    user_email: str = Depends(get_current_user_email)
):
    """Get Stripe billing portal URL."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    user_id = await ensure_user_exists(db, user_email)
    
    try:
        # Get or create Stripe customer
        customer = await get_or_create_stripe_customer(user_email, user_id)
        
        # Create billing portal session
        session = stripe.billing_portal.Session.create(
            customer=customer.id,
            return_url=f"{settings.frontend_url or 'http://localhost:3000'}/account",
        )
        
        logger.info(f"Created billing portal session for user {user_email}")
        return {"url": session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating billing portal: {e}")
        raise HTTPException(status_code=500, detail="Failed to create billing portal")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks."""
    if not stripe.api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = getattr(settings, 'stripe_webhook_secret', None)
    
    if not webhook_secret:
        logger.warning("Stripe webhook secret not configured")
        return {"status": "webhook secret not configured"}
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        logger.error("Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle the event
    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            await handle_checkout_completed(session)
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            await handle_subscription_updated(subscription)
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            await handle_subscription_deleted(subscription)
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            await handle_payment_succeeded(invoice)
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            await handle_payment_failed(invoice)
        else:
            logger.info(f"Unhandled event type: {event['type']}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def get_or_create_stripe_customer(email: str, user_id: uuid.UUID):
    """Get or create a Stripe customer."""
    try:
        # Try to find existing customer
        customers = stripe.Customer.list(email=email, limit=1)
        if customers.data:
            return customers.data[0]
        
        # Create new customer
        customer = stripe.Customer.create(
            email=email,
            metadata={
                'user_id': str(user_id),
            }
        )
        logger.info(f"Created Stripe customer for user {email}: {customer.id}")
        return customer
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe customer error: {e}")
        raise


async def handle_checkout_completed(session):
    """Handle successful checkout completion."""
    user_id = session.get('metadata', {}).get('user_id')
    user_email = session.get('metadata', {}).get('user_email')
    
    if user_id and user_email:
        logger.info(f"Checkout completed for user {user_email}: {session['id']}")
        # In a real app, you'd update the user's subscription status in your database
        # For now, we'll just log it


async def handle_subscription_updated(subscription):
    """Handle subscription updates."""
    customer_id = subscription.get('customer')
    logger.info(f"Subscription updated: {subscription['id']} for customer {customer_id}")
    # In a real app, you'd update the subscription status in your database


async def handle_subscription_deleted(subscription):
    """Handle subscription cancellation."""
    customer_id = subscription.get('customer')
    logger.info(f"Subscription canceled: {subscription['id']} for customer {customer_id}")
    # In a real app, you'd update the subscription status in your database


async def handle_payment_succeeded(invoice):
    """Handle successful payment."""
    customer_id = invoice.get('customer')
    logger.info(f"Payment succeeded for customer {customer_id}: {invoice['id']}")
    # In a real app, you'd update the payment status in your database


async def handle_payment_failed(invoice):
    """Handle failed payment."""
    customer_id = invoice.get('customer')
    logger.info(f"Payment failed for customer {customer_id}: {invoice['id']}")
    # In a real app, you'd update the payment status and notify the user
