"""
Chaos Engineering Tools - Automated Failure Injection
=======================================================

Test system resilience by injecting controlled failures
"""

from datetime import datetime
from typing import Dict, List, Optional
import asyncio
import aiohttp
import random


class ChaosEngineeringTools:
    """
    Chaos engineering for DevOps Sentinel
    
    Features:
    - Network latency injection
    - Service kill tests
    - Dependency failure simulation
    - Resource exhaustion
    - Traffic spike simulation
    - Blast radius measurement
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.active_experiments = {}
    
    async def inject_latency(
        self,
        service_id: str,
        latency_ms: int,
        duration_seconds: int,
        probability: float = 1.0
    ) -> Dict:
        """
        Inject network latency to a service
        
        Args:
            service_id: Target service
            latency_ms: Added latency in milliseconds
            duration_seconds: How long to inject
            probability: 0.0-1.0,  fraction of requests affected
        
        Returns:
            Experiment result with baseline vs degraded metrics
        """
        experiment_id = f"chaos-latency-{service_id}-{int(datetime.utcnow().timestamp())}"
        
        # Record baseline
        baseline = await self._measure_service_health(service_id)
        
        # Log experiment start
        await self._log_experiment(
            experiment_id=experiment_id,
            service_id=service_id,
            experiment_type='latency_injection',
            config={
                'latency_ms': latency_ms,
                'duration_seconds': duration_seconds,
                'probability': probability
            },
            status='running'
        )
        
        # Simulate latency (in real impl, this would use service mesh/proxy)
        print(f"[CHAOS] Injecting {latency_ms}ms latency to {service_id} for {duration_seconds}s")
        await asyncio.sleep(duration_seconds)
        
        # Measure degraded state
        degraded = await self._measure_service_health(service_id)
        
        # Calculate impact
        impact = self._calculate_impact(baseline, degraded)
        
        # Log experiment end
        await self._log_experiment(
            experiment_id=experiment_id,
            service_id=service_id,
            experiment_type='latency_injection',
            config={
                'latency_ms': latency_ms,
                'duration_seconds': duration_seconds
            },
            status='completed',
            results={
                'baseline': baseline,
                'degraded': degraded,
                'impact': impact
            }
        )
        
        return {
            'experiment_id': experiment_id,
            'type': 'latency_injection',
            'baseline_response_time': baseline['avg_response_time'],
            'degraded_response_time': degraded['avg_response_time'],
            'impact_percentage': impact['response_time_increase'],
            'incidents_triggered': impact.get('incidents_triggered', 0)
        }
    
    async def kill_service(
        self,
        service_id: str,
        duration_seconds: int
    ) -> Dict:
        """
        Kill a service temporarily to test failover
        
        Args:
            service_id: Service to kill
            duration_seconds: Downtime duration
        
        Returns:
            Experiment results including blast radius
        """
        experiment_id = f"chaos-kill-{service_id}-{int(datetime.utcnow().timestamp())}"
        
        # Identify dependencies
        dependencies = await self._get_dependent_services(service_id)
        
        # Log experiment
        await self._log_experiment(
            experiment_id=experiment_id,
            service_id=service_id,
            experiment_type='service_kill',
            config={'duration_seconds': duration_seconds},
            status='running'
        )
        
        print(f"[CHAOS] Killing service {service_id} for {duration_seconds}s")
        print(f"[CHAOS] Monitoring {len(dependencies)} dependent services for cascade failures")
        
        # Monitor all services during downtime
        monitoring_task = asyncio.create_task(
            self._monitor_cascade_failures(dependencies, duration_seconds)
        )
        
        # Simulate service kill
        await asyncio.sleep(duration_seconds)
        
        # Get monitoring results
        cascade_results = await monitoring_task
        
        blast_radius = len([s for s in cascade_results if s['cascaded']])
        
        # Log results
        await self._log_experiment(
            experiment_id=experiment_id,
            service_id=service_id,
            experiment_type='service_kill',
            config={'duration_seconds': duration_seconds},
            status='completed',
            results={
                'blast_radius': blast_radius,
                'total_dependencies': len(dependencies),
                'cascade_details': cascade_results
            }
        )
        
        return {
            'experiment_id': experiment_id,
            'type': 'service_kill',
            'downtime_seconds': duration_seconds,
            'blast_radius': blast_radius,
            'dependent_services': len(dependencies),
            'cascade_failures': cascade_results
        }
    
    async def simulate_traffic_spike(
        self,
        service_id: str,
        multiplier: float,
        duration_seconds: int
    ) -> Dict:
        """
        Simulate traffic spike to test auto-scaling
        
        Args:
            service_id: Target service
            multiplier: Traffic increase (2.0 = 2x normal traffic)
            duration_seconds: Spike duration
        
        Returns:
            Auto-scaling response and performance
        """
        experiment_id = f"chaos-traffic-{service_id}-{int(datetime.utcnow().timestamp())}"
        
        baseline = await self._measure_service_health(service_id)
        
        await self._log_experiment(
            experiment_id=experiment_id,
            service_id=service_id,
            experiment_type='traffic_spike',
            config={
                'multiplier': multiplier,
                'duration_seconds': duration_seconds
            },
            status='running'
        )
        
        print(f"[CHAOS] Simulating {multiplier}x traffic spike to {service_id}")
        
        # In real implementation, this would use load testing tools
        # For now, simulate by making concurrent requests
        normal_rps = baseline.get('requests_per_second', 10)
        spike_rps = int(normal_rps * multiplier)
        
        # Measure performance during spike
        await asyncio.sleep(duration_seconds)
        
        during_spike = await self._measure_service_health(service_id)
        
        # Check if auto-scaling happened (would monitor actual instances)
        auto_scaled = during_spike.get('instance_count', 1) > baseline.get('instance_count', 1)
        
        impact = self._calculate_impact(baseline, during_spike)
        
        await self._log_experiment(
            experiment_id=experiment_id,
            service_id=service_id,
            experiment_type='traffic_spike',
            config={'multiplier': multiplier},
            status='completed',
            results={
                'auto_scaled': auto_scaled,
                'baseline_rps': normal_rps,
                'peak_rps': spike_rps,
                'impact': impact
            }
        )
        
        return {
            'experiment_id': experiment_id,
            'type': 'traffic_spike',
            'multiplier': multiplier,
            'auto_scaled': auto_scaled,
            'performance_degradation': impact['response_time_increase'],
            'errors_introduced': impact.get('error_rate_increase', 0)
        }
    
    async def test_dependency_failure(
        self,
        service_id: str,
        dependency_id: str,
        failure_mode: str = 'timeout'
    ) -> Dict:
        """
        Simulate dependency failure to test circuit breakers
        
        Args:
            service_id: Service under test
            dependency_id: Dependency to fail
            failure_mode: 'timeout', 'error', 'slow'
        
        Returns:
            Circuit breaker response and graceful degradation
        """
        experiment_id = f"chaos-dep-{service_id}-{int(datetime.utcnow().timestamp())}"
        
        print(f"[CHAOS] Testing {service_id} response to {dependency_id} {failure_mode}")
        
        # Baseline with healthy dependency
        baseline = await self._measure_service_health(service_id)
        
        # Inject failure
        await self._simulate_dependency_failure(dependency_id, failure_mode)
        
        # Measure service behavior
        await asyncio.sleep(30)  # Give circuit breaker time to trip
        with_failure = await self._measure_service_health(service_id)
        
        # Check if circuit breaker activated
        circuit_breaker_tripped = with_failure.get('circuit_breaker_open', False)
        graceful_degradation = with_failure['status'] != 'down'  # Service still up?
        
        await self._log_experiment(
            experiment_id=experiment_id,
            service_id=service_id,
            experiment_type='dependency_failure',
            config={
                'dependency_id': dependency_id,
                'failure_mode': failure_mode
            },
            status='completed',
            results={
                'circuit_breaker_tripped': circuit_breaker_tripped,
                'graceful_degradation': graceful_degradation,
                'service_survived': with_failure['status'] != 'down'
            }
        )
        
        return {
            'experiment_id': experiment_id,
            'type': 'dependency_failure',
            'circuit_breaker_active': circuit_breaker_tripped,
            'graceful_degradation': graceful_degradation,
            'service_resilience': 'pass' if graceful_degradation else 'fail'
        }
    
    async def _measure_service_health(self, service_id: str) -> Dict:
        """Get current service health metrics"""
        # Get service details
        service = await self.supabase.table('services').select('*').eq(
            'id', service_id
        ).execute()
        
        if not service.data:
            return {}
        
        svc = service.data[0]
        
        return {
            'status': svc.get('status', 'unknown'),
            'avg_response_time': svc.get('avg_response_time', 0),
            'error_rate': svc.get('error_rate', 0),
            'requests_per_second': svc.get('requests_per_second', 0),
            'instance_count': svc.get('instance_count', 1)
        }
    
    async def _get_dependent_services(self, service_id: str) -> List[str]:
        """Get services that depend on this service"""
        deps = await self.supabase.table('service_dependencies').select(
            'source_service_id'
        ).eq('target_service_id', service_id).execute()
        
        return [d['source_service_id'] for d in deps.data] if deps.data else []
    
    async def _monitor_cascade_failures(
        self,
        services: List[str],
        duration: int
    ) -> List[Dict]:
        """Monitor services for cascade failures"""
        results = []
        
        for service_id in services:
            # Check service health at intervals
            initial = await self._measure_service_health(service_id)
            await asyncio.sleep(duration / 2)
            final = await self._measure_service_health(service_id)
            
            cascaded = final['status'] == 'down' and initial['status'] == 'healthy'
            
            results.append({
                'service_id': service_id,
                'cascaded': cascaded,
                'initial_status': initial['status'],
                'final_status': final['status']
            })
        
        return results
    
    async def _simulate_dependency_failure(self, dependency_id: str, mode: str):
        """Simulate a dependency failing"""
        # In real impl, would use service mesh to inject failures
        print(f"[CHAOS] Simulating {mode} failure for {dependency_id}")
        # This is a placeholder - actual implementation would use tools like
        # Istio, Linkerd, or Toxiproxy to inject real failures
    
    def _calculate_impact(self, baseline: Dict, degraded: Dict) -> Dict:
        """Calculate performance impact"""
        response_time_increase = (
            (degraded.get('avg_response_time', 0) - baseline.get('avg_response_time', 1)) /
            max(baseline.get('avg_response_time', 1), 1) * 100
        )
        
        error_rate_increase = (
            degraded.get('error_rate', 0) - baseline.get('error_rate', 0)
        )
        
        return {
            'response_time_increase': round(response_time_increase, 2),
            'error_rate_increase': round(error_rate_increase, 2),
            'service_degraded': degraded.get('status') != baseline.get('status')
        }
    
    async def _log_experiment(
        self,
        experiment_id: str,
        service_id: str,
        experiment_type: str,
        config: Dict,
        status: str,
        results: Optional[Dict] = None
    ):
        """Log chaos experiment to database"""
        await self.supabase.table('chaos_experiments').insert({
            'id': experiment_id,
            'service_id': service_id,
            'experiment_type': experiment_type,
            'config': config,
            'status': status,
            'results': results,
            'created_at': datetime.utcnow().isoformat(),
            'completed_at': datetime.utcnow().isoformat() if status == 'completed' else None
        }).execute()


# Example usage
if __name__ == "__main__":
    async def test_chaos():
        # Mock Supabase
        class MockSupabase:
            def table(self, name):
                return self
            
            def select(self, *args):
                return self
            
            def insert(self, *args):
                return self
            
            def eq(self, *args):
                return self
            
            async def execute(self):
                class Result:
                    data = [{
                        'id': 'svc-1',
                        'status': 'healthy',
                        'avg_response_time': 150,
                        'error_rate': 0.01,
                        'requests_per_second': 100
                    }]
                return Result()
        
        chaos = ChaosEngineeringTools(MockSupabase())
        
        # Test latency injection
        result = await chaos.inject_latency(
            service_id='svc-1',
            latency_ms=500,
            duration_seconds=5
        )
        print(f"Latency test: {result}")
        
        # Test service kill
        result = await chaos.kill_service(
            service_id='svc-1',
            duration_seconds=10
        )
        print(f"Kill test: {result}")
    
    asyncio.run(test_chaos())
