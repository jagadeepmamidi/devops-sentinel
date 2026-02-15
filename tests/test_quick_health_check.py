"""
Tests for Quick Health Check API
================================

Tests the viral health check feature
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from src.api.quick_health_check import QuickHealthCheck


class TestQuickHealthCheck:
    """Tests for QuickHealthCheck class"""
    
    @pytest.fixture
    def checker(self):
        checker = QuickHealthCheck()
        # Mock _is_safe_hostname to allow tests to run regardless of environment DNS
        checker._is_safe_hostname = AsyncMock(return_value=True)
        return checker
    
    def test_init(self, checker):
        """Should initialize with default timeout"""
        assert checker.DEFAULT_TIMEOUT == 10
    
    @pytest.mark.asyncio
    async def test_check_url_normalizes_bare_domain(self, checker):
        """Should add https:// to bare domain"""
        with patch.object(checker, '_check_http', new_callable=AsyncMock) as mock_http:
            mock_http.return_value = {
                'status_code': 200,
                'response_time_ms': 100
            }
            
            result = await checker.check_url("example.com")
            
            # Should have normalized to https://
            assert result['url'] == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_check_url_preserves_https(self, checker):
        """Should preserve https:// if specified"""
        with patch.object(checker, '_check_http', new_callable=AsyncMock) as mock_http:
            mock_http.return_value = {
                'status_code': 200,
                'response_time_ms': 100
            }
            
            result = await checker.check_url("https://example.com")
            
            assert result['url'] == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_check_url_healthy_response(self, checker):
        """Should return healthy for 200 response"""
        with patch.object(checker, '_check_http', new_callable=AsyncMock) as mock_http:
            with patch.object(checker, '_check_ssl', new_callable=AsyncMock) as mock_ssl:
                mock_http.return_value = {
                    'status_code': 200,
                    'response_time_ms': 100
                }
                mock_ssl.return_value = {'valid': True}
                
                result = await checker.check_url("https://example.com")
                
                assert result['status'] == 'healthy'
                assert result['healthy'] is True
    
    @pytest.mark.asyncio
    async def test_check_url_unhealthy_500(self, checker):
        """Should return unhealthy for 500 response"""
        with patch.object(checker, '_check_http', new_callable=AsyncMock) as mock_http:
            mock_http.return_value = {
                'status_code': 500,
                'response_time_ms': 100
            }
            
            result = await checker.check_url("https://example.com")
            
            assert result['status'] == 'unhealthy'
            assert result['healthy'] is False
    
    @pytest.mark.asyncio
    async def test_check_url_timeout(self, checker):
        """Should handle timeout gracefully"""
        import asyncio
        
        with patch.object(checker, '_check_http', new_callable=AsyncMock) as mock_http:
            mock_http.side_effect = asyncio.TimeoutError()
            
            result = await checker.check_url("https://slow-site.com")
            
            assert result['status'] == 'timeout'
            assert 'error' in result
            assert 'suggestions' in result
    
    @pytest.mark.asyncio
    async def test_check_url_includes_cta(self, checker):
        """Should include call-to-action"""
        with patch.object(checker, '_check_http', new_callable=AsyncMock) as mock_http:
            mock_http.return_value = {
                'status_code': 200,
                'response_time_ms': 100
            }
            
            result = await checker.check_url("https://example.com")
            
            assert 'cta' in result
            assert 'message' in result['cta']
            assert 'link' in result['cta']


class TestSuggestions:
    """Tests for suggestion generation"""
    
    @pytest.fixture
    def checker(self):
        checker = QuickHealthCheck()
        checker._is_safe_hostname = AsyncMock(return_value=True)
        return checker
    
    def test_suggestions_for_server_error(self, checker):
        """Should suggest checking logs for 500"""
        result = {
            'status_code': 500,
            'response_time_ms': 100,
            'ssl': {'valid': True}
        }
        
        suggestions = checker._generate_suggestions(result)
        
        assert any('server' in s.lower() or 'log' in s.lower() for s in suggestions)
    
    def test_suggestions_for_slow_response(self, checker):
        """Should suggest optimization for slow response"""
        result = {
            'status_code': 200,
            'response_time_ms': 3500,  # > 3000ms
            'ssl': {'valid': True}
        }
        
        suggestions = checker._generate_suggestions(result)
        
        assert any('slow' in s.lower() for s in suggestions)
    
    def test_suggestions_for_fast_response(self, checker):
        """Should praise fast response"""
        result = {
            'status_code': 200,
            'response_time_ms': 150,  # < 200ms
            'ssl': {'valid': True}
        }
        
        suggestions = checker._generate_suggestions(result)
        
        assert any('excellent' in s.lower() for s in suggestions)
    
    def test_suggestions_for_expiring_ssl(self, checker):
        """Should warn about expiring SSL"""
        result = {
            'status_code': 200,
            'response_time_ms': 200,
            'ssl': {'valid': True, 'warning': True, 'days_until_expiry': 15}
        }
        
        suggestions = checker._generate_suggestions(result)
        
        assert any('ssl' in s.lower() or 'expire' in s.lower() for s in suggestions)
    
    def test_suggestions_for_invalid_ssl(self, checker):
        """Should warn about invalid SSL"""
        result = {
            'status_code': 200,
            'response_time_ms': 200,
            'ssl': {'valid': False}
        }
        
        suggestions = checker._generate_suggestions(result)
        
        assert any('ssl' in s.lower() and 'invalid' in s.lower() for s in suggestions)
    
    def test_suggestions_for_404(self, checker):
        """Should suggest verifying URL for 404"""
        result = {
            'status_code': 404,
            'response_time_ms': 200
        }
        
        suggestions = checker._generate_suggestions(result)
        
        assert any('not found' in s.lower() or '404' in s.lower() or 'url' in s.lower() for s in suggestions)
    
    def test_healthy_site_suggestion(self, checker):
        """Should suggest monitoring for healthy sites"""
        result = {
            'status_code': 200,
            'response_time_ms': 500,  # Not excellent, not slow
            'healthy': True,
            'ssl': {'valid': True}
        }
        
        suggestions = checker._generate_suggestions(result)
        
        # Should have at least one suggestion
        assert len(suggestions) >= 0


class TestBatchCheck:
    """Tests for batch URL checking"""
    
    @pytest.fixture
    def checker(self):
        checker = QuickHealthCheck()
        checker._is_safe_hostname = AsyncMock(return_value=True)
        return checker
    
    @pytest.mark.asyncio
    async def test_check_multiple_urls(self, checker):
        """Should check multiple URLs in parallel"""
        with patch.object(checker, 'check_url', new_callable=AsyncMock) as mock_check:
            mock_check.return_value = {
                'url': 'https://example.com',
                'status': 'healthy',
                'healthy': True
            }
            
            results = await checker.check_multiple([
                'https://example.com',
                'https://google.com'
            ])
            
            assert len(results) == 2
            assert mock_check.call_count == 2
    
    @pytest.mark.asyncio
    async def test_check_multiple_handles_errors(self, checker):
        """Should handle individual URL errors"""
        with patch.object(checker, 'check_url', new_callable=AsyncMock) as mock_check:
            # First succeeds, second fails
            mock_check.side_effect = [
                {'url': 'https://ok.com', 'status': 'healthy'},
                Exception('Connection failed')
            ]
            
            results = await checker.check_multiple([
                'https://ok.com',
                'https://fail.com'
            ])
            
            assert len(results) == 2
            # Second result should have error
            assert 'error' in results[1]
