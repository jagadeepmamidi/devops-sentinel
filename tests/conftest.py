"""
Pytest Configuration
====================

Shared fixtures and configuration for tests
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_supabase():
    """
    Create a mock Supabase client
    
    Provides chainable mock for common patterns:
    - table().select().eq().execute()
    - table().insert().execute()
    - rpc().execute()
    """
    mock = MagicMock()
    
    # Make methods chainable
    mock.table.return_value = mock
    mock.select.return_value = mock
    mock.insert.return_value = mock
    mock.upsert.return_value = mock
    mock.update.return_value = mock
    mock.delete.return_value = mock
    mock.eq.return_value = mock
    mock.neq.return_value = mock
    mock.gte.return_value = mock
    mock.lte.return_value = mock
    mock.gt.return_value = mock
    mock.lt.return_value = mock
    mock.order.return_value = mock
    mock.limit.return_value = mock
    mock.range.return_value = mock
    mock.or_.return_value = mock
    mock.and_.return_value = mock
    mock.is_.return_value = mock
    
    # Default execute returns empty
    mock.execute = AsyncMock(return_value=MagicMock(data=[], count=0))
    
    # RPC is also async
    mock.rpc = MagicMock(return_value=MagicMock(
        execute=AsyncMock(return_value=MagicMock(data=[]))
    ))
    
    return mock


@pytest.fixture
def mock_supabase_with_data():
    """Factory fixture for pre-populated mock data"""
    def _create(data):
        mock = MagicMock()
        mock.table.return_value = mock
        mock.select.return_value = mock
        mock.insert.return_value = mock
        mock.eq.return_value = mock
        mock.gte.return_value = mock
        mock.lte.return_value = mock
        mock.order.return_value = mock
        mock.limit.return_value = mock
        mock.execute = AsyncMock(return_value=MagicMock(
            data=data,
            count=len(data)
        ))
        return mock
    return _create


@pytest.fixture
def sample_incident():
    """Sample incident for testing"""
    return {
        'id': 'inc-test-001',
        'title': 'Database Connection Timeout',
        'service_id': 'svc-api-001',
        'service_name': 'API Gateway',
        'severity': 'P1',
        'status': 'active',
        'failure_type': 'connection_timeout',
        'error_message': 'Connection to database timed out after 30000ms',
        'description': 'Primary database is not responding to health checks',
        'detected_at': '2026-01-27T12:00:00Z',
        'resolved_at': None
    }


@pytest.fixture
def sample_service():
    """Sample service for testing"""
    return {
        'id': 'svc-api-001',
        'name': 'API Gateway',
        'url': 'https://api.example.com/health',
        'check_interval_seconds': 60,
        'status': 'healthy',
        'last_check': '2026-01-27T12:00:00Z'
    }


@pytest.fixture
def sample_user():
    """Sample user for testing"""
    return {
        'id': 'user-test-001',
        'email': 'test@example.com',
        'name': 'Test User',
        'tier': 'pro',
        'created_at': '2026-01-01T00:00:00Z'
    }


@pytest.fixture
def sample_deployment():
    """Sample deployment for testing"""
    return {
        'id': 'deploy-001',
        'service_id': 'svc-api-001',
        'version': 'v1.2.3',
        'deployed_by': 'user-test-001',
        'deployed_at': '2026-01-27T11:00:00Z',
        'status': 'successful',
        'risk_score': 15
    }


# Test markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: marks tests that require API keys"
    )
