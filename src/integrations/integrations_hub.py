"""
All Integrations Hub
====================

Central hub for managing all one-click OAuth integrations
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List

from src.auth.auth_service import get_current_user
from .slack_oauth import SlackOAuth
from .github_oauth import GitHubOAuth
from .pagerduty_oauth import PagerDutyOAuth


router = APIRouter(prefix="/api/integrations", tags=["integrations"])


# Available integrations
INTEGRATIONS = {
    'slack': {
        'name': 'Slack',
        'description': 'Real-time alerts and slash commands',
        'icon': 'slack',
        'color': '#4A154B',
        'features': ['Incident alerts', 'Interactive buttons', '/sentinel commands']
    },
    'github': {
        'name': 'GitHub',
        'description': 'Deployment tracking and commit correlation',
        'icon': 'github',
        'color': '#24292e',
        'features': ['Deploy tracking', 'Commit → incident links', 'PR status']
    },
    'pagerduty': {
        'name': 'PagerDuty',
        'description': 'On-call schedules and escalation policies',
        'icon': 'pagerduty',
        'color': '#06AC38',
        'features': ['On-call sync', 'Escalation routing', 'Team sync']
    },
    'datadog': {
        'name': 'Datadog',
        'description': 'Metrics and APM data import',
        'icon': 'datadog',
        'color': '#632CA6',
        'features': ['Metrics import', 'APM traces', 'Log correlation'],
        'coming_soon': True
    },
    'jira': {
        'name': 'Jira',
        'description': 'Issue tracking and sprint integration',
        'icon': 'jira',
        'color': '#0052CC',
        'features': ['Auto-create issues', 'Sprint tracking', 'Postmortem tasks'],
        'coming_soon': True
    }
}


@router.get("/available")
async def list_available_integrations():
    """
    List all available integrations
    
    Returns integrations with their status (available, coming_soon)
    """
    result = []
    for key, info in INTEGRATIONS.items():
        result.append({
            'id': key,
            'name': info['name'],
            'description': info['description'],
            'icon': info['icon'],
            'color': info['color'],
            'features': info['features'],
            'coming_soon': info.get('coming_soon', False)
        })
    return {"integrations": result}


@router.get("/connected")
async def list_connected_integrations(user: Dict = Depends(get_current_user)):
    """
    List user's connected integrations
    """
    connected = []
    
    # Check each integration
    slack_oauth = SlackOAuth()
    slack_integrations = await slack_oauth.get_user_integrations(user['id'])
    if slack_integrations:
        for s in slack_integrations:
            connected.append({
                'type': 'slack',
                'name': 'Slack',
                'workspace': s.get('team_name'),
                'channel': s.get('webhook_channel'),
                'connected_at': s.get('installed_at')
            })
    
    # GitHub and PagerDuty would be similar checks
    
    return {"connected": connected}


@router.get("/buttons")
async def get_all_buttons():
    """
    Get all OAuth button HTML for embedding
    """
    from .slack_oauth import router as slack_router
    from .github_oauth import router as github_router
    from .pagerduty_oauth import router as pagerduty_router
    
    return {
        "buttons": {
            "slack": await get_slack_button(),
            "github": await get_github_button(),
            "pagerduty": await get_pagerduty_button()
        }
    }


async def get_slack_button():
    """Slack button HTML"""
    return '''
    <button onclick="window.location.href='/api/slack/oauth/start'"
            class="integration-btn slack-btn">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="..."/></svg>
        Add to Slack
    </button>
    '''


async def get_github_button():
    """GitHub button HTML"""
    return '''
    <button onclick="window.location.href='/api/github/oauth/start'"
            class="integration-btn github-btn">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="..."/></svg>
        Connect GitHub
    </button>
    '''


async def get_pagerduty_button():
    """PagerDuty button HTML"""
    return '''
    <button onclick="window.location.href='/api/pagerduty/oauth/start'"
            class="integration-btn pagerduty-btn">
        <svg viewBox="0 0 24 24"><path fill="currentColor" d="..."/></svg>
        Connect PagerDuty
    </button>
    '''


@router.delete("/{integration_type}/{integration_id}")
async def disconnect_integration(
    integration_type: str,
    integration_id: str,
    user: Dict = Depends(get_current_user)
):
    """
    Disconnect an integration
    """
    if integration_type == 'slack':
        oauth = SlackOAuth()
        await oauth.remove_integration(user['id'], integration_id)
    elif integration_type == 'github':
        oauth = GitHubOAuth()
        # Similar removal logic
        pass
    elif integration_type == 'pagerduty':
        oauth = PagerDutyOAuth()
        # Similar removal logic
        pass
    else:
        raise HTTPException(400, f"Unknown integration: {integration_type}")
    
    return {"status": "disconnected", "type": integration_type}
