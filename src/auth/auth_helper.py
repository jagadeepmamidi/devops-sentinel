"""
Authentication Helper - Supabase Auth Integration
==================================================

Simple auth helpers for user authentication
"""

from datetime import datetime
from typing import Dict, Optional
from fastapi import Request, HTTPException, Depends


class AuthHelper:
    """
    Authentication helper using Supabase Auth
    
    Usage:
        @app.get("/protected")
        async def protected_route(user: Dict = Depends(get_current_user)):
            return {"user": user}
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    async def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token from Supabase
        
        Returns user data if valid, None otherwise
        """
        if not token:
            return None
        
        try:
            # Supabase token verification
            result = await self.supabase.auth.get_user(token)
            
            if result and result.user:
                return {
                    'id': result.user.id,
                    'email': result.user.email,
                    'role': result.user.role,
                    'created_at': result.user.created_at
                }
        except Exception as e:
            print(f"[Auth] Token verification failed: {e}")
        
        return None
    
    async def get_user_from_request(self, request: Request) -> Optional[Dict]:
        """Extract and verify user from request"""
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.replace('Bearer ', '')
        return await self.verify_token(token)


# Dependency for protected routes
async def get_current_user(request: Request) -> Dict:
    """
    FastAPI dependency for protected routes
    
    Raises 401 if not authenticated
    """
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = auth_header.replace('Bearer ', '')
    
    # For development: accept any token and return mock user
    if token == 'dev-token':
        return {
            'id': 'dev-user-1',
            'email': 'dev@localhost',
            'role': 'admin',
            'tier': 'pro'
        }
    
    # In production: verify with Supabase
    # auth = AuthHelper(supabase_client)
    # user = await auth.verify_token(token)
    # if not user:
    #     raise HTTPException(401, "Invalid token")
    # return user
    
    raise HTTPException(401, "Invalid token")


async def get_optional_user(request: Request) -> Optional[Dict]:
    """
    FastAPI dependency for optionally authenticated routes
    
    Returns user if authenticated, None otherwise
    """
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


def require_tier(required_tier: str):
    """
    Dependency factory for tier-gated endpoints
    
    Usage:
        @app.get("/pro-feature")
        async def pro_feature(user = Depends(require_tier('pro'))):
            ...
    """
    async def dependency(user: Dict = Depends(get_current_user)):
        user_tier = user.get('tier', 'free')
        
        tier_hierarchy = {
            'free': 0,
            'pro': 1,
            'enterprise': 2
        }
        
        if tier_hierarchy.get(user_tier, 0) < tier_hierarchy.get(required_tier, 0):
            raise HTTPException(
                status_code=403,
                detail=f"This feature requires {required_tier} tier or higher"
            )
        
        return user
    
    return dependency


def require_team_access(team_id_param: str = 'team_id'):
    """
    Dependency factory for team-based access control
    
    Usage:
        @app.get("/teams/{team_id}/services")
        async def team_services(team_id: str, user = Depends(require_team_access())):
            ...
    """
    async def dependency(
        request: Request,
        user: Dict = Depends(get_current_user)
    ):
        team_id = request.path_params.get(team_id_param)
        user_teams = user.get('teams', [])
        
        # Admin can access any team
        if user.get('role') == 'admin':
            return user
        
        # Check team membership
        if team_id not in user_teams:
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this team"
            )
        
        return user
    
    return dependency


# Rate limit check with auth context
async def check_rate_limit(
    user: Dict,
    action: str,
    supabase_client
) -> bool:
    """
    Check rate limit for authenticated user
    
    Returns True if allowed, raises HTTPException if rate limited
    """
    from src.core.rate_limiter import RateLimiter
    
    rate_limiter = RateLimiter(supabase_client)
    
    allowed, info = await rate_limiter.check_rate_limit(
        user_id=user['id'],
        action=action,
        tier=user.get('tier', 'free')
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Try again in {info.get('retry_after', 60)} seconds"
        )
    
    return True
