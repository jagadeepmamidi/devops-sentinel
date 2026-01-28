"""
Slack OAuth - One-Click Integration
====================================

"Add to Slack" button flow:
1. User clicks button → redirects to Slack
2. User approves permissions → Slack redirects back
3. We exchange code for tokens → Store in database
4. Done! No manual copying needed.
"""

import os
import secrets
from datetime import datetime
from typing import Dict, Optional
from urllib.parse import urlencode

import aiohttp
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import RedirectResponse

from src.auth.auth_service import get_current_user, get_optional_user


# OAuth Configuration
SLACK_CLIENT_ID = os.environ.get('SLACK_CLIENT_ID', '')
SLACK_CLIENT_SECRET = os.environ.get('SLACK_CLIENT_SECRET', '')
SLACK_SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET', '')
APP_URL = os.environ.get('APP_URL', 'http://localhost:8000')

# Scopes for bot and webhooks
SLACK_SCOPES = [
    'channels:read',
    'chat:write',
    'commands',
    'incoming-webhook',
    'users:read',
    'team:read'
]


class SlackOAuth:
    """
    Slack OAuth 2.0 Flow
    
    Handles the complete "Add to Slack" flow:
    1. Generate authorization URL
    2. Handle callback with code
    3. Exchange code for tokens
    4. Store tokens for user
    """
    
    AUTHORIZE_URL = "https://slack.com/oauth/v2/authorize"
    TOKEN_URL = "https://slack.com/api/oauth.v2.access"
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self._state_store = {}  # In production, use Redis
    
    def get_authorization_url(self, user_id: str, redirect_uri: str = None) -> str:
        """
        Generate Slack authorization URL
        
        Args:
            user_id: Our user ID to associate with Slack workspace
            redirect_uri: Callback URL after authorization
        
        Returns:
            URL to redirect user to Slack
        """
        # Generate state token to prevent CSRF
        state = secrets.token_urlsafe(32)
        self._state_store[state] = {
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat()
        }
        
        redirect_uri = redirect_uri or f"{APP_URL}/api/slack/oauth/callback"
        
        params = {
            'client_id': SLACK_CLIENT_ID,
            'scope': ','.join(SLACK_SCOPES),
            'redirect_uri': redirect_uri,
            'state': state
        }
        
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"
    
    async def handle_callback(
        self,
        code: str,
        state: str,
        redirect_uri: str = None
    ) -> Dict:
        """
        Handle OAuth callback from Slack
        
        Args:
            code: Authorization code from Slack
            state: State token to verify
            redirect_uri: Same redirect URI used in authorization
        
        Returns:
            Workspace info and success status
        """
        # Verify state
        state_data = self._state_store.pop(state, None)
        if not state_data:
            raise HTTPException(400, "Invalid or expired state token")
        
        user_id = state_data['user_id']
        redirect_uri = redirect_uri or f"{APP_URL}/api/slack/oauth/callback"
        
        # Exchange code for tokens
        tokens = await self._exchange_code(code, redirect_uri)
        
        if not tokens.get('ok'):
            raise HTTPException(400, f"Slack error: {tokens.get('error', 'Unknown')}")
        
        # Extract and store tokens
        workspace = await self._store_tokens(user_id, tokens)
        
        return workspace
    
    async def _exchange_code(self, code: str, redirect_uri: str) -> Dict:
        """Exchange authorization code for access tokens"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.TOKEN_URL,
                data={
                    'client_id': SLACK_CLIENT_ID,
                    'client_secret': SLACK_CLIENT_SECRET,
                    'code': code,
                    'redirect_uri': redirect_uri
                }
            ) as resp:
                return await resp.json()
    
    async def _store_tokens(self, user_id: str, tokens: Dict) -> Dict:
        """Store Slack tokens in database"""
        workspace_info = {
            'user_id': user_id,
            'team_id': tokens.get('team', {}).get('id'),
            'team_name': tokens.get('team', {}).get('name'),
            'bot_token': tokens.get('access_token'),
            'bot_user_id': tokens.get('bot_user_id'),
            'webhook_url': tokens.get('incoming_webhook', {}).get('url'),
            'webhook_channel': tokens.get('incoming_webhook', {}).get('channel'),
            'webhook_channel_id': tokens.get('incoming_webhook', {}).get('channel_id'),
            'scope': tokens.get('scope'),
            'installed_at': datetime.utcnow().isoformat()
        }
        
        if self.supabase:
            # Upsert to database
            self.supabase.table('slack_integrations').upsert(
                workspace_info,
                on_conflict='user_id,team_id'
            ).execute()
        
        return {
            'team_id': workspace_info['team_id'],
            'team_name': workspace_info['team_name'],
            'channel': workspace_info['webhook_channel'],
            'success': True
        }
    
    async def get_user_integrations(self, user_id: str) -> list:
        """Get all Slack integrations for a user"""
        if not self.supabase:
            return []
        
        result = self.supabase.table('slack_integrations').select(
            'team_id, team_name, webhook_channel, installed_at'
        ).eq('user_id', user_id).execute()
        
        return result.data if result.data else []
    
    async def remove_integration(self, user_id: str, team_id: str) -> bool:
        """Remove a Slack integration"""
        if not self.supabase:
            return True
        
        self.supabase.table('slack_integrations').delete().eq(
            'user_id', user_id
        ).eq('team_id', team_id).execute()
        
        return True


# FastAPI Router
router = APIRouter(prefix="/api/slack/oauth", tags=["slack-oauth"])


@router.get("/start")
async def start_oauth(
    user: Dict = Depends(get_current_user)
):
    """
    Start Slack OAuth flow
    
    Returns URL to redirect user to Slack authorization
    """
    if not SLACK_CLIENT_ID:
        raise HTTPException(500, "Slack OAuth not configured")
    
    oauth = SlackOAuth()
    auth_url = oauth.get_authorization_url(user['id'])
    
    return {"authorization_url": auth_url}


@router.get("/callback")
async def oauth_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None
):
    """
    Handle OAuth callback from Slack
    
    Slack redirects here after user authorizes
    """
    # Handle errors
    if error:
        return RedirectResponse(
            f"{APP_URL}/settings/integrations?error={error}"
        )
    
    if not code or not state:
        return RedirectResponse(
            f"{APP_URL}/settings/integrations?error=missing_params"
        )
    
    try:
        oauth = SlackOAuth()
        result = await oauth.handle_callback(code, state)
        
        # Redirect to success page
        return RedirectResponse(
            f"{APP_URL}/settings/integrations?success=true&team={result['team_name']}"
        )
        
    except HTTPException as e:
        return RedirectResponse(
            f"{APP_URL}/settings/integrations?error={e.detail}"
        )


@router.get("/integrations")
async def list_integrations(
    user: Dict = Depends(get_current_user)
):
    """List user's Slack integrations"""
    oauth = SlackOAuth()
    integrations = await oauth.get_user_integrations(user['id'])
    return {"integrations": integrations}


@router.delete("/integrations/{team_id}")
async def remove_integration(
    team_id: str,
    user: Dict = Depends(get_current_user)
):
    """Remove a Slack integration"""
    oauth = SlackOAuth()
    await oauth.remove_integration(user['id'], team_id)
    return {"status": "removed"}


@router.get("/button")
async def get_add_to_slack_button():
    """
    Get "Add to Slack" button HTML
    
    Can be embedded in any page
    """
    if not SLACK_CLIENT_ID:
        return {"html": "<p>Slack integration not configured</p>"}
    
    button_html = f'''
    <a href="{APP_URL}/api/slack/oauth/start" 
       style="display:inline-flex;align-items:center;padding:12px 24px;
              background:#4A154B;color:white;border-radius:8px;
              font-family:system-ui;font-weight:600;text-decoration:none;
              box-shadow:0 2px 4px rgba(0,0,0,0.2);">
        <svg style="width:20px;height:20px;margin-right:8px" viewBox="0 0 24 24">
            <path fill="currentColor" d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z"/>
        </svg>
        Add to Slack
    </a>
    '''
    
    return {"html": button_html}
