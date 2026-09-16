"""Quick Health Check - Viral Feature for Instant Value"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import aiohttp
from fastapi import APIRouter, Query

FORBIDDEN_INTERNAL = "Forbidden: Access to internal or restricted IP ranges is not allowed."
FORBIDDEN_SCHEME = "Forbidden: Only http and https URLs are allowed."


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ip_is_public(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True only for globally routable addresses, including unwrapped IPv6 embeddings."""
    if isinstance(addr, ipaddress.IPv6Address):
        if addr.ipv4_mapped is not None:
            return ip_is_public(addr.ipv4_mapped)
        if addr.sixtofour is not None:
            return ip_is_public(addr.sixtofour)
        teredo = addr.teredo
        if teredo is not None:
            return ip_is_public(teredo[0]) and ip_is_public(teredo[1])
    return bool(addr.is_global)


def issuer_organization(cert: dict) -> str:
    """Read organizationName from ssl.getpeercert() issuer RDNs."""
    issuer: dict[str, str] = {}
    issuer_entries = cert.get("issuer", ())
    if not isinstance(issuer_entries, (list, tuple)):
        return "Unknown"
    for rdn in issuer_entries:
        pair = rdn
        if isinstance(rdn, (list, tuple)) and rdn and isinstance(rdn[0], (list, tuple)):
            pair = rdn[0]
        if (
            isinstance(pair, (list, tuple))
            and len(pair) == 2
            and isinstance(pair[0], str)
            and isinstance(pair[1], str)
        ):
            issuer[pair[0]] = pair[1]
    return issuer.get("organizationName", "Unknown")


class QuickHealthCheck:
    """Instant health check for any URL."""

    DEFAULT_TIMEOUT = 10  # seconds
    _BLOCKED_HOSTS = {"localhost", "0.0.0.0", "::1", "metadata.google.internal"}

    async def _is_safe_hostname(self, hostname: str | None) -> bool:
        """Reject loopback, private, link-local, CGNAT, and other non-public IPs."""
        if not hostname:
            return False
        normalized = hostname.lower().rstrip(".")
        if normalized in self._BLOCKED_HOSTS or normalized.endswith(".localhost"):
            return False
        try:
            loop = asyncio.get_running_loop()
            addr_info = await loop.run_in_executor(None, lambda: socket.getaddrinfo(hostname, None))
            if not addr_info:
                return False
            return all(ip_is_public(ipaddress.ip_address(info[4][0])) for info in addr_info)
        except (OSError, ValueError):
            return False

    def _forbidden_result(self, url: str, error: str) -> dict:
        return {
            "url": url,
            "checked_at": _utc_now().isoformat(),
            "status": "error",
            "error": error,
            "healthy": False,
            "suggestions": ["Please provide a valid public URL"],
            "cta": self._cta(),
        }

    @staticmethod
    def _cta() -> dict:
        return {
            "message": "Want continuous monitoring?",
            "action": "Sign up for free - monitor 3 services",
            "link": "/signup",
        }

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
        scheme, separator, rest = url.partition("://")
        if separator:
            if scheme.lower() not in {"http", "https"}:
                return self._forbidden_result(url, FORBIDDEN_SCHEME)
            url = f"{scheme.lower()}://{rest}"
        else:
            url = f"https://{url}"

        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not await self._is_safe_hostname(
            parsed.hostname
        ):
            return self._forbidden_result(url, FORBIDDEN_INTERNAL)

        result = {
            "url": url,
            "checked_at": _utc_now().isoformat(),
            "status": "unknown",
            "healthy": False,
        }

        try:
            http_result = await self._check_http(url, timeout_seconds)
            if http_result.get("blocked"):
                return self._forbidden_result(url, str(http_result.get("error") or FORBIDDEN_INTERNAL))
            result.update(http_result)

            if url.startswith("https://"):
                ssl_result = await self._check_ssl(url)
                result["ssl"] = ssl_result
                if "Forbidden" in str(ssl_result.get("error", "")):
                    return self._forbidden_result(url, str(ssl_result.get("error") or FORBIDDEN_INTERNAL))

            result["healthy"] = result.get("status_code", 0) in range(200, 400) and result.get(
                "ssl", {}
            ).get("valid", True)

            result["status"] = "healthy" if result["healthy"] else "unhealthy"
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

        result["cta"] = self._cta()
        return result

    async def _check_http(self, url: str, timeout: int) -> dict:
        """Perform HTTP request and measure response with safe redirect following."""
        start_time = _utc_now()
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
                        "blocked": True,
                        "error": FORBIDDEN_INTERNAL,
                        "healthy": False,
                    }

                async with session.get(
                    current_url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=False,
                    ssl=False,  # HTTP reachability is measured separately from cert validity.
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

                    elapsed_ms = (_utc_now() - start_time).total_seconds() * 1000
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
        """Check SSL certificate validity by connecting to an already-validated public IP."""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            port = parsed.port or 443

            if not await self._is_safe_hostname(hostname):
                return {
                    "valid": False,
                    "error": FORBIDDEN_INTERNAL,
                }

            context = ssl.create_default_context()
            loop = asyncio.get_running_loop()

            def get_cert() -> dict[str, object]:
                addr_info = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
                safe_ip = None
                for info in addr_info:
                    addr = ipaddress.ip_address(info[4][0])
                    if ip_is_public(addr):
                        safe_ip = info[4][0]
                        break
                if not safe_ip:
                    raise ValueError("No safe public IP address found for host")

                with (
                    socket.create_connection((safe_ip, port), timeout=5) as sock,
                    context.wrap_socket(sock, server_hostname=hostname) as ssock,
                ):
                    cert = ssock.getpeercert()
                    return dict(cert or {})

            cert = await loop.run_in_executor(None, get_cert)
            not_after = str(cert.get("notAfter", ""))
            normalized_expiry = not_after.replace(" GMT", " +0000")
            expiry_date = datetime.strptime(normalized_expiry, "%b %d %H:%M:%S %Y %z")
            days_until_expiry = (expiry_date - _utc_now()).days

            return {
                "valid": True,
                "issuer": issuer_organization(cert),
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

        if response_time > 3000:
            suggestions.append("Very slow response (>3s) - optimize performance")
        elif response_time > 1000:
            suggestions.append("Slow response (>1s) - consider caching")
        elif response_time < 200:
            suggestions.append("Excellent response time!")

        if ssl_info.get("warning"):
            days = ssl_info.get("days_until_expiry", 0)
            suggestions.append(f"SSL certificate expires in {days} days - renew soon")
        elif not ssl_info.get("valid", True):
            suggestions.append("SSL certificate invalid - fix immediately")

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
