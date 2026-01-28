"""
PagerDuty OAuth - One-Click On-Call Integration
================================================

"Connect PagerDuty" flow for on-call management
"""

import os
import secrets
from datetime import datetime
from typing import Dict
from urllib.parse import urlencode

import aiohttp
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse

from src.auth.auth_service import get_current_user


# OAuth Configuration
PAGERDUTY_CLIENT_ID = os.environ.get('PAGERDUTY_CLIENT_ID', '')
PAGERDUTY_CLIENT_SECRET = os.environ.get('PAGERDUTY_CLIENT_SECRET', '')
APP_URL = os.environ.get('APP_URL', 'http://localhost:8000')


class PagerDutyOAuth:
    """
    PagerDuty OAuth 2.0 Flow
    
    Enables:
    - On-call schedule sync
    - Incident escalation
    - Team member sync
    """
    
    AUTHORIZE_URL = "https://identity.pagerduty.com/oauth/authorize"
    TOKEN_URL = "https://identity.pagerduty.com/oauth/token"
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self._state_store = {}
    
    def get_authorization_url(self, user_id: str) -> str:
        """Generate PagerDuty authorization URL"""
        state = secrets.token_urlsafe(32)
        self._state_store[state] = {'user_id': user_id}
        
        params = {
            'client_id': PAGERDUTY_CLIENT_ID,
            'redirect_uri': f"{APP_URL}/api/pagerduty/oauth/callback",
            'response_type': 'code',
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
                data={
                    'grant_type': 'authorization_code',
                    'client_id': PAGERDUTY_CLIENT_ID,
                    'client_secret': PAGERDUTY_CLIENT_SECRET,
                    'redirect_uri': f"{APP_URL}/api/pagerduty/oauth/callback",
                    'code': code
                }
            ) as resp:
                tokens = await resp.json()
        
        if 'error' in tokens:
            raise HTTPException(400, tokens.get('error_description', 'OAuth failed'))
        
        # Get current user
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.pagerduty.com/users/me",
                headers={
                    'Authorization': f"Bearer {tokens['access_token']}",
                    'Content-Type': 'application/json'
                }
            ) as resp:
                pd_data = await resp.json()
        
        pd_user = pd_data.get('user', {})
        
        # Store integration
        integration = {
            'user_id': state_data['user_id'],
            'pagerduty_user_id': pd_user.get('id'),
            'pagerduty_email': pd_user.get('email'),
            'access_token': tokens['access_token'],
            'refresh_token': tokens.get('refresh_token'),
            'installed_at': datetime.utcnow().isoformat()
        }
        
        if self.supabase:
            self.supabase.table('pagerduty_integrations').upsert(
                integration,
                on_conflict='user_id'
            ).execute()
        
        return {
            'email': pd_user.get('email'),
            'name': pd_user.get('name'),
            'success': True
        }


# FastAPI Router
router = APIRouter(prefix="/api/pagerduty/oauth", tags=["pagerduty-oauth"])


@router.get("/start")
async def start_oauth(user: Dict = Depends(get_current_user)):
    """Start PagerDuty OAuth flow"""
    if not PAGERDUTY_CLIENT_ID:
        raise HTTPException(500, "PagerDuty OAuth not configured")
    
    oauth = PagerDutyOAuth()
    return {"authorization_url": oauth.get_authorization_url(user['id'])}


@router.get("/callback")
async def oauth_callback(code: str = None, state: str = None, error: str = None):
    """Handle PagerDuty OAuth callback"""
    if error:
        return RedirectResponse(f"{APP_URL}/settings/integrations?error={error}")
    
    try:
        oauth = PagerDutyOAuth()
        result = await oauth.handle_callback(code, state)
        return RedirectResponse(
            f"{APP_URL}/settings/integrations?pagerduty=connected"
        )
    except HTTPException as e:
        return RedirectResponse(f"{APP_URL}/settings/integrations?error={e.detail}")


@router.get("/button")
async def get_button():
    """Get Connect PagerDuty button HTML"""
    return {
        "html": f'''
        <a href="{APP_URL}/api/pagerduty/oauth/start"
           style="display:inline-flex;align-items:center;padding:12px 24px;
                  background:#06AC38;color:white;border-radius:8px;
                  font-family:system-ui;font-weight:600;text-decoration:none;">
            <svg style="width:20px;height:20px;margin-right:8px" viewBox="0 0 24 24">
                <path fill="currentColor" d="M16.965 1.18C15.085.164 13.769 0 10.683 0H3.73v14.55h6.926c2.743 0 4.8-.164 6.639-1.312 1.884-1.148 2.942-3.098 2.942-5.539 0-2.687-1.312-5.376-3.272-6.518zm-5.558 9.832H8.06V4.088h3.347c2.578 0 4.043 1.207 4.043 3.43 0 2.332-1.555 3.494-4.043 3.494zM3.73 24h4.33v-6.369H3.73z"/>
            </svg>
            Connect PagerDuty
        </a>
        '''
    }
