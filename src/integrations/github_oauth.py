"""
GitHub OAuth - One-Click Repo Monitoring
=========================================

"Connect GitHub" flow for deployment tracking
"""

import os
import secrets
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import urlencode

import aiohttp
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse

from src.auth.auth_service import get_current_user


# OAuth Configuration
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', '')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', '')
APP_URL = os.environ.get('APP_URL', 'http://localhost:8000')

# Scopes for repo access
GITHUB_SCOPES = [
    'repo:status',
    'repo_deployment',
    'read:org',
    'read:user'
]


class GitHubOAuth:
    """
    GitHub OAuth 2.0 Flow
    
    Enables:
    - Deployment tracking
    - Commit correlation with incidents
    - Repository health monitoring
    """
    
    AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    USER_URL = "https://api.github.com/user"
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self._state_store = {}
    
    def get_authorization_url(self, user_id: str) -> str:
        """Generate GitHub authorization URL"""
        state = secrets.token_urlsafe(32)
        self._state_store[state] = {'user_id': user_id}
        
        params = {
            'client_id': GITHUB_CLIENT_ID,
            'scope': ' '.join(GITHUB_SCOPES),
            'redirect_uri': f"{APP_URL}/api/github/oauth/callback",
            'state': state
        }
        
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"
    
    async def handle_callback(self, code: str, state: str) -> Dict:
        """Handle OAuth callback"""
        state_data = self._state_store.pop(state, None)
        if not state_data:
            raise HTTPException(400, "Invalid state")
        
        # Exchange code for token
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.TOKEN_URL,
                headers={'Accept': 'application/json'},
                data={
                    'client_id': GITHUB_CLIENT_ID,
                    'client_secret': GITHUB_CLIENT_SECRET,
                    'code': code
                }
            ) as resp:
                tokens = await resp.json()
        
        if 'error' in tokens:
            raise HTTPException(400, tokens.get('error_description', 'OAuth failed'))
        
        # Get user info
        async with aiohttp.ClientSession() as session:
            async with session.get(
                self.USER_URL,
                headers={
                    'Authorization': f"Bearer {tokens['access_token']}",
                    'Accept': 'application/vnd.github.v3+json'
                }
            ) as resp:
                github_user = await resp.json()
        
        # Store integration
        integration = {
            'user_id': state_data['user_id'],
            'github_user_id': github_user['id'],
            'github_username': github_user['login'],
            'access_token': tokens['access_token'],
            'scope': tokens.get('scope', ''),
            'installed_at': datetime.utcnow().isoformat()
        }
        
        if self.supabase:
            self.supabase.table('github_integrations').upsert(
                integration,
                on_conflict='user_id'
            ).execute()
        
        return {
            'username': github_user['login'],
            'avatar': github_user.get('avatar_url'),
            'success': True
        }


# FastAPI Router
router = APIRouter(prefix="/api/github/oauth", tags=["github-oauth"])


@router.get("/start")
async def start_oauth(user: Dict = Depends(get_current_user)):
    """Start GitHub OAuth flow"""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(500, "GitHub OAuth not configured")
    
    oauth = GitHubOAuth()
    return {"authorization_url": oauth.get_authorization_url(user['id'])}


@router.get("/callback")
async def oauth_callback(code: str = None, state: str = None, error: str = None):
    """Handle GitHub OAuth callback"""
    if error:
        return RedirectResponse(f"{APP_URL}/settings/integrations?error={error}")
    
    try:
        oauth = GitHubOAuth()
        result = await oauth.handle_callback(code, state)
        return RedirectResponse(
            f"{APP_URL}/settings/integrations?github=connected&user={result['username']}"
        )
    except HTTPException as e:
        return RedirectResponse(f"{APP_URL}/settings/integrations?error={e.detail}")


@router.get("/button")
async def get_button():
    """Get Connect GitHub button HTML"""
    return {
        "html": f'''
        <a href="{APP_URL}/api/github/oauth/start"
           style="display:inline-flex;align-items:center;padding:12px 24px;
                  background:#24292e;color:white;border-radius:8px;
                  font-family:system-ui;font-weight:600;text-decoration:none;">
            <svg style="width:20px;height:20px;margin-right:8px" viewBox="0 0 24 24">
                <path fill="currentColor" d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            Connect GitHub
        </a>
        '''
    }
