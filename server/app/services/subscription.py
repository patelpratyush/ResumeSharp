"""
Subscription management service
"""
import stripe
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from supabase import create_client, Client
from ..config import PlanTier, get_plan_config, get_api_limit
import os

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

class SubscriptionService:
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
    
    async def create_checkout_session(
        self, 
        user_id: str, 
        plan_tier: PlanTier, 
        billing_cycle: str = "monthly",
        success_url: str = None,
        cancel_url: str = None
    ) -> Dict[str, Any]:
        """Create Stripe checkout session for subscription with monthly/yearly options"""
        plan_config = get_plan_config(plan_tier)
        
        # Get both price IDs for the plan
        monthly_price_id = plan_config["stripe_price_id_monthly"]
        yearly_price_id = plan_config["stripe_price_id_yearly"]
        
        if not monthly_price_id or not yearly_price_id:
            raise ValueError(f"Missing Stripe price IDs for {plan_tier.value} plan")
        
        try:
            # Create or retrieve customer
            customer = await self._get_or_create_stripe_customer(user_id)
            
            # Use the selected billing cycle as default, but configure for switching
            primary_price_id = monthly_price_id if billing_cycle == "monthly" else yearly_price_id
            
            # Create checkout session with selected billing cycle
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card'],
                line_items=[{
                    'price': primary_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url or f"{os.getenv('FRONTEND_URL')}/dashboard?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url or f"{os.getenv('FRONTEND_URL')}/pricing?checkout_cancelled=true",
                allow_promotion_codes=True,
                billing_address_collection='auto',
                subscription_data={
                    'description': f'{plan_tier.value.title()} Plan - {billing_cycle.title()} Billing'
                },
                metadata={
                    'user_id': user_id,
                    'plan_tier': plan_tier.value,
                    'billing_cycle': billing_cycle,
                    'monthly_price_id': monthly_price_id,
                    'yearly_price_id': yearly_price_id,
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
            print(f"Getting Stripe customer for user: {user_id}")
            # Get customer from database or Stripe, create if needed
            customer = await self._get_stripe_customer(user_id)
            if not customer:
                print(f"No existing customer found, creating new one for user: {user_id}")
                # Create customer if they don't exist
                try:
                    customer = await self._get_or_create_stripe_customer(user_id)
                except Exception as create_error:
                    print(f"Customer creation failed: {create_error}")
                    # Check if there's an existing Stripe customer we can use
                    customer = await self._find_stripe_customer_by_metadata(user_id)
                    if not customer:
                        raise create_error
            
            print(f"Creating billing portal session for customer: {customer.id}")
            # Create portal session
            session = stripe.billing_portal.Session.create(
                customer=customer.id,
                return_url=return_url or f"{os.getenv('FRONTEND_URL')}/settings",
            )
            
            print(f"Portal session created successfully: {session.url}")
            return session.url
            
        except stripe.error.StripeError as e:
            print(f"Stripe API error: {str(e)}")
            raise Exception(f"Stripe error: {str(e)}")
        except Exception as e:
            print(f"General error in create_customer_portal_session: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Customer portal error: {str(e)}")
    
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
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
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
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
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
                os.getenv("SUPABASE_SERVICE_ROLE_KEY")
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
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for admin operations
        )
        
        # Get user email - multiple fallback strategies
        user_email = None
        
        # Strategy 1: Try admin API with service role
        try:
            user_response = supabase.auth.admin.get_user_by_id(user_id)
            if user_response.user and user_response.user.email:
                user_email = user_response.user.email
        except Exception as e:
            print(f"Admin auth failed: {e}")
        
        # Strategy 2: Try to get from user_profiles table
        if not user_email:
            try:
                # Try different possible email column names
                for email_col in ['email', 'user_email', 'contact_email']:
                    try:
                        profile_response = supabase.table('user_profiles').select(email_col).eq('id', user_id).single().execute()
                        if profile_response.data and profile_response.data.get(email_col):
                            user_email = profile_response.data[email_col]
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Profile email lookup failed: {e}")
        
        # Strategy 3: Use placeholder email with user ID
        if not user_email:
            user_email = f"user-{user_id}@temp.stripe.customer"
            print(f"Warning: Using placeholder email for user {user_id}")
        
        # Create new Stripe customer
        customer = stripe.Customer.create(
            email=user_email,
            metadata={'user_id': user_id}
        )
        
        # Save customer ID to database
        try:
            # Check if profile exists first
            existing_profile = supabase.table('user_profiles').select('id, email').eq('id', user_id).execute()
            
            if existing_profile.data:
                # Profile exists, update it (including email if it's null)
                update_data = {'stripe_customer_id': customer.id}
                if not existing_profile.data[0].get('email'):
                    update_data['email'] = user_email
                
                supabase.table('user_profiles').update(update_data).eq('id', user_id).execute()
            else:
                # Profile doesn't exist, create it
                supabase.table('user_profiles').insert({
                    'id': user_id,
                    'stripe_customer_id': customer.id,
                    'email': user_email,
                    'subscription_tier': 'free',
                    'api_calls_limit': 5,
                    'api_calls_used': 0,
                }).execute()
        except Exception as e:
            print(f"Warning: Could not save customer ID to database: {e}")
            # Continue anyway since Stripe customer was created successfully
        
        return customer
    
    async def _get_stripe_customer(self, user_id: str) -> Optional[stripe.Customer]:
        """Get Stripe customer from database"""
        from supabase import create_client
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
        
        response = supabase.table('user_profiles').select('stripe_customer_id').eq('id', user_id).single().execute()
        
        if response.data and response.data.get('stripe_customer_id'):
            try:
                return stripe.Customer.retrieve(response.data['stripe_customer_id'])
            except stripe.error.StripeError:
                return None
        
        return None
    
    async def _find_stripe_customer_by_metadata(self, user_id: str) -> Optional[stripe.Customer]:
        """Find Stripe customer by user_id in metadata"""
        try:
            customers = stripe.Customer.list(limit=10)
            for customer in customers.data:
                if customer.metadata.get('user_id') == user_id:
                    return customer
            return None
        except stripe.error.StripeError:
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
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
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
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
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
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
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
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
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
        from ..config import SUBSCRIPTION_PLANS
        for tier, config in SUBSCRIPTION_PLANS.items():
            if (config.get('stripe_price_id_monthly') == price_id or 
                config.get('stripe_price_id_yearly') == price_id):
                return tier
        
        # Default to free if not found
        return PlanTier.FREE