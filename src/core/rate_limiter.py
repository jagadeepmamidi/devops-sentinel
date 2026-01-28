"""
Rate Limiter - API Rate Limiting for Free Tier Protection
==========================================================

Prevent abuse of free tier with intelligent rate limiting
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import asyncio


class RateLimiter:
    """
    Rate limiting with BYOK (Bring Your Own Key) support
    
    Tier Model:
    - byok: Users provide their own API keys = UNLIMITED (they pay their own costs)
    - free: No API keys, limited demo access
    - pro: We provide managed infrastructure = Higher limits
    - enterprise: Dedicated infrastructure = Unlimited
    """
    
    TIER_LIMITS = {
        # BYOK - Users provide their own API keys, unlimited usage
        # They pay OpenAI/Supabase directly, we just provide the platform
        'byok': {
            'health_checks_per_minute': -1,  # unlimited
            'health_checks_per_day': -1,
            'api_calls_per_minute': -1,
            'api_calls_per_hour': -1,
            'postmortems_per_hour': -1,
            'postmortems_per_day': -1,
            'incidents_per_month': -1,
            'similarity_searches_per_hour': -1
        },
        # Free tier - No API keys, limited demo
        'free': {
            'health_checks_per_minute': 10,
            'health_checks_per_day': 100,  # Very limited without keys
            'api_calls_per_minute': 20,
            'api_calls_per_hour': 200,
            'postmortems_per_hour': 0,  # Requires AI key
            'postmortems_per_day': 0,
            'incidents_per_month': 10,
            'similarity_searches_per_hour': 0  # Requires embedding key
        },
        # Pro - Managed infrastructure (we provide keys)
        'pro': {
            'health_checks_per_minute': 100,
            'health_checks_per_day': 50000,
            'api_calls_per_minute': 300,
            'api_calls_per_hour': 10000,
            'postmortems_per_hour': 20,
            'postmortems_per_day': -1,
            'incidents_per_month': -1,
            'similarity_searches_per_hour': 100
        },
        # Enterprise - Dedicated infrastructure
        'enterprise': {
            'health_checks_per_minute': -1,
            'health_checks_per_day': -1,
            'api_calls_per_minute': -1,
            'api_calls_per_hour': -1,
            'postmortems_per_hour': -1,
            'postmortems_per_day': -1,
            'incidents_per_month': -1,
            'similarity_searches_per_hour': -1
        }
    }
    
    # Time windows in seconds
    TIME_WINDOWS = {
        'minute': 60,
        'hour': 3600,
        'day': 86400,
        'month': 2592000  # 30 days
    }
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self._cache = {}  # In-memory cache for performance
    
    async def check_rate_limit(
        self,
        user_id: str,
        action: str,
        tier: Optional[str] = None
    ) -> Dict:
        """
        Check if user action is within rate limits
        
        Args:
            user_id: User performing action
            action: Action type (health_checks, api_calls, postmortems, etc)
            tier: User tier (if known, skips lookup)
        
        Returns:
            Dict with allowed status and limit info
        
        Raises:
            RateLimitExceeded if over limit
        """
        if tier is None:
            tier = await self._get_user_tier(user_id)
        
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS['free'])
        
        # Check each relevant time window
        for window in ['minute', 'hour', 'day', 'month']:
            limit_key = f"{action}_per_{window}"
            
            if limit_key not in limits:
                continue
            
            limit_value = limits[limit_key]
            
            # -1 = unlimited
            if limit_value < 0:
                continue
            
            # Get current count
            count = await self._get_action_count(user_id, action, window)
            
            if count >= limit_value:
                raise RateLimitExceeded(
                    action=action,
                    window=window,
                    limit=limit_value,
                    current=count,
                    tier=tier
                )
        
        # Log this action
        await self._log_action(user_id, action)
        
        return {
            'allowed': True,
            'tier': tier,
            'action': action
        }
    
    async def get_remaining_quota(
        self,
        user_id: str,
        action: str
    ) -> Dict:
        """
        Get remaining quota for an action
        
        Returns dict with remaining counts for each time window
        """
        tier = await self._get_user_tier(user_id)
        limits = self.TIER_LIMITS.get(tier, self.TIER_LIMITS['free'])
        
        remaining = {}
        
        for window in ['minute', 'hour', 'day', 'month']:
            limit_key = f"{action}_per_{window}"
            
            if limit_key not in limits:
                continue
            
            limit_value = limits[limit_key]
            
            if limit_value < 0:
                remaining[window] = float('inf')
            else:
                count = await self._get_action_count(user_id, action, window)
                remaining[window] = max(0, limit_value - count)
        
        return {
            'action': action,
            'tier': tier,
            'remaining': remaining,
            'limits': {
                k: v for k, v in limits.items() 
                if k.startswith(action)
            }
        }
    
    async def _get_action_count(
        self,
        user_id: str,
        action: str,
        window: str
    ) -> int:
        """Get count of actions in time window"""
        seconds = self.TIME_WINDOWS.get(window, 60)
        since = datetime.utcnow() - timedelta(seconds=seconds)
        
        result = await self.supabase.table('rate_limit_log').select(
            'id',
            count='exact'
        ).eq('user_id', user_id).eq(
            'action', action
        ).gte('timestamp', since.isoformat()).execute()
        
        return result.count if hasattr(result, 'count') else len(result.data)
    
    async def _log_action(self, user_id: str, action: str):
        """Log an action for rate limiting"""
        await self.supabase.table('rate_limit_log').insert({
            'user_id': user_id,
            'action': action,
            'timestamp': datetime.utcnow().isoformat()
        }).execute()
    
    async def _get_user_tier(self, user_id: str) -> str:
        """Get user subscription tier"""
        # Check cache first
        cache_key = f"tier:{user_id}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached['expires'] > datetime.utcnow():
                return cached['tier']
        
        result = await self.supabase.table('users').select(
            'subscription_tier'
        ).eq('id', user_id).execute()
        
        tier = 'free'
        if result.data:
            tier = result.data[0].get('subscription_tier', 'free')
        
        # Cache for 5 minutes
        self._cache[cache_key] = {
            'tier': tier,
            'expires': datetime.utcnow() + timedelta(minutes=5)
        }
        
        return tier
    
    async def cleanup_old_logs(self, days: int = 7):
        """Clean up old rate limit logs"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        await self.supabase.table('rate_limit_log').delete().lt(
            'timestamp', cutoff.isoformat()
        ).execute()


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""
    
    def __init__(
        self,
        action: str,
        window: str,
        limit: int,
        current: int,
        tier: str
    ):
        self.action = action
        self.window = window
        self.limit = limit
        self.current = current
        self.tier = tier
        
        self.message = (
            f"Rate limit exceeded for {action}: "
            f"{current}/{limit} per {window} ({tier} tier). "
            f"Try again later or upgrade to Pro for higher limits."
        )
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict:
        return {
            'error': 'rate_limit_exceeded',
            'action': self.action,
            'window': self.window,
            'limit': self.limit,
            'current': self.current,
            'tier': self.tier,
            'message': self.message
        }


