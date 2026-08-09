import sys
from unittest.mock import MagicMock

# Mock missing dependencies to allow importing QuickHealthCheck
for module in ['aiohttp', 'fastapi', 'pydantic']:
    sys.modules[module] = MagicMock()

import asyncio
import unittest
from src.api.quick_health_check import QuickHealthCheck

class TestSSRFProtection(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.checker = QuickHealthCheck()

    async def test_is_safe_hostname(self):
        # Test known unsafe hostnames/IPs
        unsafe_hosts = [
            'localhost',
            '127.0.0.1',
            '::1',
            '0.0.0.0',
            '169.254.169.254', # AWS Metadata
            '10.0.0.1',       # Private Class A
            '172.16.0.1',     # Private Class B
            '192.168.1.1',    # Private Class C
        ]

        for host in unsafe_hosts:
            is_safe = await self.checker._is_safe_hostname(host)
            print(f"Host {host} safe? {is_safe}")
            self.assertFalse(is_safe, f"Host {host} should be unsafe")

    async def test_is_safe_hostname_public(self):
        # Test known safe hostnames/IPs
        # Note: This depends on DNS resolution working in the environment
        safe_hosts = [
            'google.com',
            '8.8.8.8',
            'github.com'
        ]

        for host in safe_hosts:
            is_safe = await self.checker._is_safe_hostname(host)
            print(f"Host {host} safe? {is_safe}")
            # If DNS fails, it will return False, which is also 'safe' in terms of SSRF
            # (it just won't work for health check), but for this test we expect True
            # if the environment has internet.
            # I'll just log it for now since I know DNS resolution works from my previous check.
            self.assertTrue(is_safe, f"Host {host} should be safe")

    async def test_check_url_initial_validation(self):
        # Test that check_url catches unsafe URLs before calling any other methods
        result = await self.checker.check_url("http://127.0.0.1/admin")
        self.assertEqual(result['status'], 'error')
        self.assertIn('Forbidden', result['error'])
        self.assertFalse(result['healthy'])

    async def test_check_http_redirect_to_unsafe(self):
        # Test that _check_http blocks redirects to internal IPs

        class AsyncContextManagerMock:
            def __init__(self, return_value):
                self.return_value = return_value
            async def __aenter__(self):
                return self.return_value
            async def __aexit__(self, exc_type, exc, tb):
                pass

        mock_response = MagicMock()
        mock_response.status = 302
        mock_response.headers = {'Location': 'http://localhost/admin'}

        mock_session = MagicMock()
        mock_session.get.return_value = AsyncContextManagerMock(mock_response)

        with unittest.mock.patch('aiohttp.ClientSession', return_value=AsyncContextManagerMock(mock_session)):
            result = await self.checker._check_http("http://safe-site.com", 10)

            self.assertEqual(result['status_code'], 403)
            self.assertIn('Forbidden', result['error'])

    async def test_check_ssl_unsafe(self):
        # Test that _check_ssl blocks unsafe hosts
        result = await self.checker._check_ssl("https://127.0.0.1")
        self.assertFalse(result['valid'])
        self.assertIn('Forbidden', result['error'])

if __name__ == '__main__':
    unittest.main()
