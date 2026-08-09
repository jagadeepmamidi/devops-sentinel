"""
Alert Router - Severity-Based Intelligent Routing
=================================================

Routes incidents to the right people based on:
- Severity level (P0-P3)
- On-call schedule
- Service ownership
- Escalation policies
"""

from typing import List, Dict, Optional
from datetime import datetime
import asyncio


class AlertRouter:
    """
    Routes alerts based on severity, on-call, and escalation policies
    
    Routing Logic:
    - P0/P1: Page on-call immediately (Slack + PagerDuty + SMS)
    - P2: Slack notification only
    - P3: Log only, no immediate alert
    
    Escalation:
    - P0: Escalate to secondary after 5 minutes if not acknowledged
    - P1: Escalate after 15 minutes
    - P2/P3: No auto-escalation
    """
    
    def __init__(self, db_client=None):
        """
        Initialize alert router
       
        Args:
            db_client: Database client for on-call schedules
        """
        self.db = db_client
        self.escalation_rules = {
            'P0': {'timeout_minutes': 5, 'escalate': True},
            'P1': {'timeout_minutes': 15, 'escalate': True},
            'P2': {'timeout_minutes': 60, 'escalate': False},
            'P3': {'timeout_minutes': None, 'escalate': False}
        }
    
    async def route_incident(
        self,
        incident: Dict,
        immediate: bool = True
    ) -> Dict:
        """
        Route incident to appropriate responders
        
        Args:
            incident: Incident details dict
            immediate: Send immediately or queue
        
        Returns:
            Routing result with assigned users and channels
        """
        severity = incident.get('severity', 'P2')
        service_id = incident.get('service_id')
        service_name = incident.get('service_name', 'Unknown')
        
        # Get on-call person
        on_call = await self._get_on_call_user(severity, service_id)
        
        # Determine notification channels
        channels = self._get_notification_channels(severity)
        
        # Build routing result
        routing = {
            'incident_id': incident.get('id'),
            'severity': severity,
            'assigned_to': on_call['email'] if on_call else None,
            'assigned_name': on_call['name'] if on_call else None,
            'channels': channels,
            'escalation_policy': self.escalation_rules.get(severity),
            'routed_at': datetime.utcnow()
        }
        
        # Send notifications
        if immediate:
            await self._send_notifications(incident, routing)
        
        return routing
    
    async def escalate_incident(
        self,
        incident_id: str,
        current_assignee: str,
        reason: str = "No acknowledgment"
    ) -> Optional[Dict]:
        """
        Escalate incident to next person in rotation
        
        Args:
            incident_id: Incident UUID
            current_assignee: Current assigned user email
            reason: Escalation reason
        
        Returns:
            New routing with escalated assignee
        """
        # TODO: Fetch incident from DB
        incident = await self._fetch_incident(incident_id)
        
        if not incident:
            return None
        
        # Get next person in escalation chain
        next_on_call = await self._get_on_call_user(
            incident['severity'],
            incident['service_id'],
            priority=2  # Secondary on-call
        )
        
        if not next_on_call:
            # No one to escalate to
            return None
        
        # Create escalation routing
        routing = {
            'incident_id': incident_id,
            'assigned_to': next_on_call['email'],
            'assigned_name': next_on_call['name'],
            'escalated_from': current_assignee,
            'escalation_reason': reason,
            'escalated_at': datetime.utcnow()
        }
        
        # Send escalation notification
        await self._send_escalation_notification(incident, routing)
        
        return routing
    
    def _get_notification_channels(self, severity: str) -> List[str]:
        """
        Determine which channels to notify based on severity
        
        Args:
            severity: P0-P3
        
        Returns:
            List of channel names
        """
        if severity == 'P0':
            return ['slack', 'pagerduty', 'sms', 'email', 'discord']
        elif severity == 'P1':
            return ['slack', 'pagerduty', 'email']
        elif severity == 'P2':
            return ['slack', 'email']
        else:  # P3
            return ['slack']
    
    async def _get_on_call_user(
        self,
        severity: str,
        service_id: str,
        priority: int = 1
    ) -> Optional[Dict]:
        """
        Get current on-call user from database
        
        Args:
            severity: Incident severity
            service_id: Service UUID
            priority: 1=primary, 2=secondary, etc.
        
        Returns:
            User dict with email, name, slack_id
        """
        if not self.db:
            # Return mock data for testing
            return {
                'email': 'oncall@example.com',
                'name': 'On-Call Engineer',
                'slack_id': 'U123456',
                'priority': priority
            }
        
        # TODO: Query database using get_current_on_call function
        # SELECT * FROM get_current_on_call(severity, service_id)
        # WHERE priority = priority_param
        
        return None
    
    async def _send_notifications(
        self,
        incident: Dict,
        routing: Dict
    ):
        """
        Send notifications to all configured channels
        
        Args:
            incident: Incident details
            routing: Routing details
        """
        channels = routing['channels']
        
        # Send to each channel in parallel
        tasks = []
        
        if 'slack' in channels:
            tasks.append(self._send_slack_notification(incident, routing))
        
        if 'email' in channels:
            tasks.append(self._send_email_notification(incident, routing))
        
        if 'pagerduty' in channels:
            tasks.append(self._send_pagerduty_notification(incident, routing))
        
        if 'sms' in channels:
            tasks.append(self._send_sms_notification(incident, routing))
        
        if 'discord' in channels:
            tasks.append(self._send_discord_notification(incident, routing))
        
        # Execute all notifications concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_slack_notification(self, incident: Dict, routing: Dict):
        """Send Slack notification (placeholder)"""
        # TODO: Implement actual Slack integration
        print(f"📢 Slack: {routing['severity']} incident {incident.get('id')} → {routing['assigned_name']}")
    
    async def _send_email_notification(self, incident: Dict, routing: Dict):
        """Send email notification (placeholder)"""
        # TODO: Implement actual email sending
        print(f"📧 Email: {routing['severity']} incident → {routing['assigned_to']}")
    
    async def _send_pagerduty_notification(self, incident: Dict, routing: Dict):
        """Send PagerDuty page (placeholder)"""
        # TODO: Implement PagerDuty integration
        print(f"📟 PagerDuty: Paging {routing['assigned_name']}")
    
    async def _send_sms_notification(self, incident: Dict, routing: Dict):
        """Send SMS notification (placeholder)"""
        # TODO: Implement SMS (Twilio)
        print(f"📱 SMS: Alert sent")
    
    async def _send_discord_notification(self, incident: Dict, routing: Dict):
        """Send Discord notification (placeholder)"""
        # TODO: Implement Discord webhook
        print(f"💬 Discord: Alert sent")
    
    async def _send_escalation_notification(self, incident: Dict, routing: Dict):
        """Send escalation notification"""
        print(f"⚠️  ESCALATED: {incident.get('id')} → {routing['assigned_name']}")
        # TODO: Send to all channels with ESCALATION prefix
    
    async def _fetch_incident(self, incident_id: str) -> Optional[Dict]:
        """Fetch incident from database (placeholder)"""
        # TODO: Implement actual DB query
        return None
    
    def get_escalation_timeout(self, severity: str) -> Optional[int]:
        """
        Get escalation timeout in minutes for severity level
        
        Args:
            severity: P0-P3
        
        Returns:
            Minutes to wait before escalation, or None if no escalation
        """
        rule = self.escalation_rules.get(severity)
        return rule['timeout_minutes'] if rule else None
    
    def should_escalate(self, severity: str) -> bool:
        """Check if severity level has auto-escalation"""
        rule = self.escalation_rules.get(severity)
        return rule['escalate'] if rule else False


# Example usage
if __name__ == "__main__":
    async def test_alert_router():
        router = AlertRouter()
        
        # Test P0 incident routing
        incident = {
            'id': 'inc-123',
            'service_id': 'svc-456',
            'service_name': 'Auth API',
            'severity': 'P0',
            'error_message': 'Service completely down'
        }
        
        routing = await router.route_incident(incident)
        print(f"P0 Routing: {routing}")
        
        # Test escalation timeout
        timeout = router.get_escalation_timeout('P0')
        print(f"P0 escalation timeout: {timeout} minutes")
    
    asyncio.run(test_alert_router())