# Decorator for easy rate limiting
def rate_limit(action: str):
    """Decorator to rate limit an endpoint"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user_id from request context
            user_id = kwargs.get('user_id') or kwargs.get('current_user', {}).get('id')
            
            if user_id:
                from .rate_limiter import RateLimiter
                limiter = RateLimiter(kwargs.get('supabase'))
                await limiter.check_rate_limit(user_id, action)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Example usage
if __name__ == "__main__":
    async def demo():
        class MockSupabase:
            def table(self, name):
                return self
            def insert(self, data):
                return self
            def select(self, *args, **kwargs):
                return self
            def eq(self, *args):
                return self
            def gte(self, *args):
                return self
            def lt(self, *args):
                return self
            def delete(self):
                return self
            async def execute(self):
                class R:
                    data = [{'subscription_tier': 'free'}]
                    count = 3
                return R()
        
        limiter = RateLimiter(MockSupabase())
        
        try:
            result = await limiter.check_rate_limit(
                user_id='user-123',
                action='postmortems'
            )
            print(f"Allowed: {result['allowed']}")
            
            quota = await limiter.get_remaining_quota('user-123', 'postmortems')
            print(f"Remaining: {quota['remaining']}")
            
        except RateLimitExceeded as e:
            print(f"Rate limited: {e.message}")
    
    asyncio.run(demo())
