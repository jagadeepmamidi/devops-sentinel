"""
Baseline Monitor - Degraded State Detection
==========================================

Monitors service baselines and detects DEGRADED state before full failure.

Key Features:
- Calculates statistical baselines (avg, p50, p95, p99, stddev)
- Detects degradation when response times exceed thresholds
- Provides early warning before catastrophic failure
"""

import asyncio
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import statistics


class BaselineMonitor:
    """
    Monitors service health baselines and detects degraded states
    
    States:
        HEALTHY: Normal operation within baseline
        DEGRADED: Performance degrading (warning state)
        FAILED: Complete failure
    
    Degradation Triggers:
        - Response time > 1.5x p95 baseline
        - Response time > 2.0x average baseline
        - Error rate > 2x normal
    """
    
    def __init__(self, db_client=None):
        """
        Initialize baseline monitor
        
        Args:
            db_client: Database client (Supabase or SQLite)
        """
        self.db = db_client
        self.baselines_cache = {}  # In-memory cache for performance
    
    async def calculate_baseline(
        self,
        service_id: str,
        lookback_hours: int = 24
    ) -> Optional[Dict]:
        """
        Calculate baseline metrics from recent health check history
        
        Args:
            service_id: Service UUID
            lookback_hours: Hours of history to analyze (default 24)
        
        Returns:
            Baseline dict with statistical metrics, or None if insufficient data
        """
        # Fetch recent health checks (only healthy ones for baseline)
        # Note: This is pseudocode - actual implementation depends on your DB
        if self.db:
            health_checks = await self._fetch_health_checks(
                service_id,
                lookback_hours,
                healthy_only=True
            )
        else:
            # Fallback to mock data if no DB
            health_checks = []
        
        if len(health_checks) < 10:
            # Insufficient data for baseline
            return None
        
        # Extract and sort response times once for multiple percentile calculations
        response_times = [h['response_time_ms'] for h in health_checks]
        sorted_response_times = sorted(response_times)
        
        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        baseline = {
            'service_id': service_id,
            'avg_response_time_ms': avg_response_time,
            'p50_response_time_ms': self._percentile(sorted_response_times, 50),
            'p95_response_time_ms': self._percentile(sorted_response_times, 95),
            'p99_response_time_ms': self._percentile(sorted_response_times, 99),
            'stddev_response_time_ms': statistics.stdev(response_times, xbar=avg_response_time) if len(response_times) > 1 else 0,
            'sample_size': len(health_checks),
            'calculated_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(days=7)  # Re-calculate weekly
        }
        
        # Calculate error rate from all checks (including unhealthy)
        all_checks = await self._fetch_health_checks(
            service_id,
            lookback_hours,
            healthy_only=False
        ) if self.db else []
        
        if all_checks:
            healthy_count = sum(1 for h in all_checks if h['is_healthy'])
            baseline['error_rate'] = 1 - (healthy_count / len(all_checks))
        else:
            baseline['error_rate'] = 0.0
        
        # Cache baseline
        self.baselines_cache[service_id] = baseline
        
        # Store in database
        if self.db:
            await self._store_baseline(baseline)
        
        return baseline
    
    async def check_for_degradation(
        self,
        service_id: str,
        current_response_time: float,
        status_code: int
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if current metrics indicate degraded state
        
        Args:
            service_id: Service UUID
            current_response_time: Current response time in ms
            status_code: HTTP status code
        
        Returns:
            Tuple of (is_degraded, degradation_reason)
        """
        # Get baseline (from cache or DB)
        baseline = await self.get_baseline(service_id)
        
        if not baseline:
            # No baseline yet, can't detect degradation
            return False, None
        
        # Check if response time indicates degradation
        is_degraded = False
        reason = None
        
        # Rule 1: Response time > 1.5x p95
        if current_response_time > baseline['p95_response_time_ms'] * 1.5:
            is_degraded = True
            reason = (
                f"Response time {current_response_time:.0f}ms exceeds "
                f"1.5x p95 baseline ({baseline['p95_response_time_ms']:.0f}ms)"
            )
        
        # Rule 2: Response time > 2x average (more severe)
        elif current_response_time > baseline['avg_response_time_ms'] * 2.0:
            is_degraded = True
            reason = (
                f"Response time {current_response_time:.0f}ms exceeds "
                f"2x average baseline ({baseline['avg_response_time_ms']:.0f}ms)"
            )
        
        # Rule 3: Approaching failure threshold (p99 + 2 stddev)
        failure_threshold = baseline['p99_response_time_ms'] + (2 * baseline['stddev_response_time_ms'])
        if current_response_time > failure_threshold:
            is_degraded = True
            reason = f"Response time {current_response_time:.0f}ms approaching failure threshold"
        
        return is_degraded, reason
    
    async def get_baseline(self, service_id: str) -> Optional[Dict]:
        """
        Get cached baseline or fetch from database
        
        Args:
            service_id: Service UUID
        
        Returns:
            Baseline dict or None
        """
        # Check cache first
        if service_id in self.baselines_cache:
            cached = self.baselines_cache[service_id]
            # Check if expired
            if cached['expires_at'] > datetime.utcnow():
                return cached
        
        # Fetch from database
        if self.db:
            baseline = await self._fetch_baseline_from_db(service_id)
            if baseline:
                self.baselines_cache[service_id] = baseline
            return baseline
        
        return None
    
    async def update_baseline_if_needed(self, service_id: str):
        """
        Check if baseline needs recalculation and update if needed
        
        Args:
            service_id: Service UUID
        """
        baseline = await self.get_baseline(service_id)
        
        # Recalculate if:
        # 1. No baseline exists
        # 2. Baseline expired
        # 3. More than 7 days old
        should_recalculate = (
            baseline is None or
            baseline['expires_at'] <= datetime.utcnow()
        )
        
        if should_recalculate:
            await self.calculate_baseline(service_id)
    
    def _percentile(self, sorted_data: List[float], percentile: int) -> float:
        """
        Calculate percentile from already sorted data

        Args:
            sorted_data: List of floats, must be sorted in ascending order
            percentile: Integer between 0 and 100

        Returns:
            Calculated percentile value
        """
        if not sorted_data:
            return 0.0

        index = (len(sorted_data) - 1) * percentile / 100
        floor = int(index)
        ceil = floor + 1
        
        if ceil >= len(sorted_data):
            return sorted_data[floor]
        
        # Linear interpolation
        fraction = index - floor
        return sorted_data[floor] + fraction * (sorted_data[ceil] - sorted_data[floor])
    
    async def _fetch_health_checks(
        self,
        service_id: str,
        lookback_hours: int,
        healthy_only: bool
    ) -> List[Dict]:
        """Fetch health checks from database (placeholder)"""
        # TODO: Implement actual DB query when Supabase is ready
        # For now, return empty list
        return []
    
    async def _store_baseline(self, baseline: Dict):
        """Store baseline in database (placeholder)"""
        # TODO: Implement actual DB insert when Supabase is ready
        pass
    
    async def _fetch_baseline_from_db(self, service_id: str) -> Optional[Dict]:
        """Fetch baseline from database (placeholder)"""
        # TODO: Implement actual DB query when Supabase is ready
        return None


class DegradationAlert:
    """Data class for degradation alerts"""
    
    def __init__(
        self,
        service_id: str,
        service_name: str,
        current_response_time: float,
        baseline_p95: float,
        reason: str,
        severity: str = "warning"
    ):
        self.service_id = service_id
        self.service_name = service_name
        self.current_response_time = current_response_time
        self.baseline_p95 = baseline_p95
        self.reason = reason
        self.severity = severity
        self.detected_at = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/API"""
        return {
            'service_id': self.service_id,
            'service_name': self.service_name,
            'current_response_time': self.current_response_time,
            'baseline_p95': self.baseline_p95,
            'reason': self.reason,
            'severity': self.severity,
            'detected_at': self.detected_at.isoformat()
        }


# Example usage
if __name__ == "__main__":
    async def test_baseline_monitor():
        monitor = BaselineMonitor()
        
        # Mock service data
        service_id = "test-service-123"
        
        # Simulate degradation detection
        is_degraded, reason = await monitor.check_for_degradation(
            service_id=service_id,
            current_response_time=850,  # Slow response
            status_code=200
        )
        
        print(f"Degraded: {is_degraded}")
        if reason:
            print(f"Reason: {reason}")
    
    # Run test
    asyncio.run(test_baseline_monitor())
