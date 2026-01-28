"""
Tests for DevOps Sentinel CLI Authentication Module
====================================================

Tests cover:
- Credential storage (save/load/clear)
- Login state management
- Config directory creation
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import auth module functions
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from src.cli.auth import (
    ensure_config_dir,
    save_credentials,
    load_credentials,
    clear_credentials,
    get_current_user,
    get_access_token,
    is_logged_in,
    CONFIG_DIR,
    CREDENTIALS_FILE,
)


class TestCredentialStorage:
    """Test credential save/load/clear operations."""
    
    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Use temporary directory for config."""
        with patch('src.cli.auth.CONFIG_DIR', tmp_path):
            with patch('src.cli.auth.CREDENTIALS_FILE', tmp_path / 'credentials.json'):
                yield tmp_path
    
    def test_save_and_load_credentials(self, temp_config_dir):
        """Test credentials are saved and loaded correctly."""
        with patch('src.cli.auth.CONFIG_DIR', temp_config_dir):
            with patch('src.cli.auth.CREDENTIALS_FILE', temp_config_dir / 'credentials.json'):
                # Save credentials
                test_user = {'email': 'test@example.com', 'id': 'user-123'}
                save_credentials('access-token-123', 'refresh-token-456', test_user)
                
                # Load and verify
                creds = load_credentials()
                assert creds is not None
                assert creds['access_token'] == 'access-token-123'
                assert creds['refresh_token'] == 'refresh-token-456'
                assert creds['user']['email'] == 'test@example.com'
    
    def test_clear_credentials(self, temp_config_dir):
        """Test credentials are cleared properly."""
        creds_file = temp_config_dir / 'credentials.json'
        
        with patch('src.cli.auth.CONFIG_DIR', temp_config_dir):
            with patch('src.cli.auth.CREDENTIALS_FILE', creds_file):
                # Save then clear
                save_credentials('token', 'refresh', {'email': 'test@example.com'})
                assert creds_file.exists()
                
                clear_credentials()
                assert not creds_file.exists()
    
    def test_load_returns_none_when_no_creds(self, temp_config_dir):
        """Test load_credentials returns None when no file exists."""
        with patch('src.cli.auth.CREDENTIALS_FILE', temp_config_dir / 'nonexistent.json'):
            assert load_credentials() is None


class TestLoginState:
    """Test login state management."""
    
    @pytest.fixture
    def logged_in_state(self, tmp_path):
        """Set up a logged-in state."""
        creds_file = tmp_path / 'credentials.json'
        creds = {
            'access_token': 'test-token',
            'refresh_token': 'test-refresh',
            'user': {'email': 'user@test.com', 'id': 'uid-123'},
            'saved_at': 1234567890
        }
        creds_file.write_text(json.dumps(creds))
        return tmp_path, creds_file
    
    def test_is_logged_in_true(self, logged_in_state):
        """Test is_logged_in returns True when credentials exist."""
        tmp_path, creds_file = logged_in_state
        with patch('src.cli.auth.CREDENTIALS_FILE', creds_file):
            assert is_logged_in() is True
    
    def test_is_logged_in_false(self, tmp_path):
        """Test is_logged_in returns False when no credentials."""
        with patch('src.cli.auth.CREDENTIALS_FILE', tmp_path / 'nope.json'):
            assert is_logged_in() is False
    
    def test_get_current_user(self, logged_in_state):
        """Test get_current_user returns user dict."""
        tmp_path, creds_file = logged_in_state
        with patch('src.cli.auth.CREDENTIALS_FILE', creds_file):
            user = get_current_user()
            assert user is not None
            assert user['email'] == 'user@test.com'
    
    def test_get_access_token(self, logged_in_state):
        """Test get_access_token returns token string."""
        tmp_path, creds_file = logged_in_state
        with patch('src.cli.auth.CREDENTIALS_FILE', creds_file):
            token = get_access_token()
            assert token == 'test-token'


class TestConfigDirectory:
    """Test config directory management."""
    
    def test_ensure_config_dir_creates_directory(self, tmp_path):
        """Test config directory is created if missing."""
        new_dir = tmp_path / 'new_sentinel_config'
        with patch('src.cli.auth.CONFIG_DIR', new_dir):
            ensure_config_dir()
            assert new_dir.exists()
            assert new_dir.is_dir()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
