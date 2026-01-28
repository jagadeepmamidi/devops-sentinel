"""
Slack Integration - Real-time Notifications & Commands
=======================================================

Slack webhooks, slash commands, and interactive messages
"""

import asyncio
import hashlib
import hmac
import time
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp


class SlackIntegration:
    """
    Slack integration for DevOps Sentinel
    
    Features:
    - Incident alerts with smart formatting
    - Interactive acknowledge/resolve buttons
    - /sentinel slash commands
    - Channel-based routing by severity
    """
    
    def __init__(
        self,
        webhook_url: str = None,
        bot_token: str = None,
        signing_secret: str = None
    ):
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.signing_secret = signing_secret
    
    async def send_incident_alert(
        self,
        incident: Dict,
        channel: Optional[str] = None,
        similar_incident: Optional[Dict] = None
    ) -> bool:
        """
        Send incident alert to Slack
        
        Args:
            incident: Incident data
            channel: Override channel (defaults to severity-based routing)
            similar_incident: Optional similar past incident
        
        Returns:
            True if sent successfully
        """
        severity = incident.get('severity', 'P2')
        
        # Route by severity
        if not channel:
            channel = self._get_channel_for_severity(severity)
        
        # Build message blocks
        blocks = self._build_incident_blocks(incident, similar_incident)
        
        payload = {
            'channel': channel,
            'text': f"[{severity}] {incident.get('title', 'Incident detected')}",
            'blocks': blocks,
            'unfurl_links': False
        }
        
        return await self._send_message(payload)
    
    async def send_resolution_notice(
        self,
        incident: Dict,
        resolved_by: str,
        duration_minutes: int
    ) -> bool:
        """Send incident resolved notification"""
        blocks = [
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': (
                        f"✅ *Resolved:* {incident.get('title', 'Incident')}\n"
                        f"*Service:* {incident.get('service_name', 'Unknown')}\n"
                        f"*Duration:* {duration_minutes} minutes\n"
                        f"*Resolved by:* {resolved_by}"
                    )
                }
            }
        ]
        
        payload = {
            'text': f"Incident resolved: {incident.get('title')}",
            'blocks': blocks
        }
        
        return await self._send_message(payload)
    
    async def send_daily_digest(
        self,
        summary: Dict,
        incidents: List[Dict]
    ) -> bool:
        """Send daily digest summary"""
        blocks = [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': f"📊 Daily Digest - {datetime.utcnow().strftime('%B %d, %Y')}"
                }
            },
            {
                'type': 'section',
                'fields': [
                    {
                        'type': 'mrkdwn',
                        'text': f"*Total Incidents:*\n{summary.get('total_incidents', 0)}"
                    },
                    {
                        'type': 'mrkdwn',
                        'text': f"*Resolved:*\n{summary.get('resolved', 0)}"
                    },
                    {
                        'type': 'mrkdwn',
                        'text': f"*Avg Resolution:*\n{summary.get('mttr_minutes', 0)}m"
                    },
                    {
                        'type': 'mrkdwn',
                        'text': f"*Uptime:*\n{summary.get('uptime_percent', 99.9):.1f}%"
                    }
                ]
            },
            {'type': 'divider'}
        ]
        
        # Add recent incidents
        if incidents:
            incident_text = "\n".join([
                f"• {inc.get('service_name')}: {inc.get('title', '')[:50]}"
                for inc in incidents[:5]
            ])
            
            blocks.append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f"*Recent Incidents:*\n{incident_text}"
                }
            })
        
        return await self._send_message({
            'text': 'Daily Digest',
            'blocks': blocks
        })
    
    async def handle_slash_command(
        self,
        command: str,
        text: str,
        user_id: str,
        channel_id: str
    ) -> Dict:
        """
        Handle /sentinel slash command
        
        Commands:
        - /sentinel status - Get system status
        - /sentinel ack <incident_id> - Acknowledge incident
        - /sentinel resolve <incident_id> - Resolve incident
        - /sentinel oncall - Who's on call
        """
        parts = text.strip().split()
        action = parts[0] if parts else 'help'
        args = parts[1:] if len(parts) > 1 else []
        
        if action == 'status':
            return await self._handle_status_command()
        elif action == 'ack' and args:
            return await self._handle_ack_command(args[0], user_id)
        elif action == 'resolve' and args:
            return await self._handle_resolve_command(args[0], user_id)
        elif action == 'oncall':
            return await self._handle_oncall_command()
        else:
            return self._get_help_response()
    
    async def handle_interaction(
        self,
        payload: Dict
    ) -> Dict:
        """
        Handle interactive button clicks
        
        Actions:
        - acknowledge_incident
        - resolve_incident
        - view_postmortem
        """
        action_id = payload.get('actions', [{}])[0].get('action_id', '')
        user = payload.get('user', {})
        
        if action_id.startswith('ack_'):
            incident_id = action_id.replace('ack_', '')
            return await self._acknowledge_incident(incident_id, user.get('id'))
        
        elif action_id.startswith('resolve_'):
            incident_id = action_id.replace('resolve_', '')
            return await self._resolve_incident(incident_id, user.get('id'))
        
        return {'text': 'Unknown action'}
    
    def verify_request(
        self,
        signature: str,
        timestamp: str,
        body: bytes
    ) -> bool:
        """Verify request is from Slack"""
        if not self.signing_secret:
            return True  # Skip verification in dev
        
        # Check timestamp (reject if > 5 minutes old)
        if abs(time.time() - float(timestamp)) > 300:
            return False
        
        # Compute signature
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        my_signature = 'v0=' + hmac.new(
            self.signing_secret.encode(),
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(my_signature, signature)
    
    # Private methods
    
    async def _send_message(self, payload: Dict) -> bool:
        """Send message to Slack"""
        if not self.webhook_url:
            print(f"[Slack] Would send: {payload.get('text', '')[:100]}")
            return True
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            print(f"[Slack] Error sending message: {e}")
            return False
    
    def _get_channel_for_severity(self, severity: str) -> str:
        """Get channel based on severity"""
        channels = {
            'P0': '#incidents-critical',
            'P1': '#incidents-high',
            'P2': '#incidents',
            'P3': '#incidents'
        }
        return channels.get(severity, '#incidents')
    
    def _build_incident_blocks(
        self,
        incident: Dict,
        similar: Optional[Dict] = None
    ) -> List[Dict]:
        """Build incident message blocks"""
        severity = incident.get('severity', 'P2')
        emoji = {'P0': '🔴', 'P1': '🟠', 'P2': '🟡', 'P3': '🔵'}.get(severity, '⚪')
        
        blocks = [
            {
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': f"{emoji} [{severity}] {incident.get('title', 'Incident')}"
                }
            },
            {
                'type': 'section',
                'fields': [
                    {
                        'type': 'mrkdwn',
                        'text': f"*Service:*\n{incident.get('service_name', 'Unknown')}"
                    },
                    {
                        'type': 'mrkdwn',
                        'text': f"*Detected:*\n<!date^{int(datetime.utcnow().timestamp())}^{{time}}|now>"
                    }
                ]
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f"*Description:*\n{incident.get('description', 'No description')[:500]}"
                }
            }
        ]
        
        # Add similar incident if found
        if similar:
            blocks.append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': (
                        f"💡 *Similar incident found:* #{similar.get('id', 'N/A')}\n"
                        f"_Resolution: {similar.get('resolution', 'N/A')[:200]}_"
                    )
                }
            })
        
        # Add action buttons
        incident_id = incident.get('id', '')
        blocks.append({
            'type': 'actions',
            'elements': [
                {
                    'type': 'button',
                    'text': {'type': 'plain_text', 'text': '✓ Acknowledge'},
                    'style': 'primary',
                    'action_id': f'ack_{incident_id}'
                },
                {
                    'type': 'button',
                    'text': {'type': 'plain_text', 'text': '✓ Resolve'},
                    'style': 'danger',
                    'action_id': f'resolve_{incident_id}'
                },
                {
                    'type': 'button',
                    'text': {'type': 'plain_text', 'text': 'View Details'},
                    'url': f"https://app.sentinel.dev/incidents/{incident_id}"
                }
            ]
        })
        
        return blocks
    
    async def _handle_status_command(self) -> Dict:
        """Handle /sentinel status"""
        # Would fetch real status
        return {
            'response_type': 'in_channel',
            'text': (
                "📊 *System Status*\n"
                "• Services: 12 monitored\n"
                "• Active Incidents: 0\n"
                "• Uptime (24h): 99.9%"
            )
        }
    
    async def _handle_ack_command(self, incident_id: str, user_id: str) -> Dict:
        """Handle /sentinel ack"""
        return {
            'response_type': 'in_channel',
            'text': f"✓ <@{user_id}> acknowledged incident {incident_id}"
        }
    
    async def _handle_resolve_command(self, incident_id: str, user_id: str) -> Dict:
        """Handle /sentinel resolve"""
        return {
            'response_type': 'in_channel',
            'text': f"✅ <@{user_id}> resolved incident {incident_id}"
        }
    
    async def _handle_oncall_command(self) -> Dict:
        """Handle /sentinel oncall"""
        return {
            'response_type': 'ephemeral',
            'text': "👤 *Currently On-Call:* @alice (until Monday 9am)"
        }
    
    def _get_help_response(self) -> Dict:
        """Return help text"""
        return {
            'response_type': 'ephemeral',
            'text': (
                "*DevOps Sentinel Commands:*\n"
                "• `/sentinel status` - System status\n"
                "• `/sentinel ack <id>` - Acknowledge incident\n"
                "• `/sentinel resolve <id>` - Resolve incident\n"
                "• `/sentinel oncall` - Who's on call"
            )
        }
    
    async def _acknowledge_incident(self, incident_id: str, user_id: str) -> Dict:
        """Handle acknowledge button click"""
        return {
            'text': f"✓ <@{user_id}> acknowledged",
            'replace_original': False
        }
    
    async def _resolve_incident(self, incident_id: str, user_id: str) -> Dict:
        """Handle resolve button click"""
        return {
            'text': f"✅ <@{user_id}> resolved",
            'replace_original': False
        }


# FastAPI routes
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/integrations/slack", tags=["slack"])


@router.post("/webhook")
async def slack_events(request: Request):
    """Handle Slack Events API"""
    body = await request.json()
    
    # Handle URL verification
    if body.get('type') == 'url_verification':
        return {'challenge': body.get('challenge')}
    
    # Handle events
    event = body.get('event', {})
    event_type = event.get('type')
    
    # Process event (would dispatch to handlers)
    
    return {'ok': True}


@router.post("/commands")
async def slack_commands(request: Request):
    """Handle slash commands"""
    form = await request.form()
    
    slack = SlackIntegration()
    return await slack.handle_slash_command(
        command=form.get('command', ''),
        text=form.get('text', ''),
        user_id=form.get('user_id', ''),
        channel_id=form.get('channel_id', '')
    )


@router.post("/interactions")
async def slack_interactions(request: Request):
    """Handle interactive components"""
    form = await request.form()
    import json
    payload = json.loads(form.get('payload', '{}'))
    
    slack = SlackIntegration()
    return await slack.handle_interaction(payload)
