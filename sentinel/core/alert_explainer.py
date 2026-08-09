"""
Alert Explainer - "Why Did Sentinel Page Me?" Feature
======================================================

Generate plain-English explanations for every alert
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio


class AlertExplainer:
    """
    Generate human-readable explanations for alerts
    
    Features:
    - Plain-English explanations
    - Context from deployments, baselines, history
    - Similar incident references
    - Actionable next steps
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    async def explain_alert(self, incident_id: str) -> Dict:
        """
        Generate full explanation for an alert
        
        Args:
            incident_id: The incident to explain
        
        Returns:
            Complete explanation with reasons, context, and history
        """
        # Get incident details
        incident = await self._get_incident(incident_id)
        if not incident:
            return {'error': 'Incident not found'}
        
        # Get related data
        service = await self._get_service(incident['service_id'])
        baseline = await self._get_baseline(incident['service_id'])
        deployment = await self._get_recent_deployment(incident['service_id'])
        similar = await self._find_similar_incident(incident)
        dependencies = await self._get_affected_dependencies(incident['service_id'])
        
        # Build explanation
        explanation = {
            'incident_id': incident_id,
            'summary': self._generate_summary(incident, service),
            'severity': incident.get('severity', 'P2'),
            'reasons': self._generate_reasons(incident, service, baseline),
            'context': self._generate_context(incident, deployment, dependencies),
            'history': None,
            'suggested_actions': self._generate_actions(incident, similar),
            'generated_at': datetime.utcnow().isoformat()
        }
        
        # Add history if similar incident found
        if similar:
            explanation['history'] = {
                'related_incident_id': similar['id'],
                'occurred': similar.get('detected_at'),
                'similarity': similar.get('similarity_score', 0.85),
                'resolution': similar.get('resolution_notes'),
                'time_to_resolve': similar.get('time_to_resolve_minutes')
            }
        
        return explanation
    
    def _generate_summary(self, incident: Dict, service: Optional[Dict]) -> str:
        """Generate one-line summary"""
        severity = incident.get('severity', 'P2')
        service_name = service.get('name', 'Unknown Service') if service else 'Unknown Service'
        failure_type = incident.get('failure_type', 'issue')
        
        severity_map = {
            'P0': 'CRITICAL',
            'P1': 'High Priority',
            'P2': 'Medium Priority',
            'P3': 'Low Priority'
        }
        
        return f"{severity_map.get(severity, 'Alert')}: {service_name} - {failure_type}"
    
    def _generate_reasons(
        self,
        incident: Dict,
        service: Optional[Dict],
        baseline: Optional[Dict]
    ) -> List[str]:
        """Generate list of reasons why this alert was triggered"""
        reasons = []
        
        # Severity-based reasons
        severity = incident.get('severity')
        if severity == 'P0':
            reasons.append("Service is DOWN (critical outage detected)")
        elif severity == 'P1':
            reasons.append("Severe degradation detected (P1 alert)")
        
        # Service criticality
        if service:
            criticality = service.get('criticality', 'standard')
            if criticality == 'critical':
                reasons.append("Service is marked as CRITICAL (user-facing)")
            elif criticality == 'high':
                reasons.append("Service has HIGH criticality rating")
        
        # Metric-based reasons
        if baseline:
            # Error rate comparison
            current_error = incident.get('error_rate', 0)
            baseline_error = baseline.get('error_rate_p95', 0.01)
            if baseline_error > 0 and current_error > baseline_error * 2:
                multiplier = current_error / baseline_error
                reasons.append(
                    f"Error rate exceeded baseline by {multiplier:.1f}x "
                    f"({current_error:.1%} vs {baseline_error:.1%} normal)"
                )
            
            # Response time comparison
            current_latency = incident.get('response_time_ms', 0)
            baseline_latency = baseline.get('response_time_p95', 200)
            if baseline_latency > 0 and current_latency > baseline_latency * 2:
                multiplier = current_latency / baseline_latency
                reasons.append(
                    f"Response time {multiplier:.1f}x slower than normal "
                    f"({current_latency}ms vs {baseline_latency}ms)"
                )
        
        # Status code reasons
        status_code = incident.get('status_code')
        if status_code:
            if status_code >= 500:
                reasons.append(f"Server error detected (HTTP {status_code})")
            elif status_code == 0:
                reasons.append("Connection failed (service unreachable)")
            elif status_code >= 400:
                reasons.append(f"Client error detected (HTTP {status_code})")
        
        # Failure type specific
        failure_type = incident.get('failure_type', '')
        if failure_type == 'ssl_expiry':
            days = incident.get('ssl_days_remaining', 0)
            reasons.append(f"SSL certificate expiring in {days} days")
        elif failure_type == 'connection_timeout':
            reasons.append("Connection timeout (service not responding)")
        elif failure_type == 'dns_failure':
            reasons.append("DNS resolution failed")
        
        # Ensure at least one reason
        if not reasons:
            reasons.append("Anomaly detected in service behavior")
        
        return reasons
    
    def _generate_context(
        self,
        incident: Dict,
        deployment: Optional[Dict],
        dependencies: List[Dict]
    ) -> List[str]:
        """Generate contextual information"""
        context = []
        
        # Deployment context
        if deployment:
            deployed_at = deployment.get('deployed_at')
            if deployed_at:
                try:
                    deploy_time = datetime.fromisoformat(deployed_at.replace('Z', '+00:00'))
                    minutes_ago = (datetime.utcnow() - deploy_time.replace(tzinfo=None)).seconds // 60
                    
                    if minutes_ago < 60:
                        context.append(
                            f"Deployment v{deployment.get('version', 'unknown')} "
                            f"occurred {minutes_ago} minutes ago"
                        )
                        
                        # Check deployment status
                        if deployment.get('status') == 'failed':
                            context.append("WARNING: Recent deployment marked as FAILED")
                except:
                    pass
        
        # Dependency context
        if dependencies:
            down_deps = [d for d in dependencies if d.get('status') == 'unhealthy']
            if down_deps:
                dep_names = ', '.join(d.get('name', 'Unknown') for d in down_deps[:3])
                context.append(f"Upstream services affected: {dep_names}")
        
        # Time context
        incident_time = incident.get('detected_at')
        if incident_time:
            context.append(f"First detected: {incident_time}")
        
        # Incident duration
        if incident.get('status') == 'ongoing':
            duration = incident.get('duration_minutes', 0)
            if duration > 0:
                context.append(f"Ongoing for {duration} minutes")
        
        return context
    
    def _generate_actions(
        self,
        incident: Dict,
        similar: Optional[Dict]
    ) -> List[str]:
        """Generate suggested next actions"""
        actions = []
        
        # If similar incident found with resolution
        if similar and similar.get('resolution_notes'):
            actions.append(
                f"SUGGESTED: {similar.get('resolution_notes')[:200]}"
            )
        
        # Failure type specific actions
        failure_type = incident.get('failure_type', '')
        
        if failure_type == 'connection_timeout':
            actions.append("Check server status and network connectivity")
            actions.append("Review recent deployments for connection pool changes")
        
        elif failure_type == 'ssl_expiry':
            actions.append("Renew SSL certificate immediately")
            actions.append("Check certificate auto-renewal configuration")
        
        elif failure_type == 'high_error_rate':
            actions.append("Check application logs for error patterns")
            actions.append("Consider rolling back recent deployments")
        
        elif failure_type == 'high_latency':
            actions.append("Check database query performance")
            actions.append("Review CPU/memory utilization")
            actions.append("Check for traffic spikes")
        
        # Generic actions
        if not actions:
            actions.append("Review service logs for errors")
            actions.append("Check recent deployments")
            actions.append("Verify upstream dependencies")
        
        return actions
    
    async def _get_incident(self, incident_id: str) -> Optional[Dict]:
        """Get incident details"""
        result = await self.supabase.table('incidents').select(
            '*'
        ).eq('id', incident_id).execute()
        
        return result.data[0] if result.data else None
    
    async def _get_service(self, service_id: str) -> Optional[Dict]:
        """Get service details"""
        result = await self.supabase.table('services').select(
            '*'
        ).eq('id', service_id).execute()
        
        return result.data[0] if result.data else None
    
    async def _get_baseline(self, service_id: str) -> Optional[Dict]:
        """Get service baseline metrics"""
        result = await self.supabase.table('baselines').select(
            '*'
        ).eq('service_id', service_id).order(
            'created_at', desc=True
        ).limit(1).execute()
        
        return result.data[0] if result.data else None
    
    async def _get_recent_deployment(self, service_id: str) -> Optional[Dict]:
        """Get most recent deployment"""
        one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        result = await self.supabase.table('deployments').select(
            '*'
        ).eq('service_id', service_id).gte(
            'deployed_at', one_hour_ago
        ).order('deployed_at', desc=True).limit(1).execute()
        
        return result.data[0] if result.data else None
    
    async def _find_similar_incident(self, incident: Dict) -> Optional[Dict]:
        """Find similar past incident"""
        # Look for incidents with same service and failure type
        result = await self.supabase.table('incidents').select(
            '*'
        ).eq('service_id', incident['service_id']).eq(
            'failure_type', incident.get('failure_type', '')
        ).eq('status', 'resolved').order(
            'resolved_at', desc=True
        ).limit(1).execute()
        
        if result.data:
            similar = result.data[0]
            similar['similarity_score'] = 0.85  # Placeholder
            return similar
        
        return None
    
    async def _get_affected_dependencies(self, service_id: str) -> List[Dict]:
        """Get upstream dependencies that might be affected"""
        result = await self.supabase.table('service_dependencies').select(
            'upstream_service_id'
        ).eq('downstream_service_id', service_id).execute()
        
        if not result.data:
            return []
        
        # Get status of each dependency
        dependencies = []
        for dep in result.data:
            upstream_id = dep['upstream_service_id']
            svc = await self._get_service(upstream_id)
            if svc:
                dependencies.append({
                    'id': upstream_id,
                    'name': svc.get('name'),
                    'status': svc.get('status', 'unknown')
                })
        
        return dependencies


# Example usage
if __name__ == "__main__":
    async def demo():
        class MockSupabase:
            def table(self, name):
                return self
            def select(self, *args):
                return self
            def eq(self, *args):
                return self
            def gte(self, *args):
                return self
            def order(self, *args, **kwargs):
                return self
            def limit(self, n):
                return self
            async def execute(self):
                class R:
                    data = [{
                        'id': 'inc-1',
                        'service_id': 'svc-1',
                        'severity': 'P0',
                        'failure_type': 'connection_timeout',
                        'error_rate': 0.15,
                        'detected_at': '2026-01-27T10:00:00Z'
                    }]
                return R()
        
        explainer = AlertExplainer(MockSupabase())
        explanation = await explainer.explain_alert('inc-1')
        
        print(f"Summary: {explanation['summary']}")
        print(f"Reasons:")
        for reason in explanation['reasons']:
            print(f"  - {reason}")
        print(f"Actions:")
        for action in explanation['suggested_actions']:
            print(f"  - {action}")
    
    asyncio.run(demo())
