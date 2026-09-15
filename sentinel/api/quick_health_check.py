"""Quick Health Check - Viral Feature for Instant Value"""

import asyncio
import ipaddress
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import aiohttp


class QuickHealthCheck:
    """Instant health check for any URL."""

    DEFAULT_TIMEOUT = 10  # seconds
    _BLOCKED_HOSTS = {"localhost", "0.0.0.0", "::1", "metadata.google.internal"}

    async def _is_safe_hostname(self, hostname: str | None) -> bool:
        """Reject loopback, private, link-local, and other non-public resolved IPs."""
        if not hostname:
            return False
        if hostname.lower().rstrip(".") in self._BLOCKED_HOSTS:
            return False
        try:
            loop = asyncio.get_running_loop()
            addr_info = await loop.run_in_executor(None, lambda: socket.getaddrinfo(hostname, None))
            for info in addr_info:
                addr = ipaddress.ip_address(info[4][0])
                if (
                    addr.is_loopback
                    or addr.is_private
                    or addr.is_link_local
                    or addr.is_multicast
                    or addr.is_reserved
                    or addr.is_unspecified
                ):
                    return False
            return True
        except (OSError, ValueError):
            return False

    async def check_url(self, url: str, timeout: int | None = None) -> dict:
        """
        Perform instant health check on URL

        Args:
            url: URL to check (with or without protocol)
            timeout: Custom timeout in seconds

        Returns:
            Complete health check result
        """
        timeout_seconds: int = timeout if timeout is not None else self.DEFAULT_TIMEOUT

        if "://" in url and not url.startswith(("http://", "https://")):
            return {
                "url": url,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "status": "error",
                "error": "Forbidden: Only http and https URLs are allowed.",
                "healthy": False,
                "suggestions": ["Please provide a valid public URL"],
            }

        # Normalize URL
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not await self._is_safe_hostname(
            parsed.hostname
        ):
            return {
                "url": url,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "status": "error",
                "error": "Forbidden: Access to internal or restricted IP ranges is not allowed.",
                "healthy": False,
                "suggestions": ["Please provide a valid public URL"],
            }

        result = {
            "url": url,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "status": "unknown",
            "healthy": False,
        }

        try:
            # Perform HTTP check
            http_result = await self._check_http(url, timeout_seconds)
            result.update(http_result)

            # Check SSL if HTTPS
            if url.startswith("https://"):
                ssl_result = await self._check_ssl(url)
                result["ssl"] = ssl_result

            # Determine overall health
            result["healthy"] = result.get("status_code", 0) in range(200, 400) and result.get(
                "ssl", {}
            ).get("valid", True)

            result["status"] = "healthy" if result["healthy"] else "unhealthy"

            # Generate suggestions
            result["suggestions"] = self._generate_suggestions(result)

        except asyncio.TimeoutError:
            result["status"] = "timeout"
            result["error"] = f"Request timed out after {timeout_seconds} seconds"
            result["suggestions"] = [
                "Server may be overloaded or unreachable",
                "Check if the URL is correct",
                "Try again in a few minutes",
            ]

        except aiohttp.ClientError as e:
            result["status"] = "connection_error"
            result["error"] = str(e)
            result["suggestions"] = [
                "Unable to connect to the server",
                "Check if the domain exists",
                "Verify network connectivity",
            ]

        except (OSError, ValueError, TypeError) as e:
            result["status"] = "error"
            result["error"] = str(e)

        # Add call-to-action
        result["cta"] = {
            "message": "Want continuous monitoring?",
            "action": "Sign up for free - monitor 3 services",
            "link": "/signup",
        }

        return result

    async def _check_http(self, url: str, timeout: int) -> dict:
        """Perform HTTP request and measure response with safe redirect following."""
        start_time = datetime.now(timezone.utc)
        current_url = url
        redirect_count = 0
        max_redirects = 5

        async with aiohttp.ClientSession() as session:
            while True:
                parsed = urlparse(current_url)
                if parsed.scheme not in {"http", "https"} or not await self._is_safe_hostname(
                    parsed.hostname
                ):
                    return {
                        "status_code": 403,
                        "error": "Forbidden: Access to internal or restricted IP ranges is not allowed.",
                        "healthy": False,
                    }

                async with session.get(
                    current_url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=False,
                    ssl=False,
                ) as response:
                    if (
                        response.status in (301, 302, 303, 307, 308)
                        and redirect_count < max_redirects
                    ):
                        location = response.headers.get("Location")
                        if location:
                            current_url = urljoin(current_url, location)
                            redirect_count += 1
                            continue

                    end_time = datetime.now(timezone.utc)
                    elapsed_ms = (end_time - start_time).total_seconds() * 1000
                    content_length = str(response.headers.get("Content-Length", "0"))
                    try:
                        content_length_value = int(content_length)
                    except (TypeError, ValueError):
                        content_length_value = 0

                    return {
                        "status_code": response.status,
                        "response_time_ms": round(elapsed_ms, 2),
                        "content_length": content_length_value,
                        "headers": {
                            "server": response.headers.get("Server", "Unknown"),
                            "content_type": response.headers.get("Content-Type", "Unknown"),
                        },
                        "redirected": current_url != url,
                        "final_url": current_url,
                    }

    async def _check_ssl(self, url: str) -> dict:
        """Check SSL certificate validity"""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            port = parsed.port or 443

            if not await self._is_safe_hostname(hostname):
                return {
                    "valid": False,
                    "error": "Forbidden: Access to internal or restricted IP ranges is not allowed.",
                }

            # Create SSL context
            context = ssl.create_default_context()

            # Connect and get certificate
            loop = asyncio.get_event_loop()

            def get_cert() -> dict[str, object]:
                with (
                    socket.create_connection((hostname, port), timeout=5) as sock,
                    context.wrap_socket(sock, server_hostname=hostname) as ssock,
                ):
                    cert = ssock.getpeercert()
                    return dict(cert or {})

            cert = await loop.run_in_executor(None, get_cert)

            # Parse certificate
            not_after = str(cert.get("notAfter", ""))
            issuer_entries = cert.get("issuer", [])
            issuer: dict[str, str] = {}
            if isinstance(issuer_entries, (list, tuple)):
                for item in issuer_entries:
                    if (
                        isinstance(item, (list, tuple))
                        and len(item) == 2
                        and isinstance(item[0], str)
                        and isinstance(item[1], str)
                    ):
                        issuer[item[0]] = item[1]

            normalized_expiry = not_after.replace(" GMT", " +0000")
            expiry_date = datetime.strptime(normalized_expiry, "%b %d %H:%M:%S %Y %z")
            days_until_expiry = (expiry_date - datetime.now(timezone.utc)).days

            return {
                "valid": True,
                "issuer": issuer.get("organizationName", "Unknown"),
                "expires": not_after,
                "days_until_expiry": days_until_expiry,
                "warning": days_until_expiry < 30,
            }

        except ssl.SSLError as e:
            return {"valid": False, "error": "SSL certificate error", "details": str(e)}
        except (OSError, TypeError, ValueError) as e:
            return {"valid": False, "error": str(e)}

    def _generate_suggestions(self, result: dict) -> list:
        """Generate actionable suggestions based on results"""
        suggestions = []

        status_code = result.get("status_code", 0)
        response_time = result.get("response_time_ms", 0)
        ssl_info = result.get("ssl", {})

        # Status code suggestions
        if status_code >= 500:
            suggestions.append("Server error detected - check server logs")
        elif status_code == 404:
            suggestions.append("Page not found - verify the URL path")
        elif status_code == 403:
            suggestions.append("Access forbidden - check authentication")
        elif status_code == 401:
            suggestions.append("Unauthorized - credentials required")
        elif status_code >= 400:
            suggestions.append(f"Client error (HTTP {status_code}) - check request")

        # Response time suggestions
        if response_time > 3000:
            suggestions.append("Very slow response (>3s) - optimize performance")
        elif response_time > 1000:
            suggestions.append("Slow response (>1s) - consider caching")
        elif response_time < 200:
            suggestions.append("Excellent response time!")

        # SSL suggestions
        if ssl_info.get("warning"):
            days = ssl_info.get("days_until_expiry", 0)
            suggestions.append(f"SSL certificate expires in {days} days - renew soon")
        elif not ssl_info.get("valid", True):
            suggestions.append("SSL certificate invalid - fix immediately")

        # Healthy suggestion
        if result.get("healthy") and not suggestions:
            suggestions.append("Everything looks good! Add to monitoring?")

        return suggestions

    async def check_multiple(self, urls: list, timeout: int | None = None) -> list:
        """Check multiple URLs in parallel"""
        timeout_seconds = timeout if timeout is not None else self.DEFAULT_TIMEOUT
        tasks = [self.check_url(url, timeout_seconds) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            r if isinstance(r, dict) else {"url": urls[i], "error": str(r)}
            for i, r in enumerate(results)
        ]


# FastAPI endpoint
from fastapi import APIRouter, Query

router = APIRouter(tags=["quick-check"])


@router.get("/api/quick-check")
async def quick_check(
    url: str = Query(..., description="URL to check"),
    timeout: int = Query(10, description="Timeout in seconds", le=30),
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
async def quick_check_batch(urls: list[str], timeout: int = Query(10, le=30)):
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

        if result.get("ssl"):
            print(f"SSL Valid: {result['ssl'].get('valid')}")
            print(f"SSL Expires: {result['ssl'].get('days_until_expiry')} days")

        print("Suggestions:")
        for suggestion in result.get("suggestions", []):
            print(f"  - {suggestion}")

    asyncio.run(demo())
