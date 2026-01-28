"""
Slack Integration Test Script
=============================

Test Slack webhook and message formatting
Run: python scripts/test_slack.py
"""

import asyncio
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.slack import SlackIntegration


async def test_webhook():
    """Test sending a message to Slack webhook"""
    webhook_url = os.environ.get('SLACK_WEBHOOK_URL')
    
    if not webhook_url:
        print("❌ SLACK_WEBHOOK_URL not set in environment")
        print("   Set it in .env or export SLACK_WEBHOOK_URL=...")
        return False
    
    slack = SlackIntegration(webhook_url=webhook_url)
    
    # Test incident alert
    test_incident = {
        'id': 'test-123',
        'title': '[TEST] DevOps Sentinel Integration Test',
        'severity': 'P3',
        'service_name': 'Test Service',
        'description': 'This is a test alert from DevOps Sentinel. If you see this, Slack integration is working!'
    }
    
    print("📤 Sending test incident alert...")
    result = await slack.send_incident_alert(test_incident)
    
    if result:
        print("✅ Incident alert sent successfully!")
    else:
        print("❌ Failed to send incident alert")
        return False
    
    return True


async def test_message_formatting():
    """Test message block formatting"""
    slack = SlackIntegration()
    
    # Test incident with similar past incident
    incident = {
        'id': 'inc-001',
        'title': 'Database Connection Timeout',
        'severity': 'P1',
        'service_name': 'API Gateway',
        'description': 'Connection to primary database timed out after 30 seconds'
    }
    
    similar = {
        'id': 'inc-old-001',
        'title': 'Previous DB Timeout',
        'resolution': 'Restarted connection pool and increased max connections'
    }
    
    blocks = slack._build_incident_blocks(incident, similar)
    
    print("📋 Generated message blocks:")
    print(f"   - {len(blocks)} blocks created")
    
    # Verify structure
    block_types = [b.get('type') for b in blocks]
    assert 'header' in block_types, "Missing header block"
    assert 'section' in block_types, "Missing section block"
    assert 'actions' in block_types, "Missing actions block"
    
    print("✅ Message formatting test passed!")
    return True


async def test_slash_command_handling():
    """Test slash command responses"""
    slack = SlackIntegration()
    
    # Test status command
    response = await slack.handle_slash_command(
        command='/sentinel',
        text='status',
        user_id='U123',
        channel_id='C123'
    )
    
    assert 'text' in response, "Response missing text"
    print(f"✅ /sentinel status: {response['text'][:50]}...")
    
    # Test ack command
    response = await slack.handle_slash_command(
        command='/sentinel',
        text='ack inc-123',
        user_id='U123',
        channel_id='C123'
    )
    
    assert 'acknowledged' in response.get('text', '').lower(), "Ack response incorrect"
    print(f"✅ /sentinel ack: {response['text'][:50]}...")
    
    # Test help
    response = await slack.handle_slash_command(
        command='/sentinel',
        text='',
        user_id='U123',
        channel_id='C123'
    )
    
    assert 'Commands' in response.get('text', ''), "Help response incorrect"
    print(f"✅ /sentinel (help): Shows command list")
    
    return True


async def test_channel_routing():
    """Test severity-based channel routing"""
    slack = SlackIntegration()
    
    routing = {
        'P0': '#incidents-critical',
        'P1': '#incidents-high',
        'P2': '#incidents',
        'P3': '#incidents'
    }
    
    for severity, expected_channel in routing.items():
        channel = slack._get_channel_for_severity(severity)
        assert channel == expected_channel, f"Wrong channel for {severity}"
    
    print("✅ Channel routing test passed!")
    return True


async def test_request_verification():
    """Test Slack request signature verification"""
    slack = SlackIntegration(signing_secret='test_secret')
    
    import hmac
    import hashlib
    import time
    
    timestamp = str(int(time.time()))
    body = b'test_body'
    
    # Create valid signature
    sig_basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    signature = 'v0=' + hmac.new(
        b'test_secret',
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Valid request
    assert slack.verify_request(signature, timestamp, body) is True
    print("✅ Valid signature verification passed")
    
    # Invalid signature
    assert slack.verify_request('v0=invalid', timestamp, body) is False
    print("✅ Invalid signature correctly rejected")
    
    # Old timestamp (should fail)
    old_timestamp = str(int(time.time()) - 600)  # 10 minutes ago
    old_sig = 'v0=' + hmac.new(
        b'test_secret',
        f"v0:{old_timestamp}:{body.decode('utf-8')}".encode(),
        hashlib.sha256
    ).hexdigest()
    
    assert slack.verify_request(old_sig, old_timestamp, body) is False
    print("✅ Old timestamp correctly rejected")
    
    return True


async def main():
    """Run all tests"""
    print("=" * 50)
    print("Slack Integration Tests")
    print("=" * 50)
    print()
    
    tests = [
        ("Message Formatting", test_message_formatting),
        ("Slash Command Handling", test_slash_command_handling),
        ("Channel Routing", test_channel_routing),
        ("Request Verification", test_request_verification),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n🧪 Testing: {name}")
        print("-" * 30)
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append((name, False))
    
    # Webhook test (only if env is set)
    if os.environ.get('SLACK_WEBHOOK_URL'):
        print(f"\n🧪 Testing: Webhook (Live)")
        print("-" * 30)
        try:
            result = await test_webhook()
            results.append(("Webhook", result))
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(("Webhook", False))
    else:
        print("\n⏭️  Skipping webhook test (SLACK_WEBHOOK_URL not set)")
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
