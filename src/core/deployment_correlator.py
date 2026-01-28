"""
Deployment Correlator - Link Incidents to Deployments
======================================================

Correlates incidents with recent deployments to identify bad releases
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio


class DeploymentCorrelator:
    """
    Correlate incidents with deployments
    
    Features:
    - Track deployments per service
    - Calculate incident rate post-deployment
    - Identify problematic releases
    - Suggest rollbacks
    - Deployment risk scoring
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.correlation_window = timedelta(hours=2)  # Look for incidents within 2 hours
    
    async def record_deployment(
        self,
        service_id: str,
        version: str,
        environment: str = 'production',
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Record a deployment
        
        Args:
            service_id: Service being deployed
            version: Version/tag being deployed (e.g., 'v1.2.3', git SHA)
            environment: 'production', 'staging', 'development'
            metadata: Optional deployment details (commit, author, CI job)
        
        Returns:
            Deployment record
        """
        deployment = {
            'service_id': service_id,
            'version': version,
            'environment': environment,
            'deployed_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {},
            'status': 'deployed'
        }
        
        result = await self.supabase.table('deployments').insert(
            deployment
        ).execute()
        
        deployment_id = result.data[0]['id']
        
        # Start monitoring for incidents
        asyncio.create_task(
            self._monitor_post_deployment(deployment_id, service_id)
        )
        
        return result.data[0]
    
    async def _monitor_post_deployment(
        self,
        deployment_id: str,
        service_id: str
    ):
        """
        Monitor for incidents after deployment
        
        Wait for correlation window and check for incidents
        """
        await asyncio.sleep(self.correlation_window.total_seconds())
        
        # Check for incidents created after deployment
        deployment = await self.supabase.table('deployments').select(
            'deployed_at'
        ).eq('id', deployment_id).execute()
        
        if not deployment.data:
            return
        
        deployed_at = datetime.fromisoformat(deployment.data[0]['deployed_at'])
        window_end = deployed_at + self.correlation_window
        
        # Find incidents in the window
        incidents = await self.supabase.table('incidents').select(
            'id, severity, details'
        ).eq('service_id', service_id).gte(
            'created_at', deployed_at.isoformat()
        ).lte('created_at', window_end.isoformat()).execute()
        
        if incidents.data:
            # Correlate incidents to deployment
            incident_count = len(incidents.data)
            high_severity = sum(
                1 for i in incidents.data if i['severity'] in ['P0', 'P1']
            )
            
            # Update deployment status
            status = 'failed' if high_severity > 0 else 'degraded'
            
            await self.supabase.table('deployments').update({
                'status': status,
                'incident_count': incident_count,
                'high_severity_count': high_severity
            }).eq('id', deployment_id).execute()
            
            # Create deployment-incident links
            for incident in incidents.data:
                await self.supabase.table('deployment_incidents').insert({
                    'deployment_id': deployment_id,
                    'incident_id': incident['id'],
                    'correlation_confidence': self._calculate_confidence(
                        deployed_at,
                        datetime.fromisoformat(incident['created_at'])
                    )
                }).execute()
    
    def _calculate_confidence(
        self,
        deployed_at: datetime,
        incident_at: datetime
    ) -> float:
        """
        Calculate correlation confidence (0-1)
        
        Closer to deployment = higher confidence
        """
        time_diff = (incident_at - deployed_at).total_seconds()
        window_seconds = self.correlation_window.total_seconds()
        
        # Confidence decreases linearly with time
        # Incident immediately after deploy = 1.0
        # Incident at end of window = 0.5
        confidence = 1.0 - (0.5 * (time_diff / window_seconds))
        
        return max(0.5, min(1.0, confidence))
    
    async def check_deployment_health(
        self,
        deployment_id: str
    ) -> Dict:
        """
        Check if a deployment is healthy
        
        Returns:
            Health status with recommendation
        """
        deployment = await self.supabase.table('deployments').select(
            '*'
        ).eq('id', deployment_id).execute()
        
        if not deployment.data:
            return {'error': 'Deployment not found'}
        
        dep = deployment.data[0]
        incident_count = dep.get('incident_count', 0)
        high_severity_count = dep.get('high_severity_count', 0)
        
        # Determine health status
        if high_severity_count > 0:
            status = 'unhealthy'
            recommendation = 'ROLLBACK RECOMMENDED'
            risk_score = 0.9
        elif incident_count > 3:
            status = 'degraded'
            recommendation = 'Monitor closely, prepare rollback'
            risk_score = 0.6
        elif incident_count > 0:
            status = 'warning'
            recommendation = 'Monitor for further incidents'
            risk_score = 0.3
        else:
            status = 'healthy'
            recommendation = 'Deployment looks good'
            risk_score = 0.1
        
        return {
            'deployment_id': deployment_id,
            'version': dep['version'],
            'status': status,
            'incident_count': incident_count,
            'high_severity_count': high_severity_count,
            'recommendation': recommendation,
            'risk_score': risk_score,
            'deployed_at': dep['deployed_at']
        }
    
    async def get_deployment_history(
        self,
        service_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent deployment history for a service
        
        Returns:
            List of deployments with incident counts
        """
        deployments = await self.supabase.table('deployments').select(
            '*'
        ).eq('service_id', service_id).order(
            'deployed_at', desc=True
        ).limit(limit).execute()
        
        if not deployments.data:
            return []
        
        # Enrich with incident data
        enriched = []
        for dep in deployments.data:
            health = await self.check_deployment_health(dep['id'])
            enriched.append({
                **dep,
                'health': health
            })
        
        return enriched
    
    async def suggest_rollback(
        self,
        service_id: str
    ) -> Optional[Dict]:
        """
        Suggest rollback to last known good version
        
        Returns:
            Rollback suggestion or None
        """
        deployments = await self.get_deployment_history(service_id, limit=5)
        
        if not deployments:
            return None
        
        latest = deployments[0]
        
        # If latest deployment is unhealthy, find last healthy version
        if latest['health']['status'] in ['unhealthy', 'degraded']:
            for dep in deployments[1:]:
                if dep['health']['status'] == 'healthy':
                    return {
                        'should_rollback': True,
                        'current_version': latest['version'],
                        'rollback_to': dep['version'],
                        'reason': f"Current version has {latest['health']['incident_count']} incidents",
                        'last_healthy_deployed': dep['deployed_at']
                    }
            
            # No healthy version found
            return {
                'should_rollback': True,
                'current_version': latest['version'],
                'rollback_to': None,
                'reason': 'No recent healthy version found. Manual intervention required.'
            }
        
        return {
            'should_rollback': False,
            'current_version': latest['version'],
            'status': 'Deployment is healthy'
        }
    
    async def compare_deployments(
        self,
        deployment_id_1: str,
        deployment_id_2: str
    ) -> Dict:
        """
        Compare two deployments
        
        Use case: Compare prod vs staging deployments
        """
        dep1 = await self.check_deployment_health(deployment_id_1)
        dep2 = await self.check_deployment_health(deployment_id_2)
        
        return {
            'deployment_1': dep1,
            'deployment_2': dep2,
            'comparison': {
                'incident_delta': dep2['incident_count'] - dep1['incident_count'],
                'risk_delta': dep2['risk_score'] - dep1['risk_score'],
                'safer_deployment': deployment_id_1 if dep1['risk_score'] < dep2['risk_score'] else deployment_id_2
            }
        }
    
    async def get_deployment_trends(
        self,
        service_id: str,
        days: int = 30
    ) -> Dict:
        """
        Analyze deployment trends over time
        
        Returns:
            Trend analysis (failure rate, MTTR, deploy frequency)
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        deployments = await self.supabase.table('deployments').select(
            '*'
        ).eq('service_id', service_id).gte(
            'deployed_at', cutoff.isoformat()
        ).execute()
        
        if not deployments.data:
            return {
                'total_deployments': 0,
                'message': 'No deployments in the specified period'
            }
        
        total = len(deployments.data)
        failed = sum(1 for d in deployments.data if d.get('status') == 'failed')
        degraded = sum(1 for d in deployments.data if d.get('status') == 'degraded')
        healthy = sum(1 for d in deployments.data if d.get('status') == 'healthy')
        
        failure_rate = (failed / total) * 100 if total > 0 else 0
        success_rate = (healthy / total) * 100 if total > 0 else 0
        
        # Calculate deploy frequency
        deploy_frequency = total / days  # Deploys per day
        
        return {
            'period_days': days,
            'total_deployments': total,
            'failed': failed,
            'degraded': degraded,
            'healthy': healthy,
            'failure_rate': round(failure_rate, 2),
            'success_rate': round(success_rate, 2),
            'deploy_frequency': round(deploy_frequency, 2),
            'trend': 'improving' if success_rate > 70 else 'concerning' if success_rate < 50 else 'stable'
        }


# Example usage
if __name__ == "__main__":
    async def test_deployment_correlator():
        # Mock Supabase
        class MockSupabase:
            def table(self, name):
                return self
            
            def select(self, *args):
                return self
            
            def insert(self, *args):
                return self
            
            def update(self, *args):
                return self
            
            def eq(self, *args):
                return self
            
            def gte(self, *args):
                return self
            
            def lte(self, *args):
                return self
            
            def order(self, *args, **kwargs):
                return self
            
            def limit(self, *args):
                return self
            
            async def execute(self):
                class Result:
                    data = [{
                        'id': 'deploy-1',
                        'version': 'v1.2.3',
                        'deployed_at': datetime.utcnow().isoformat(),
                        'incident_count': 0,
                        'high_severity_count': 0,
                        'status': 'healthy'
                    }]
                return Result()
        
        correlator = DeploymentCorrelator(MockSupabase())
        
        # Record a deployment
        deployment = await correlator.record_deployment(
            'service-1',
            'v1.2.3',
            metadata={'commit': 'abc123', 'author': 'alice'}
        )
        print(f"Deployment recorded: {deployment}")
        
        # Check health
        health = await correlator.check_deployment_health('deploy-1')
        print(f"Deployment health: {health}")
    
    asyncio.run(test_deployment_correlator())
