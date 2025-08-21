"""
Subscription management service
"""
import stripe
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..config import PlanTier, get_plan_config, get_api_limit
from ..database import get_db
import os

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

class SubscriptionService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_checkout_session(
        self, 
        user_id: str, 
        plan_tier: PlanTier, 
        billing_cycle: str = "monthly",
        success_url: str = None,
        cancel_url: str = None
    ) -> Dict[str, Any]:
        """Create Stripe checkout session for subscription"""
        plan_config = get_plan_config(plan_tier)
        
        # Get the appropriate price ID
        price_id = (
            plan_config["stripe_price_id_yearly"] 
            if billing_cycle == "yearly" 
            else plan_config["stripe_price_id_monthly"]
        )
        
        if not price_id:
            raise ValueError(f"No Stripe price ID configured for {plan_tier.value} {billing_cycle}")
        
        try:
            # Create or retrieve customer
            customer = await self._get_or_create_stripe_customer(user_id)
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url or f"{os.getenv('FRONTEND_URL')}/settings?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url or f"{os.getenv('FRONTEND_URL')}/settings",
                metadata={
                    'user_id': user_id,
                    'plan_tier': plan_tier.value,
                    'billing_cycle': billing_cycle,
                }
            )
            
            return {
                'checkout_url': session.url,
                'session_id': session.id,
                'customer_id': customer.id,
            }
            
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    async def create_customer_portal_session(self, user_id: str, return_url: str = None) -> str:
        """Create Stripe customer portal session for subscription management"""
        try:
            # Get customer from database or Stripe
            customer = await self._get_stripe_customer(user_id)
            if not customer:
                raise ValueError("No Stripe customer found for user")
            
            # Create portal session
            session = stripe.billing_portal.Session.create(
                customer=customer.id,
                return_url=return_url or f"{os.getenv('FRONTEND_URL')}/settings",
            )
            
            return session.url
            
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    async def handle_webhook_event(self, event_data: Dict[str, Any], signature: str) -> bool:
        """Handle Stripe webhook events"""
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                event_data, signature, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise ValueError("Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid signature")
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            await self._handle_checkout_completed(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            await self._handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            await self._handle_subscription_cancelled(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            await self._handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'invoice.payment_failed':
            await self._handle_payment_failed(event['data']['object'])
        
        return True
    
    async def get_subscription_status(self, user_id: str) -> Dict[str, Any]:
        """Get current subscription status for user"""
        # Get user profile from database
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
        response = supabase.table('user_profiles').select('*').eq('id', user_id).single().execute()
        
        if not response.data:
            return {
                'tier': PlanTier.FREE.value,
                'status': 'active',
                'current_period_end': None,
                'cancel_at_period_end': False,
            }
        
        profile = response.data
        return {
            'tier': profile.get('subscription_tier', PlanTier.FREE.value),
            'status': profile.get('subscription_status', 'active'),
            'current_period_end': profile.get('subscription_current_period_end'),
            'cancel_at_period_end': profile.get('subscription_cancel_at_period_end', False),
            'stripe_customer_id': profile.get('stripe_customer_id'),
        }
    
    async def cancel_subscription(self, user_id: str) -> bool:
        """Cancel subscription at period end"""
        try:
            subscription_status = await self.get_subscription_status(user_id)
            stripe_customer_id = subscription_status.get('stripe_customer_id')
            
            if not stripe_customer_id:
                raise ValueError("No Stripe customer found")
            
            # Get active subscription
            subscriptions = stripe.Subscription.list(customer=stripe_customer_id, status='active')
            
            if not subscriptions.data:
                raise ValueError("No active subscription found")
            
            subscription = subscriptions.data[0]
            
            # Cancel at period end
            stripe.Subscription.modify(
                subscription.id,
                cancel_at_period_end=True
            )
            
            # Update database
            from supabase import create_client
            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_ANON_KEY")
            )
            
            supabase.table('user_profiles').update({
                'subscription_cancel_at_period_end': True
            }).eq('id', user_id).execute()
            
            return True
            
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    async def reactivate_subscription(self, user_id: str) -> bool:
        """Reactivate a cancelled subscription"""
        try:
            subscription_status = await self.get_subscription_status(user_id)
            stripe_customer_id = subscription_status.get('stripe_customer_id')
            
            if not stripe_customer_id:
                raise ValueError("No Stripe customer found")
            
            # Get subscription
            subscriptions = stripe.Subscription.list(customer=stripe_customer_id)
            
            if not subscriptions.data:
                raise ValueError("No subscription found")
            
            subscription = subscriptions.data[0]
            
            # Reactivate subscription
            stripe.Subscription.modify(
                subscription.id,
                cancel_at_period_end=False
            )
            
            # Update database
            from supabase import create_client
            supabase = create_client(
                os.getenv("SUPABASE_URL"),
                os.getenv("SUPABASE_ANON_KEY")
            )
            
            supabase.table('user_profiles').update({
                'subscription_cancel_at_period_end': False
            }).eq('id', user_id).execute()
            
            return True
            
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    # Private helper methods
    async def _get_or_create_stripe_customer(self, user_id: str) -> stripe.Customer:
        """Get existing Stripe customer or create new one"""
        # First check if customer exists in database
        customer = await self._get_stripe_customer(user_id)
        if customer:
            return customer
        
        # Get user email from Supabase
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
        # Get user data from auth
        user_response = supabase.auth.admin.get_user_by_id(user_id)
        if not user_response.user:
            raise ValueError("User not found")
        
        user_email = user_response.user.email
        
        # Create new Stripe customer
        customer = stripe.Customer.create(
            email=user_email,
            metadata={'user_id': user_id}
        )
        
        # Save customer ID to database
        supabase.table('user_profiles').upsert({
            'id': user_id,
            'stripe_customer_id': customer.id,
        }).execute()
        
        return customer
    
    async def _get_stripe_customer(self, user_id: str) -> Optional[stripe.Customer]:
        """Get Stripe customer from database"""
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
        response = supabase.table('user_profiles').select('stripe_customer_id').eq('id', user_id).single().execute()
        
        if response.data and response.data.get('stripe_customer_id'):
            try:
                return stripe.Customer.retrieve(response.data['stripe_customer_id'])
            except stripe.error.StripeError:
                return None
        
        return None
    
    async def _handle_checkout_completed(self, session: Dict[str, Any]):
        """Handle successful checkout completion"""
        user_id = session['metadata']['user_id']
        plan_tier = session['metadata']['plan_tier']
        
        # Get subscription details
        subscription_id = session['subscription']
        subscription = stripe.Subscription.retrieve(subscription_id)
        
        # Update user profile
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
        plan_config = get_plan_config(PlanTier(plan_tier))
        
        supabase.table('user_profiles').upsert({
            'id': user_id,
            'subscription_tier': plan_tier,
            'subscription_status': 'active',
            'subscription_id': subscription_id,
            'stripe_customer_id': session['customer'],
            'subscription_current_period_end': datetime.fromtimestamp(subscription.current_period_end).isoformat(),
            'api_calls_limit': plan_config['api_calls_limit'],
            'api_calls_used': 0,  # Reset usage on new subscription
        }).execute()
    
    async def _handle_subscription_updated(self, subscription: Dict[str, Any]):
        """Handle subscription updates"""
        customer_id = subscription['customer']
        
        # Find user by customer ID
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
        response = supabase.table('user_profiles').select('*').eq('stripe_customer_id', customer_id).single().execute()
        
        if response.data:
            # Determine plan tier from subscription
            plan_tier = self._get_plan_tier_from_subscription(subscription)
            plan_config = get_plan_config(plan_tier)
            
            supabase.table('user_profiles').update({
                'subscription_tier': plan_tier.value,
                'subscription_status': subscription['status'],
                'subscription_current_period_end': datetime.fromtimestamp(subscription['current_period_end']).isoformat(),
                'subscription_cancel_at_period_end': subscription.get('cancel_at_period_end', False),
                'api_calls_limit': plan_config['api_calls_limit'],
            }).eq('stripe_customer_id', customer_id).execute()
    
    async def _handle_subscription_cancelled(self, subscription: Dict[str, Any]):
        """Handle subscription cancellation"""
        customer_id = subscription['customer']
        
        # Find user by customer ID and downgrade to free
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
        free_plan = get_plan_config(PlanTier.FREE)
        
        supabase.table('user_profiles').update({
            'subscription_tier': PlanTier.FREE.value,
            'subscription_status': 'cancelled',
            'subscription_id': None,
            'subscription_current_period_end': None,
            'subscription_cancel_at_period_end': False,
            'api_calls_limit': free_plan['api_calls_limit'],
            'api_calls_used': 0,  # Reset usage
        }).eq('stripe_customer_id', customer_id).execute()
    
    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]):
        """Handle successful payment"""
        # Reset monthly usage count
        customer_id = invoice['customer']
        
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
        supabase.table('user_profiles').update({
            'api_calls_used': 0,  # Reset monthly usage
        }).eq('stripe_customer_id', customer_id).execute()
    
    async def _handle_payment_failed(self, invoice: Dict[str, Any]):
        """Handle failed payment"""
        customer_id = invoice['customer']
        
        # You might want to send notifications, temporarily suspend access, etc.
        # For now, just log the event
        print(f"Payment failed for customer {customer_id}")
    
    def _get_plan_tier_from_subscription(self, subscription: Dict[str, Any]) -> PlanTier:
        """Determine plan tier from Stripe subscription"""
        # Get the price ID from the subscription
        price_id = subscription['items']['data'][0]['price']['id']
        
        # Map price IDs to plan tiers
        for tier, config in SUBSCRIPTION_PLANS.items():
            if (config.get('stripe_price_id_monthly') == price_id or 
                config.get('stripe_price_id_yearly') == price_id):
                return tier
        
        # Default to free if not found
        return PlanTier.FREE