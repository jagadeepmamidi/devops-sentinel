"""
Tests for Rate Limiter
======================

Tests rate limiting functionality
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from src.core.rate_limiter import RateLimiter, RateLimitExceeded


class TestRateLimiter:
    """Tests for RateLimiter class"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client"""
        mock = MagicMock()
        mock.table.return_value = mock
        mock.select.return_value = mock
        mock.insert.return_value = mock
        mock.eq.return_value = mock
        mock.gte.return_value = mock
        mock.lt.return_value = mock
        mock.delete.return_value = mock
        
        # Default: return empty data and count=0 (under limit)
        mock.execute = AsyncMock(return_value=MagicMock(data=[], count=0))
        return mock
    
    @pytest.fixture
    def limiter(self, mock_supabase):
        return RateLimiter(mock_supabase)
    
    def test_init(self, limiter):
        """Should initialize with Supabase client"""
        assert limiter.supabase is not None
        assert limiter._cache == {}
    
    def test_tier_limits_defined(self, limiter):
        """Should have limits defined for all tiers"""
        assert 'free' in limiter.TIER_LIMITS
        assert 'pro' in limiter.TIER_LIMITS
        assert 'enterprise' in limiter.TIER_LIMITS
    
    def test_free_tier_has_limits(self, limiter):
        """Free tier should have restrictive limits"""
        free_limits = limiter.TIER_LIMITS['free']
        
        assert 'health_checks_per_minute' in free_limits
        assert free_limits['health_checks_per_minute'] < 100
        assert free_limits['health_checks_per_day'] < 10000
    
    def test_pro_tier_has_higher_limits(self, limiter):
        """Pro tier should have higher limits than free"""
        free_limits = limiter.TIER_LIMITS['free']
        pro_limits = limiter.TIER_LIMITS['pro']
        
        assert pro_limits['health_checks_per_minute'] > free_limits['health_checks_per_minute']
    
    def test_enterprise_has_unlimited(self, limiter):
        """Enterprise should have unlimited (-1) for most"""
        enterprise_limits = limiter.TIER_LIMITS['enterprise']
        
        # -1 means unlimited
        assert enterprise_limits['health_checks_per_minute'] == -1
        assert enterprise_limits['api_calls_per_hour'] == -1
    
    def test_time_windows_defined(self, limiter):
        """Should have time windows defined"""
        assert 'minute' in limiter.TIME_WINDOWS
        assert 'hour' in limiter.TIME_WINDOWS
        assert 'day' in limiter.TIME_WINDOWS
        assert limiter.TIME_WINDOWS['minute'] == 60
        assert limiter.TIME_WINDOWS['hour'] == 3600
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_allows_first_request(self, limiter, mock_supabase):
        """Should allow first request (under limit)"""
        # Mock: user is free tier, 0 actions taken
        mock_supabase.execute = AsyncMock(return_value=MagicMock(
            data=[{'subscription_tier': 'free'}],
            count=0
        ))
        
        result = await limiter.check_rate_limit(
            user_id='user-1',
            action='health_checks',
            tier='free'
        )
        
        assert result['allowed'] is True
        assert result['tier'] == 'free'
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_raises_when_exceeded(self, limiter, mock_supabase):
        """Should raise RateLimitExceeded when limit reached"""
        # Mock: user has exceeded limit
        mock_supabase.execute = AsyncMock(return_value=MagicMock(
            data=[{}] * 100,
            count=100  # Exceeds free tier per-minute limit
        ))
        
        with pytest.raises(RateLimitExceeded) as exc:
            await limiter.check_rate_limit(
                user_id='user-1',
                action='health_checks',
                tier='free'
            )
        
        assert exc.value.action == 'health_checks'
        assert exc.value.tier == 'free'
    
    @pytest.mark.asyncio
    async def test_get_remaining_quota(self, limiter, mock_supabase):
        """Should return remaining quota"""
        mock_supabase.execute = AsyncMock(return_value=MagicMock(
            data=[{'subscription_tier': 'free'}],
            count=5
        ))
        
        quota = await limiter.get_remaining_quota('user-1', 'health_checks')
        
        assert 'remaining' in quota
        assert 'limits' in quota
        assert quota['action'] == 'health_checks'


class TestRateLimitExceeded:
    """Tests for RateLimitExceeded exception"""
    
    def test_exception_message(self):
        """Should have descriptive message"""
        exc = RateLimitExceeded(
            action='health_checks',
            window='minute',
            limit=10,
            current=15,
            tier='free'
        )
        
        assert 'health_checks' in exc.message
        assert '15/10' in exc.message
        assert 'minute' in exc.message
        assert 'free' in exc.message
    
    def test_to_dict(self):
        """Should convert to dict for API response"""
        exc = RateLimitExceeded(
            action='api_calls',
            window='hour',
            limit=500,
            current=501,
            tier='free'
        )
        
        d = exc.to_dict()
        
        assert d['error'] == 'rate_limit_exceeded'
        assert d['action'] == 'api_calls'
        assert d['window'] == 'hour'
        assert d['limit'] == 500
        assert d['current'] == 501
        assert d['tier'] == 'free'


class TestTierConfiguration:
    """Tests for tier configuration"""
    
    def test_all_tiers_have_required_limits(self):
        """Each tier should have common limit types"""
        limiter = RateLimiter(None)
        
        required = ['health_checks_per_minute', 'health_checks_per_day', 'api_calls_per_minute']
        
        for tier in ['free', 'pro', 'enterprise']:
            for limit in required:
                assert limit in limiter.TIER_LIMITS[tier], f"Missing {limit} in {tier}"
    
    def test_tier_limits_are_integers(self):
        """All limits should be integers"""
        limiter = RateLimiter(None)
        
        for tier, limits in limiter.TIER_LIMITS.items():
            for key, value in limits.items():
                assert isinstance(value, int), f"{tier}/{key} is not int"
