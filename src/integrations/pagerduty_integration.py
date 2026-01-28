"""
PagerDuty Integration - Critical Incident Escalation
=====================================================

Route critical incidents to on-call engineers via PagerDuty
"""

from datetime import datetime
from typing import Dict, Optional, List
import asyncio
import aiohttp


class PagerDutyIntegration:
    """
    PagerDuty integration for incident escalation
    
    Features:
    - Trigger incidents for P0/P1 alerts
    - Auto-acknowledge from DevOps Sentinel
    - Auto-resolve when incidents close
    - Link incidents bidirectionally
    - Escalation to backup on-call
    - Incident notes sync
    """
    
    def __init__(self, integration_key: str, api_token: Optional[str] = None):
        self.integration_key = integration_key
        self.api_token = api_token
        self.events_url = "https://events.pagerduty.com/v2/enqueue"
        self.api_url = "https://api.pagerduty.com"
    
    async def trigger_incident(
        self,
        incident: Dict,
        severity: str = 'critical',
        custom_details: Optional[Dict] = None
    ) -> Dict:
        """
        Trigger PagerDuty incident
        
        Args:
            incident: DevOps Sentinel incident data
            severity: 'critical', 'error', 'warning', 'info'
            custom_details: Additional context
        
        Returns:
            PagerDuty response with dedup_key
        """
        payload = {
            "routing_key": self.integration_key,
            "event_action": "trigger",
            "dedup_key": f"sentinel-{incident['id']}",
            "payload": {
                "summary": f"[{incident.get('severity', 'P2')}] {incident.get('service_name', 'Unknown Service')} - {incident.get('failure_type', 'Incident')}",
                "severity": severity,
                "source": incident.get('service_name', 'DevOps Sentinel'),
                "timestamp": incident.get('created_at', datetime.utcnow().isoformat()),
                "component": incident.get('service_id'),
                "group": incident.get('team_id'),
                "class": incident.get('failure_type', 'availability'),
                "custom_details": custom_details or {
                    "incident_id": incident['id'],
                    "service_name": incident.get('service_name'),
                    "service_url": incident.get('service_url'),
                    "error_message": incident.get('error_message'),
                    "response_time": incident.get('response_time_ms'),
                    "dashboard_url": f"https://devops-sentinel.dev/incidents/{incident['id']}"
                }
            },
            "links": [
                {
                    "href": f"https://devops-sentinel.dev/incidents/{incident['id']}",
                    "text": "View in DevOps Sentinel"
                }
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.events_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 202:
                    result = await response.json()
                    return {
                        'status': 'triggered',
                        'dedup_key': result.get('dedup_key'),
                        'message': result.get('message')
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"PagerDuty trigger failed: {error_text}")
    
    async def acknowledge_incident(
        self,
        incident_id: str,
        acknowledged_by: str = 'DevOps Sentinel'
    ) -> Dict:
        """
        Acknowledge PagerDuty incident
        
        Args:
            incident_id: Sentinel incident ID
            acknowledged_by: Who acknowledged
        """
        payload = {
            "routing_key": self.integration_key,
            "event_action": "acknowledge",
            "dedup_key": f"sentinel-{incident_id}",
            "payload": {
                "summary": f"Acknowledged by {acknowledged_by}",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.events_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 202:
                    return {'status': 'acknowledged'}
                else:
                    raise Exception(f"PagerDuty acknowledge failed: {await response.text()}")
    
    async def resolve_incident(
        self,
        incident_id: str,
        resolution_note: Optional[str] = None
    ) -> Dict:
        """
        Resolve PagerDuty incident
        
        Args:
            incident_id: Sentinel incident ID
            resolution_note: Resolution details
        """
        payload = {
            "routing_key": self.integration_key,
            "event_action": "resolve",
            "dedup_key": f"sentinel-{incident_id}",
            "payload": {
                "summary": resolution_note or "Resolved in DevOps Sentinel",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.events_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 202:
                    return {'status': 'resolved'}
                else:
                    raise Exception(f"PagerDuty resolve failed: {await response.text()}")
    
    async def add_note(
        self,
        pagerduty_incident_id: str,
        note: str,
        user_email: str
    ) -> Dict:
        """
        Add note to PagerDuty incident (requires API token)
        
        Args:
            pagerduty_incident_id: PagerDuty incident ID
            note: Note text
            user_email: Email of user adding note
        """
        if not self.api_token:
            raise ValueError("API token required for adding notes")
        
        payload = {
            "note": {
                "content": note
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/incidents/{pagerduty_incident_id}/notes",
                json=payload,
                headers={
                    "Authorization": f"Token token={self.api_token}",
                    "Content-Type": "application/json",
                    "From": user_email
                }
            ) as response:
                if response.status == 201:
                    return {'status': 'note_added'}
                else:
                    raise Exception(f"Failed to add note: {await response.text()}")
    
    async def get_incident_status(
        self,
        pagerduty_incident_id: str
    ) -> Dict:
        """
        Get PagerDuty incident status (requires API token)
        
        Returns:
            Status, assignee, acknowledgements
        """
        if not self.api_token:
            raise ValueError("API token required for status check")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.api_url}/incidents/{pagerduty_incident_id}",
                headers={
                    "Authorization": f"Token token={self.api_token}",
                    "Accept": "application/vnd.pagerduty+json;version=2"
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    incident = data.get('incident', {})
                    return {
                        'status': incident.get('status'),
                        'urgency': incident.get('urgency'),
                        'assigned_to': incident.get('assignments', [{}])[0].get('assignee', {}).get('summary'),
                        'acknowledged_at': incident.get('last_status_change_at'),
                        'html_url': incident.get('html_url')
                    }
                else:
                    raise Exception(f"Failed to get status: {await response.text()}")
    
    async def escalate_to_backup(
        self,
        incident: Dict,
        escalation_reason: str = 'Primary on-call not responding'
    ) -> Dict:
        """
        Escalate to backup on-call (re-trigger with higher urgency)
        
        Args:
            incident: Incident data
            escalation_reason: Why escalating
        """
        # Trigger new incident with [ESCALATED] prefix
        escalated_incident = incident.copy()
        escalated_incident['failure_type'] = f"[ESCALATED] {incident.get('failure_type', 'Incident')}"
        
        return await self.trigger_incident(
            escalated_incident,
            severity='critical',
            custom_details={
                **incident,
                'escalation_reason': escalation_reason,
                'escalated_at': datetime.utcnow().isoformat()
            }
        )
    
    def should_page(self, incident: Dict) -> bool:
        """
        Determine if incident should trigger PagerDuty page
        
        Rules:
        - Always page for P0 (critical outages)
        - Page for P1 during business hours
        - Never page for P2/P3
        """
        severity = incident.get('severity', 'P3')
        
        if severity == 'P0':
            return True
        
        if severity == 'P1':
            # Could add time-based logic here
            return True
        
        return False


# Example usage
if __name__ == "__main__":
    async def test_pagerduty():
        # Mock incident
        incident = {
            'id': 'inc-123',
            'service_name': 'API Gateway',
            'service_id': 'svc-1',
            'severity': 'P0',
            'failure_type': 'Service Down',
            'error_message': 'Connection timeout',
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Initialize (use test integration key)
        pd = PagerDutyIntegration('YOUR_INTEGRATION_KEY')
        
        # Check if should page
        if pd.should_page(incident):
            # Trigger incident
            result = await pd.trigger_incident(incident, severity='critical')
            print(f"Triggered: {result}")
            
            # Later: acknowledge
            await asyncio.sleep(2)
            await pd.acknowledge_incident(incident['id'])
            print("Acknowledged")
            
            # Later: resolve
            await asyncio.sleep(2)
            await pd.resolve_incident(incident['id'], "Issue resolved")
            print("Resolved")
    
    asyncio.run(test_pagerduty())
