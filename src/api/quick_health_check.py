"""
Quick Health Check - Viral Feature for Instant Value
=====================================================

No signup required - check any URL instantly
"""

from datetime import datetime
from typing import Dict, Optional
import aiohttp
import asyncio
import ssl
import socket
import ipaddress
from urllib.parse import urlparse, urljoin


class QuickHealthCheck:
    """
    Instant health check for any URL
    
    Features:
    - No authentication required (viral growth)
    - Response time measurement
    - SSL certificate validation
    - HTTP status check
    - Suggestions for issues
    """
    
    DEFAULT_TIMEOUT = 10  # seconds
    
    async def _is_safe_hostname(self, hostname: str) -> bool:
        """
        Check if a hostname resolves to a safe (public) IP address.
        Prevents SSRF by blocking private, loopback, and other restricted ranges.
        """
        if not hostname:
            return False

        # Block common local hostnames directly
        if hostname.lower() in ('localhost', '0.0.0.0', '::1'):
            return False

        try:
            # Resolve hostname to all associated IP addresses (IPv4 and IPv6)
            loop = asyncio.get_event_loop()
            addr_info = await loop.run_in_executor(
                None,
                lambda: socket.getaddrinfo(hostname, None)
            )

            for info in addr_info:
                ip = info[4][0]
                addr = ipaddress.ip_address(ip)

                # Check for restricted ranges
                if (addr.is_loopback or
                    addr.is_private or
                    addr.is_link_local or
                    addr.is_multicast or
                    addr.is_reserved or
                    addr.is_unspecified):
                    return False

            return True
        except Exception:
            # If resolution fails or any other error occurs, treat as unsafe
            return False

    async def check_url(self, url: str, timeout: int = None) -> Dict:
        """
        Perform instant health check on URL
        
        Args:
            url: URL to check (with or without protocol)
            timeout: Custom timeout in seconds
        
        Returns:
            Complete health check result
        """
        timeout = timeout or self.DEFAULT_TIMEOUT
        
        # Normalize URL
        if not url.startswith(('http://', 'https://')):
            url = f"https://{url}"
        
        # Initial SSRF validation
        parsed = urlparse(url)
        if not await self._is_safe_hostname(parsed.hostname):
            return {
                'url': url,
                'checked_at': datetime.utcnow().isoformat(),
                'status': 'error',
                'error': 'Forbidden: Access to internal or restricted IP ranges is not allowed.',
                'healthy': False,
                'suggestions': ['Please provide a valid public URL']
            }

        result = {
            'url': url,
            'checked_at': datetime.utcnow().isoformat(),
            'status': 'unknown',
            'healthy': False
        }
        
        try:
            # Perform HTTP check
            http_result = await self._check_http(url, timeout)
            result.update(http_result)
            
            # Check SSL if HTTPS
            if url.startswith('https://'):
                ssl_result = await self._check_ssl(url)
                result['ssl'] = ssl_result
            
            # Determine overall health
            result['healthy'] = (
                result.get('status_code', 0) in range(200, 400) and
                result.get('ssl', {}).get('valid', True)
            )
            
            result['status'] = 'healthy' if result['healthy'] else 'unhealthy'
            
            # Generate suggestions
            result['suggestions'] = self._generate_suggestions(result)
            
        except asyncio.TimeoutError:
            result['status'] = 'timeout'
            result['error'] = f'Request timed out after {timeout} seconds'
            result['suggestions'] = [
                'Server may be overloaded or unreachable',
                'Check if the URL is correct',
                'Try again in a few minutes'
            ]
        
        except aiohttp.ClientError as e:
            result['status'] = 'connection_error'
            result['error'] = str(e)
            result['suggestions'] = [
                'Unable to connect to the server',
                'Check if the domain exists',
                'Verify network connectivity'
            ]
        
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        # Add call-to-action
        result['cta'] = {
            'message': 'Want continuous monitoring?',
            'action': 'Sign up for free - monitor 3 services',
            'link': '/signup'
        }
        
        return result
    
    async def _check_http(self, url: str, timeout: int) -> Dict:
        """Perform HTTP request and measure response with safe redirect following"""
        start_time = datetime.utcnow()
        current_url = url
        redirect_count = 0
        max_redirects = 5
        
        async with aiohttp.ClientSession() as session:
            while True:
                # Validate hostname for each hop
                parsed = urlparse(current_url)
                if not await self._is_safe_hostname(parsed.hostname):
                    return {
                        'status_code': 403,
                        'error': 'Forbidden: Access to internal or restricted IP ranges is not allowed.',
                        'healthy': False
                    }
                
                async with session.get(
                    current_url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=False,
                    ssl=False  # We check SSL separately
                ) as response:
                    # Check for redirect
                    if response.status in (301, 302, 303, 307, 308) and redirect_count < max_redirects:
                        location = response.headers.get('Location')
                        if location:
                            current_url = urljoin(current_url, location)
                            redirect_count += 1
                            continue

                    end_time = datetime.utcnow()
                    elapsed_ms = (end_time - start_time).total_seconds() * 1000

                    # Read some content to verify it works
                    content_length = response.headers.get('Content-Length', '0')

                    return {
                        'status_code': response.status,
                        'response_time_ms': round(elapsed_ms, 2),
                        'content_length': int(content_length) if content_length.isdigit() else 0,
                        'headers': {
                            'server': response.headers.get('Server', 'Unknown'),
                            'content_type': response.headers.get('Content-Type', 'Unknown')
                        },
                        'redirected': current_url != url,
                        'final_url': current_url
                    }
    
    async def _check_ssl(self, url: str) -> Dict:
        """Check SSL certificate validity"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            port = parsed.port or 443
            
            # Validate hostname for SSRF
            if not await self._is_safe_hostname(hostname):
                return {
                    'valid': False,
                    'error': 'Forbidden: Access to internal or restricted IP ranges is not allowed.'
                }

            # Create SSL context
            context = ssl.create_default_context()
            
            # Connect and get certificate
            loop = asyncio.get_event_loop()
            
            def get_cert():
                # To prevent DNS rebinding, we resolve once and connect to the IP
                addr_info = socket.getaddrinfo(hostname, port)
                safe_ip = None
                for info in addr_info:
                    ip = info[4][0]
                    addr = ipaddress.ip_address(ip)
                    if not (addr.is_loopback or addr.is_private or addr.is_link_local or
                            addr.is_multicast or addr.is_reserved or addr.is_unspecified):
                        safe_ip = ip
                        break

                if not safe_ip:
                    raise ValueError("No safe public IP address found for host")

                # Use the safe IP but keep original hostname for SNI and cert verification
                with socket.create_connection((safe_ip, port), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        return cert
            
            cert = await loop.run_in_executor(None, get_cert)
            
            # Parse certificate
            not_after = cert.get('notAfter', '')
            not_before = cert.get('notBefore', '')
            issuer = dict(x[0] for x in cert.get('issuer', []))
            
            # Calculate days until expiry
            from datetime import datetime
            expiry_date = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
            days_until_expiry = (expiry_date - datetime.utcnow()).days
            
            return {
                'valid': True,
                'issuer': issuer.get('organizationName', 'Unknown'),
                'expires': not_after,
                'days_until_expiry': days_until_expiry,
                'warning': days_until_expiry < 30
            }
            
        except ssl.SSLError as e:
            return {
                'valid': False,
                'error': 'SSL certificate error',
                'details': str(e)
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def _generate_suggestions(self, result: Dict) -> list:
        """Generate actionable suggestions based on results"""
        suggestions = []
        
        status_code = result.get('status_code', 0)
        response_time = result.get('response_time_ms', 0)
        ssl_info = result.get('ssl', {})
        
        # Status code suggestions
        if status_code >= 500:
            suggestions.append('Server error detected - check server logs')
        elif status_code == 404:
            suggestions.append('Page not found - verify the URL path')
        elif status_code == 403:
            suggestions.append('Access forbidden - check authentication')
        elif status_code == 401:
            suggestions.append('Unauthorized - credentials required')
        elif status_code >= 400:
            suggestions.append(f'Client error (HTTP {status_code}) - check request')
        
        # Response time suggestions
        if response_time > 3000:
            suggestions.append('Very slow response (>3s) - optimize performance')
        elif response_time > 1000:
            suggestions.append('Slow response (>1s) - consider caching')
        elif response_time < 200:
            suggestions.append('Excellent response time!')
        
        # SSL suggestions
        if ssl_info.get('warning'):
            days = ssl_info.get('days_until_expiry', 0)
            suggestions.append(f'SSL certificate expires in {days} days - renew soon')
        elif not ssl_info.get('valid', True):
            suggestions.append('SSL certificate invalid - fix immediately')
        
        # Healthy suggestion
        if result.get('healthy') and not suggestions:
            suggestions.append('Everything looks good! Add to monitoring?')
        
        return suggestions
    
    async def check_multiple(self, urls: list, timeout: int = None) -> list:
        """Check multiple URLs in parallel"""
        tasks = [self.check_url(url, timeout) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [
            r if isinstance(r, dict) else {'url': urls[i], 'error': str(r)}
            for i, r in enumerate(results)
        ]


# FastAPI endpoint
from fastapi import APIRouter, Query

router = APIRouter(tags=["quick-check"])

@router.get("/api/quick-check")
async def quick_check(
    url: str = Query(..., description="URL to check"),
    timeout: int = Query(10, description="Timeout in seconds", le=30)
):
    """
    Instant health check - no signup required
    
    Check any URL and get:
    - HTTP status
    - Response time
    - SSL certificate info
    - Actionable suggestions
    """
    checker = QuickHealthCheck()
    return await checker.check_url(url, timeout)


@router.post("/api/quick-check/batch")
async def quick_check_batch(
    urls: list[str],
    timeout: int = Query(10, le=30)
):
    """Check multiple URLs at once (max 10)"""
    if len(urls) > 10:
        return {"error": "Maximum 10 URLs allowed"}
    
    checker = QuickHealthCheck()
    return await checker.check_multiple(urls, timeout)


# Demo
if __name__ == "__main__":
    async def demo():
        checker = QuickHealthCheck()
        
        # Check a URL
        result = await checker.check_url("https://google.com")
        
        print(f"URL: {result['url']}")
        print(f"Status: {result['status']}")
        print(f"Response Time: {result.get('response_time_ms', 'N/A')}ms")
        print(f"Healthy: {result['healthy']}")
        
        if result.get('ssl'):
            print(f"SSL Valid: {result['ssl'].get('valid')}")
            print(f"SSL Expires: {result['ssl'].get('days_until_expiry')} days")
        
        print("Suggestions:")
        for suggestion in result.get('suggestions', []):
            print(f"  - {suggestion}")
    
    asyncio.run(demo())
