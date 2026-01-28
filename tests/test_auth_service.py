"""
Tests for Auth Service
======================

Tests authentication functionality
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.auth.auth_service import AuthService, get_current_user, get_optional_user


class TestAuthService:
    """Tests for AuthService class"""
    
    @pytest.fixture
    def auth_service(self):
        """Create auth service without Supabase (mock mode)"""
        return AuthService(None)
    
    @pytest.mark.asyncio
    async def test_signup_mock_mode(self, auth_service):
        """Should return mock response when no Supabase"""
        result = await auth_service.sign_up(
            email="test@example.com",
            password="password123",
            name="Test User"
        )
        
        assert 'user' in result
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert result['user']['email'] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_signin_mock_mode(self, auth_service):
        """Should return mock response for signin"""
        result = await auth_service.sign_in(
            email="test@example.com",
            password="password123"
        )
        
        assert 'user' in result
        assert 'access_token' in result
        assert result['user']['email'] == "test@example.com"
    
    @pytest.mark.asyncio
    async def test_signout_mock_mode(self, auth_service):
        """Should succeed for signout"""
        result = await auth_service.sign_out("mock-token")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_user_mock_mode(self, auth_service):
        """Should return mock user"""
        result = await auth_service.get_user("mock-token")
        
        assert result is not None
        assert 'id' in result
        assert 'email' in result
    
    @pytest.mark.asyncio
    async def test_refresh_token_mock_mode(self, auth_service):
        """Should return new tokens"""
        result = await auth_service.refresh_token("mock-refresh")
        
        assert 'access_token' in result
        assert 'refresh_token' in result
    
    @pytest.mark.asyncio
    async def test_reset_password_mock_mode(self, auth_service):
        """Should succeed for password reset"""
        result = await auth_service.reset_password("test@example.com")
        
        assert result is True
    
    def test_mock_auth_response_format(self, auth_service):
        """Mock response should have correct format"""
        response = auth_service._mock_auth_response(
            email="user@test.com",
            name="Test"
        )
        
        assert 'user' in response
        assert 'access_token' in response
        assert 'refresh_token' in response
        assert 'expires_at' in response
        
        assert response['user']['email'] == "user@test.com"
        assert response['user']['name'] == "Test"


class TestAuthServiceWithSupabase:
    """Tests with mocked Supabase client"""
    
    @pytest.fixture
    def mock_supabase(self):
        mock = MagicMock()
        
        # Mock auth methods
        mock.auth.sign_up = MagicMock(return_value=MagicMock(
            user=MagicMock(id='user-1', email='test@test.com'),
            session=MagicMock(
                access_token='token',
                refresh_token='refresh',
                expires_at=9999999999
            )
        ))
        
        mock.auth.sign_in_with_password = MagicMock(return_value=MagicMock(
            user=MagicMock(id='user-1', email='test@test.com'),
            session=MagicMock(
                access_token='token',
                refresh_token='refresh',
                expires_at=9999999999
            )
        ))
        
        mock.auth.get_user = MagicMock(return_value=MagicMock(
            user=MagicMock(id='user-1', email='test@test.com')
        ))
        
        mock.auth.sign_out = MagicMock()
        mock.auth.refresh_session = MagicMock(return_value=MagicMock(
            session=MagicMock(
                access_token='new-token',
                refresh_token='new-refresh',
                expires_at=9999999999
            )
        ))
        
        mock.auth.reset_password_email = MagicMock()
        mock.auth.update_user = MagicMock()
        
        # Mock table operations
        mock.table.return_value = mock
        mock.select.return_value = mock
        mock.insert.return_value = mock
        mock.eq.return_value = mock
        mock.execute = MagicMock(return_value=MagicMock(data=[
            {'id': 'user-1', 'name': 'Test', 'subscription_tier': 'free'}
        ]))
        
        return mock
    
    @pytest.fixture
    def auth_with_supabase(self, mock_supabase):
        return AuthService(mock_supabase)
    
    @pytest.mark.asyncio
    async def test_signup_with_supabase(self, auth_with_supabase):
        """Should call Supabase signup"""
        result = await auth_with_supabase.sign_up(
            email="new@test.com",
            password="password"
        )
        
        assert 'user' in result
        assert result['user']['email'] == "test@test.com"
    
    @pytest.mark.asyncio
    async def test_signin_with_supabase(self, auth_with_supabase):
        """Should call Supabase signin"""
        result = await auth_with_supabase.sign_in(
            email="test@test.com",
            password="password"
        )
        
        assert 'access_token' in result


class TestAuthDependencies:
    """Tests for FastAPI dependencies"""
    
    @pytest.mark.asyncio
    async def test_get_current_user_no_credentials(self):
        """Should raise 401 without credentials"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc:
            await get_current_user(None)
        
        assert exc.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_optional_user_without_credentials(self):
        """Should return None without credentials"""
        result = await get_optional_user(None)
        
        assert result is None


class TestUserProfile:
    """Tests for user profile operations"""
    
    @pytest.fixture
    def auth_service(self):
        return AuthService(None)
    
    def test_mock_user_has_tier(self, auth_service):
        """Mock user should have a tier"""
        response = auth_service._mock_auth_response("test@test.com")
        
        assert 'tier' in response['user']
    
    def test_mock_user_default_tier_is_free(self, auth_service):
        """Default tier should be free"""
        response = auth_service._mock_auth_response("test@test.com")
        
        assert response['user']['tier'] == 'free'
