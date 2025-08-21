"""
Subscription management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import stripe
import json

from ..services.subscription import SubscriptionService
from ..config import PlanTier, get_plan_comparison
from ..middleware.usage_limiter import get_user_id_from_token, check_api_limit_no_increment
from ..database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/subscription", tags=["subscription"])

# Pydantic models
class CreateCheckoutRequest(BaseModel):
    plan_tier: str
    billing_cycle: str = "monthly"  # monthly or yearly
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None

class CreatePortalRequest(BaseModel):
    return_url: Optional[str] = None

class WebhookPayload(BaseModel):
    data: Dict[str, Any]

@router.get("/plans")
async def get_subscription_plans():
    """Get all available subscription plans"""
    return {
        "plans": get_plan_comparison(),
        "success": True
    }

@router.get("/status")
async def get_subscription_status(
    user_id: str = Depends(get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Get current subscription status for user"""
    try:
        subscription_service = SubscriptionService(db)
        status = await subscription_service.get_subscription_status(user_id)
        
        # Also get current usage
        usage_info = await check_api_limit_no_increment(user_id)
        
        return {
            "subscription": status,
            "usage": usage_info,
            "success": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/checkout")
async def create_checkout_session(
    request: CreateCheckoutRequest,
    user_id: str = Depends(get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Create Stripe checkout session for subscription upgrade"""
    try:
        # Validate plan tier
        try:
            plan_tier = PlanTier(request.plan_tier)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid plan tier")
        
        # Validate billing cycle
        if request.billing_cycle not in ["monthly", "yearly"]:
            raise HTTPException(status_code=400, detail="Invalid billing cycle")
        
        subscription_service = SubscriptionService(db)
        checkout_session = await subscription_service.create_checkout_session(
            user_id=user_id,
            plan_tier=plan_tier,
            billing_cycle=request.billing_cycle,
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        
        return {
            "checkout_url": checkout_session["checkout_url"],
            "session_id": checkout_session["session_id"],
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/portal")
async def create_customer_portal(
    request: CreatePortalRequest,
    user_id: str = Depends(get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Create Stripe customer portal session for subscription management"""
    try:
        subscription_service = SubscriptionService(db)
        portal_url = await subscription_service.create_customer_portal_session(
            user_id=user_id,
            return_url=request.return_url
        )
        
        return {
            "portal_url": portal_url,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel")
async def cancel_subscription(
    user_id: str = Depends(get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Cancel subscription at period end"""
    try:
        subscription_service = SubscriptionService(db)
        success = await subscription_service.cancel_subscription(user_id)
        
        return {
            "cancelled": success,
            "message": "Subscription will be cancelled at the end of the current period",
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reactivate")
async def reactivate_subscription(
    user_id: str = Depends(get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Reactivate a cancelled subscription"""
    try:
        subscription_service = SubscriptionService(db)
        success = await subscription_service.reactivate_subscription(user_id)
        
        return {
            "reactivated": success,
            "message": "Subscription has been reactivated",
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    try:
        # Get raw body and signature
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        subscription_service = SubscriptionService(db)
        await subscription_service.handle_webhook_event(payload, signature)
        
        return {"success": True}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usage")
async def get_usage_details(
    user_id: str = Depends(get_user_id_from_token)
):
    """Get detailed usage information"""
    try:
        usage_info = await check_api_limit_no_increment(user_id)
        
        # Get usage history from database (optional)
        # You could add more detailed usage analytics here
        
        return {
            "usage": usage_info,
            "success": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/verify-session/{session_id}")
async def verify_checkout_session(
    session_id: str,
    user_id: str = Depends(get_user_id_from_token),
    db: Session = Depends(get_db)
):
    """Verify completed checkout session"""
    try:
        # Retrieve session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == "paid":
            return {
                "verified": True,
                "status": "paid",
                "subscription_id": session.subscription,
                "success": True
            }
        else:
            return {
                "verified": False,
                "status": session.payment_status,
                "success": True
            }
            
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))