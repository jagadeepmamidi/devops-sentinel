"""
Tests for Slack Integration
===========================

Tests Slack webhook, slash commands, and message formatting
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import hashlib
import hmac
import time

from src.integrations.slack import SlackIntegration


class TestSlackIntegration:
    """Tests for SlackIntegration class"""
    
    @pytest.fixture
    def slack(self):
        return SlackIntegration(
            webhook_url="https://hooks.slack.com/test",
            bot_token="xoxb-test",
            signing_secret="test_secret"
        )
    
    @pytest.fixture
    def sample_incident(self):
        return {
            'id': 'inc-001',
            'title': 'Database Connection Error',
            'severity': 'P1',
            'service_name': 'API Gateway',
            'description': 'Connection to primary database failed'
        }
    
    def test_init_with_credentials(self, slack):
        """Should initialize with credentials"""
        assert slack.webhook_url is not None
        assert slack.bot_token is not None
        assert slack.signing_secret is not None
    
    def test_channel_routing_p0(self, slack):
        """P0 should go to critical channel"""
        channel = slack._get_channel_for_severity('P0')
        assert 'critical' in channel.lower()
    
    def test_channel_routing_p1(self, slack):
        """P1 should go to high priority channel"""
        channel = slack._get_channel_for_severity('P1')
        assert 'high' in channel.lower()
    
    def test_channel_routing_p2_p3(self, slack):
        """P2/P3 should go to default channel"""
        assert slack._get_channel_for_severity('P2') == '#incidents'
        assert slack._get_channel_for_severity('P3') == '#incidents'
    
    def test_build_incident_blocks(self, slack, sample_incident):
        """Should build valid Slack blocks"""
        blocks = slack._build_incident_blocks(sample_incident)
        
        assert len(blocks) > 0
        
        # Should have header
        assert any(b['type'] == 'header' for b in blocks)
        
        # Should have section with details
        assert any(b['type'] == 'section' for b in blocks)
        
        # Should have action buttons
        assert any(b['type'] == 'actions' for b in blocks)
    
    def test_build_incident_blocks_with_similar(self, slack, sample_incident):
        """Should include similar incident info"""
        similar = {
            'id': 'inc-old-001',
            'resolution': 'Restarted the service'
        }
        
        blocks = slack._build_incident_blocks(sample_incident, similar)
        
        # Should have reference to similar incident
        block_text = str(blocks)
        assert 'similar' in block_text.lower() or 'resolution' in block_text.lower()
    
    def test_action_buttons_include_ack(self, slack, sample_incident):
        """Should include acknowledge button"""
        blocks = slack._build_incident_blocks(sample_incident)
        
        actions_block = next(b for b in blocks if b['type'] == 'actions')
        elements = actions_block.get('elements', [])
        
        ack_button = next(
            (e for e in elements if 'ack' in e.get('action_id', '')),
            None
        )
        assert ack_button is not None
    
    def test_action_buttons_include_resolve(self, slack, sample_incident):
        """Should include resolve button"""
        blocks = slack._build_incident_blocks(sample_incident)
        
        actions_block = next(b for b in blocks if b['type'] == 'actions')
        elements = actions_block.get('elements', [])
        
        resolve_button = next(
            (e for e in elements if 'resolve' in e.get('action_id', '')),
            None
        )
        assert resolve_button is not None


class TestSlashCommands:
    """Tests for slash command handling"""
    
    @pytest.fixture
    def slack(self):
        return SlackIntegration()
    
    @pytest.mark.asyncio
    async def test_status_command(self, slack):
        """Should return system status"""
        response = await slack.handle_slash_command(
            command='/sentinel',
            text='status',
            user_id='U123',
            channel_id='C123'
        )
        
        assert 'text' in response
        assert 'status' in response['text'].lower()
    
    @pytest.mark.asyncio
    async def test_ack_command(self, slack):
        """Should acknowledge incident"""
        response = await slack.handle_slash_command(
            command='/sentinel',
            text='ack inc-123',
            user_id='U123',
            channel_id='C123'
        )
        
        assert 'acknowledged' in response['text'].lower()
        assert 'inc-123' in response['text']
    
    @pytest.mark.asyncio
    async def test_resolve_command(self, slack):
        """Should resolve incident"""
        response = await slack.handle_slash_command(
            command='/sentinel',
            text='resolve inc-123',
            user_id='U123',
            channel_id='C123'
        )
        
        assert 'resolved' in response['text'].lower()
    
    @pytest.mark.asyncio
    async def test_oncall_command(self, slack):
        """Should show on-call info"""
        response = await slack.handle_slash_command(
            command='/sentinel',
            text='oncall',
            user_id='U123',
            channel_id='C123'
        )
        
        assert 'on-call' in response['text'].lower() or 'On-Call' in response['text']
    
    @pytest.mark.asyncio
    async def test_help_command(self, slack):
        """Should show help text"""
        response = await slack.handle_slash_command(
            command='/sentinel',
            text='',
            user_id='U123',
            channel_id='C123'
        )
        
        assert 'commands' in response['text'].lower() or 'Commands' in response['text']


class TestRequestVerification:
    """Tests for Slack request signature verification"""
    
    @pytest.fixture
    def slack(self):
        return SlackIntegration(signing_secret='test_secret_12345')
    
    def test_valid_signature(self, slack):
        """Should accept valid signature"""
        timestamp = str(int(time.time()))
        body = b'test_payload'
        
        sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        signature = 'v0=' + hmac.new(
            b'test_secret_12345',
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        assert slack.verify_request(signature, timestamp, body) is True
    
    def test_invalid_signature(self, slack):
        """Should reject invalid signature"""
        timestamp = str(int(time.time()))
        body = b'test_payload'
        
        assert slack.verify_request('v0=invalid_signature', timestamp, body) is False
    
    def test_expired_timestamp(self, slack):
        """Should reject old requests"""
        old_timestamp = str(int(time.time()) - 600)  # 10 mins ago
        body = b'test_payload'
        
        sig_basestring = f"v0:{old_timestamp}:{body.decode('utf-8')}"
        signature = 'v0=' + hmac.new(
            b'test_secret_12345',
            sig_basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        assert slack.verify_request(signature, old_timestamp, body) is False
    
    def test_no_signing_secret(self):
        """Should skip verification when no secret"""
        slack = SlackIntegration(signing_secret=None)
        
        # Should return True (skip verification in dev)
        assert slack.verify_request('anything', '0', b'body') is True


class TestMessageSending:
    """Tests for message sending"""
    
    @pytest.fixture
    def slack(self):
        return SlackIntegration(webhook_url="https://hooks.slack.com/test")
    
    @pytest.mark.asyncio
    async def test_send_incident_alert(self):
        """Should format alert - uses mock mode when no webhook"""
        slack = SlackIntegration(webhook_url=None)
        
        result = await slack.send_incident_alert({
            'id': 'inc-001',
            'title': 'Test Incident',
            'severity': 'P2',
            'service_name': 'Test',
            'description': 'Test description'
        })
        
        # Returns True in mock/dev mode (no webhook)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_send_without_webhook(self):
        """Should handle missing webhook gracefully"""
        slack = SlackIntegration(webhook_url=None)
        
        # Should not crash, just print/log
        result = await slack.send_incident_alert({
            'id': 'inc-001',
            'title': 'Test'
        })
        
        # Returns True in mock/dev mode
        assert result is True


class TestInteractiveHandling:
    """Tests for interactive component handling"""
    
    @pytest.fixture
    def slack(self):
        return SlackIntegration()
    
    @pytest.mark.asyncio
    async def test_handle_ack_button(self, slack):
        """Should handle acknowledge button click"""
        payload = {
            'actions': [{'action_id': 'ack_inc-123'}],
            'user': {'id': 'U123'}
        }
        
        result = await slack.handle_interaction(payload)
        
        assert 'acknowledged' in result['text'].lower()
    
    @pytest.mark.asyncio
    async def test_handle_resolve_button(self, slack):
        """Should handle resolve button click"""
        payload = {
            'actions': [{'action_id': 'resolve_inc-123'}],
            'user': {'id': 'U123'}
        }
        
        result = await slack.handle_interaction(payload)
        
        assert 'resolved' in result['text'].lower()


class TestDailyDigest:
    """Tests for daily digest"""
    
    @pytest.fixture
    def slack(self):
        return SlackIntegration()
    
    @pytest.mark.asyncio
    async def test_send_daily_digest(self, slack):
        """Should build digest message"""
        summary = {
            'total_incidents': 5,
            'resolved': 4,
            'mttr_minutes': 25,
            'uptime_percent': 99.5
        }
        
        incidents = [
            {'service_name': 'API', 'title': 'Connection timeout'},
            {'service_name': 'DB', 'title': 'High latency'}
        ]
        
        result = await slack.send_daily_digest(summary, incidents)
        
        # Should succeed (mock mode)
        assert result is True
