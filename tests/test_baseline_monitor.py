
import pytest
import asyncio
from src.core.baseline_monitor import BaselineMonitor

def test_percentile_direct():
    monitor = BaselineMonitor()
    # Data is already sorted
    data = [float(i) for i in range(1, 101)]
    assert monitor._percentile(data, 50) == 50.5
    assert monitor._percentile(data, 95) == 95.05
    assert monitor._percentile(data, 99) == 99.01

def test_percentile_with_unsorted_input_pre_sorted():
    monitor = BaselineMonitor()
    data = [10.0, 1.0, 5.0]
    # We must pass sorted data now
    assert monitor._percentile(sorted(data), 50) == 5.0

def test_calculate_baseline_integration():
    monitor = BaselineMonitor(db_client=True)

    async def mock_fetch(service_id, lookback_hours, healthy_only):
        return [{'response_time_ms': float(i), 'is_healthy': True} for i in range(1, 101)]

    # Mocking the internal methods
    monitor._fetch_health_checks = mock_fetch

    async def mock_store(baseline):
        pass
    monitor._store_baseline = mock_store

    async def run_test():
        baseline = await monitor.calculate_baseline("test-service")
        assert baseline is not None
        assert baseline['p50_response_time_ms'] == 50.5
        assert baseline['avg_response_time_ms'] == 50.5
        # p95: 95.05
        assert baseline['p95_response_time_ms'] == 95.05
        # stdev of 1..100
        import statistics
        expected_stdev = statistics.stdev([float(i) for i in range(1, 101)])
        assert baseline['stddev_response_time_ms'] == expected_stdev

    asyncio.run(run_test())
