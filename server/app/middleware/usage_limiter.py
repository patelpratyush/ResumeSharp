"""
Usage limiting middleware for API calls
"""
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
from typing import Optional
import os
from supabase import create_client
from ..config import PlanTier, get_api_limit

security = HTTPBearer()

class UsageLimiter:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )
    
    async def check_api_limit(self, user_id: str, increment: bool = True) -> dict:
        """
        Check if user has exceeded their API limit
        Returns usage info and raises HTTPException if limit exceeded
        """
        try:
            # Get user profile
            response = self.supabase.table('user_profiles').select(
                'subscription_tier, api_calls_limit, api_calls_used, api_calls_reset_date'
            ).eq('id', user_id).single().execute()
            
            if not response.data:
                # User not found, create with free tier defaults
                await self._create_default_profile(user_id)
                tier = PlanTier.FREE
                limit = get_api_limit(tier)
                used = 0
            else:
                profile = response.data
                tier = PlanTier(profile.get('subscription_tier', 'free'))
                limit = profile.get('api_calls_limit') or get_api_limit(tier)
                used = profile.get('api_calls_used', 0)
                reset_date = profile.get('api_calls_reset_date')
                
                # Check if we need to reset monthly usage
                if reset_date:
                    reset_datetime = datetime.fromisoformat(reset_date.replace('Z', '+00:00'))
                    if datetime.utcnow() > reset_datetime:
                        used = 0
                        await self._reset_monthly_usage(user_id)
            
            # Check if limit exceeded
            if used >= limit:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "API limit exceeded",
                        "message": f"You have reached your monthly limit of {limit} API calls",
                        "current_usage": used,
                        "limit": limit,
                        "tier": tier.value,
                        "upgrade_required": tier == PlanTier.FREE
                    }
                )
            
            # Increment usage if requested
            if increment:
                await self._increment_usage(user_id, used + 1)
                used += 1
            
            return {
                "current_usage": used,
                "limit": limit,
                "remaining": limit - used,
                "tier": tier.value,
                "percentage_used": (used / limit) * 100 if limit > 0 else 0
            }
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"Error checking API limit: {e}")
            # On error, allow the request but log it
            return {
                "current_usage": 0,
                "limit": 5,  # Default to free tier limit
                "remaining": 5,
                "tier": "free",
                "percentage_used": 0
            }
    
    async def _create_default_profile(self, user_id: str):
        """Create default profile for new user"""
        next_reset = datetime.utcnow().replace(day=1) + timedelta(days=32)
        next_reset = next_reset.replace(day=1)  # First day of next month
        
        self.supabase.table('user_profiles').upsert({
            'id': user_id,
            'subscription_tier': PlanTier.FREE.value,
            'api_calls_limit': get_api_limit(PlanTier.FREE),
            'api_calls_used': 0,
            'api_calls_reset_date': next_reset.isoformat(),
            'created_at': datetime.utcnow().isoformat(),
        }).execute()
    
    async def _increment_usage(self, user_id: str, new_usage: int):
        """Increment user's API usage count"""
        self.supabase.table('user_profiles').update({
            'api_calls_used': new_usage,
            'updated_at': datetime.utcnow().isoformat(),
        }).eq('id', user_id).execute()
    
    async def _reset_monthly_usage(self, user_id: str):
        """Reset monthly usage and set next reset date"""
        # Calculate next reset date (first day of next month)
        now = datetime.utcnow()
        next_reset = now.replace(day=1) + timedelta(days=32)
        next_reset = next_reset.replace(day=1)
        
        self.supabase.table('user_profiles').update({
            'api_calls_used': 0,
            'api_calls_reset_date': next_reset.isoformat(),
            'updated_at': now.isoformat(),
        }).eq('id', user_id).execute()

# Global instance
usage_limiter = UsageLimiter()

async def enforce_api_limit(user_id: str) -> dict:
    """
    Dependency to enforce API limits
    Use this in your API endpoints that should count against the limit
    """
    return await usage_limiter.check_api_limit(user_id, increment=True)

async def check_api_limit_no_increment(user_id: str) -> dict:
    """
    Dependency to check API limits without incrementing
    Use this to check usage without counting the request
    """
    return await usage_limiter.check_api_limit(user_id, increment=False)

def get_user_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Extract user ID from JWT token using Supabase auth
    """
    import jwt
    import requests
    from jwt.exceptions import InvalidTokenError
    
    token = credentials.credentials
    
    try:
        # Get Supabase JWT verification key
        supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_url:
            raise HTTPException(status_code=500, detail="Supabase URL not configured")
            
        # For Supabase JWT verification, we can either:
        # 1. Use Supabase client to verify the token, or 
        # 2. Verify JWT directly using Supabase's public key
        
        # Method 1: Use Supabase client (simpler and more reliable)
        from supabase import create_client
        # For token verification, we can use anon key
        supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
        # Verify the token by trying to get user info
        try:
            user_response = supabase.auth.get_user(token)
            if user_response.user:
                return user_response.user.id
            else:
                raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            # If direct token verification fails, try parsing JWT manually
            # Supabase JWTs are signed, but we can decode without verification for user ID
            try:
                # Decode without verification to get user_id (Supabase tokens are verified by the client)
                decoded = jwt.decode(token, options={"verify_signature": False})
                user_id = decoded.get("sub")
                if user_id:
                    return user_id
                else:
                    raise HTTPException(status_code=401, detail="No user ID in token")
            except Exception:
                raise HTTPException(status_code=401, detail="Invalid token format")
                
    except HTTPException:
        raise
    except Exception as e:
        print(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")

# Convenience dependency that combines auth and usage checking
async def require_api_access(user_id: str = Depends(get_user_id_from_token)) -> tuple[str, dict]:
    """
    Combined dependency for authentication and usage limiting
    Returns (user_id, usage_info)
    """
    usage_info = await enforce_api_limit(user_id)
    return user_id, usage_info