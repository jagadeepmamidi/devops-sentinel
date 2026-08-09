"""
Slack Integration - Collaborative Incident Management
======================================================

Manage incidents through Slack threads with rich formatting
"""

import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import json


class SlackIntegration:
    """
    Slack integration for incident management
    
    Features:
    - Create incident threads
    - Post updates to threads
    - Rich message formatting
    - Interactive buttons (Acknowledge, Resolve)
    - Thread-based collaboration
    - Status updates
    """
    
    def __init__(self, webhook_url: str, bot_token: Optional[str] = None):
        """
        Initialize Slack integration
        
        Args:
            webhook_url: Slack incoming webhook URL
            bot_token: Optional bot token for advanced features (threading, reactions)
        """
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.api_base = "https://slack.com/api"
    
    async def post_incident_alert(
        self,
        incident: Dict,
        channel: str = None
    ) -> Dict:
        """
        Post incident alert to Slack
        
        Args:
            incident: Incident details
            channel: Optional channel override
        
        Returns:
            Slack response with thread_ts
        """
        severity = incident.get('severity', 'P3')
        service_name = incident.get('service_name', 'Unknown Service')
        status = incident.get('status', 'open')
        details = incident.get('details', 'No details provided')
        
        # Emoji and color based on severity
        severity_config = {
            'P0': {'emoji': '🚨', 'color': '#FF0000', 'text': 'CRITICAL'},
            'P1': {'emoji': '⚠️', 'color': '#FFA500', 'text': 'HIGH'},
            'P2': {'emoji': '⚡', 'color': '#FFD700', 'text': 'MEDIUM'},
            'P3': {'emoji': 'ℹ️', 'color': '#4A90E2', 'text': 'LOW'}
        }
        
        config = severity_config.get(severity, severity_config['P3'])
        
        # Build rich message
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{config['emoji']} {config['text']} Incident Detected",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Service:*\n{service_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:*\n{severity}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:*\n{status.upper()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Incident ID:*\n`{incident.get('id', 'N/A')}`"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Details:*\n{details}"
                    }
                },
                {
                    "type": "divider"
                }
            ],
            "attachments": [
                {
                    "color": config['color'],
                    "blocks": [
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "👀 Acknowledge"
                                    },
                                    "value": f"ack_{incident.get('id')}",
                                    "action_id": "acknowledge_incident",
                                    "style": "primary"
                                },
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "✅ Resolve"
                                    },
                                    "value": f"resolve_{incident.get('id')}",
                                    "action_id": "resolve_incident",
                                    "style": "primary"
                                },
                                {
                                    "type": "button",
                                    "text": {
                                        "type": "plain_text",
                                        "text": "🔍 View Details"
                                    },
                                    "url": f"https://devops-sentinel.dev/incidents/{incident.get('id')}",
                                    "action_id": "view_incident"
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # Add AI postmortem if available
        if incident.get('ai_postmortem'):
            message['blocks'].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*AI Analysis:*\n```{incident['ai_postmortem'][:500]}```"
                }
            })
        
        # Send to Slack
        response = await self._send_message(message, channel)
        
        return response
    
    async def post_thread_update(
        self,
        thread_ts: str,
        message: str,
        channel: str = None
    ) -> Dict:
        """
        Post update to existing incident thread
        
        Args:
            thread_ts: Thread timestamp from original message
            message: Update message
            channel: Channel ID
        """
        if not self.bot_token:
            # Fallback to webhook (can't thread without bot token)
            return await self._send_message({"text": message}, channel)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base}/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.bot_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "channel": channel,
                    "text": message,
                    "thread_ts": thread_ts
                }
            ) as response:
                return await response.json()
    
    async def post_resolution_summary(
        self,
        incident: Dict,
        thread_ts: str,
        channel: str = None
    ) -> Dict:
        """
        Post incident resolution summary to thread
        
        Args:
            incident: Resolved incident details
            thread_ts: Original incident thread
            channel: Channel ID
        """
        duration = incident.get('duration_minutes', 'Unknown')
        resolved_by = incident.get('resolved_by', 'System')
        resolution_steps = incident.get('resolution_steps', [])
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "✅ Incident Resolved",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Duration:*\n{duration} minutes"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Resolved By:*\n{resolved_by}"
                        }
                    ]
                }
            ]
        }
        
        # Add resolution steps if available
        if resolution_steps:
            steps_text = "\n".join([f"• {step}" for step in resolution_steps])
            message['blocks'].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Resolution Steps:*\n{steps_text}"
                }
            })
        
        return await self.post_thread_update(thread_ts, json.dumps(message), channel)
    
    async def post_escalation_alert(
        self,
        incident: Dict,
        escalated_to: str,
        level: int,
        thread_ts: str,
        channel: str = None
    ) -> Dict:
        """
        Post escalation notification
        
        Args:
            incident: Incident being escalated
            escalated_to: User being escalated to
            level: Escalation level
            thread_ts: Original thread
            channel: Channel ID
        """
        message = f"⬆️ *Incident Escalated to Level {level}*\n" \
                  f"Alerting: <@{escalated_to}>\n" \
                  f"Reason: No acknowledgment after timeout"
        
        return await self.post_thread_update(thread_ts, message, channel)
    
    async def post_deployment_alert(
        self,
        deployment: Dict,
        health: Dict,
        channel: str = None
    ) -> Dict:
        """
        Post deployment health alert
        
        Args:
            deployment: Deployment details
            health: Health check results
            channel: Channel ID
        """
        status = health.get('status', 'unknown')
        recommendation = health.get('recommendation', 'No action needed')
        
        status_config = {
            'healthy': {'emoji': '✅', 'color': '#00FF00'},
            'warning': {'emoji': '⚠️', 'color': '#FFD700'},
            'degraded': {'emoji': '⚡', 'color': '#FFA500'},
            'unhealthy': {'emoji': '🚨', 'color': '#FF0000'}
        }
        
        config = status_config.get(status, {'emoji': 'ℹ️', 'color': '#4A90E2'})
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{config['emoji']} Deployment Health Alert",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Version:*\n{deployment.get('version')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:*\n{status.upper()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Incidents:*\n{health.get('incident_count', 0)}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Risk Score:*\n{health.get('risk_score', 0):.2f}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Recommendation:*\n{recommendation}"
                    }
                }
            ],
            "attachments": [{
                "color": config['color']
            }]
        }
        
        return await self._send_message(message, channel)
    
    async def _send_message(
        self,
        message: Dict,
        channel: Optional[str] = None
    ) -> Dict:
        """
        Send message to Slack via webhook or API
        
        Args:
            message: Message payload
            channel: Optional channel override
        """
        if channel:
            message['channel'] = channel
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.webhook_url,
                json=message,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return {
                        'success': True,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'error': await response.text()
                    }
    
    def format_code_block(self, code: str, language: str = '') -> str:
        """Format code for Slack markdown"""
        return f"```{language}\n{code}\n```"
    
    def format_user_mention(self, user_id: str) -> str:
        """Format user mention"""
        return f"<@{user_id}>"
    
    def format_channel_mention(self, channel_id: str) -> str:
        """Format channel mention"""
        return f"<#{channel_id}>"


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_slack():
        # Initialize with webhook URL
        slack = SlackIntegration(
            webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
        )
        
        # Test incident alert
        incident = {
            'id': 'inc-123',
            'severity': 'P1',
            'service_name': 'API Gateway',
            'status': 'open',
            'details': 'Service response time >5s for 3 consecutive checks',
            'ai_postmortem': 'High CPU usage detected. Recommend scaling horizontally.'
        }
        
        response = await slack.post_incident_alert(incident)
        print(f"Slack response: {response}")
    
    # asyncio.run(test_slack())
    print("Slack integration ready. Configure SLACK_WEBHOOK_URL to test.")
