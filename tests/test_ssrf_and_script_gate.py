import ipaddress
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sentinel.api.quick_health_check import (
    FORBIDDEN_INTERNAL,
    QuickHealthCheck,
    ip_is_public,
    issuer_organization,
)
from sentinel.tools.custom_health_check_tool import CustomHealthCheckTool


class _Aenter:
    def __init__(self, value):
        self.value = value

    async def __aenter__(self):
        return self.value

    async def __aexit__(self, exc_type, exc, tb):
        return False


@pytest.mark.asyncio
async def test_quick_check_rejects_loopback():
    result = await QuickHealthCheck().check_url("http://127.0.0.1/")
    assert result["healthy"] is False
    assert result["status"] == "error"
    assert "Forbidden" in result["error"]


@pytest.mark.asyncio
async def test_quick_check_rejects_localhost():
    result = await QuickHealthCheck().check_url("http://localhost/")
    assert result["healthy"] is False
    assert "Forbidden" in result["error"]


@pytest.mark.asyncio
async def test_quick_check_rejects_non_http_schemes():
    result = await QuickHealthCheck().check_url("file:///etc/passwd")
    assert result["healthy"] is False
    assert "http and https" in result["error"]


@pytest.mark.asyncio
async def test_quick_check_rejects_uppercase_file_scheme():
    result = await QuickHealthCheck().check_url("FILE:///etc/passwd")
    assert result["healthy"] is False
    assert "http and https" in result["error"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url",
    [
        "http://2130706433/",
        "http://127.1/",
        "http://0x7f000001/",
        "http://[::ffff:127.0.0.1]/",
        "http://100.64.0.1/",
        "http://169.254.169.254/",
        "http://example.localhost/",
    ],
)
async def test_quick_check_rejects_ssrf_aliases(url):
    result = await QuickHealthCheck().check_url(url)
    assert result["healthy"] is False
    assert result["status"] == "error"
    assert "Forbidden" in result["error"]


@pytest.mark.asyncio
async def test_quick_check_normalizes_uppercase_http_scheme():
    with patch.object(QuickHealthCheck, "_is_safe_hostname", new_callable=AsyncMock) as safe:
        safe.return_value = True
        with patch.object(QuickHealthCheck, "_check_http", new_callable=AsyncMock) as http:
            http.return_value = {"status_code": 200, "response_time_ms": 10}
            result = await QuickHealthCheck().check_url("HTTP://example.com")
    assert result["url"] == "http://example.com"
    http.assert_awaited()


@pytest.mark.asyncio
async def test_check_http_blocks_redirect_to_loopback():
    mock_response = MagicMock()
    mock_response.status = 302
    mock_response.headers = {"Location": "http://127.0.0.1/admin"}

    mock_session = MagicMock()
    mock_session.get.return_value = _Aenter(mock_response)

    checker = QuickHealthCheck()
    with patch.object(checker, "_is_safe_hostname", new_callable=AsyncMock) as safe:
        safe.side_effect = lambda host: host not in {None, "127.0.0.1"}
        with patch("aiohttp.ClientSession", return_value=_Aenter(mock_session)):
            result = await checker._check_http("http://safe.example", 10)

    assert result["blocked"] is True
    assert FORBIDDEN_INTERNAL in result["error"]
    assert "status_code" not in result


@pytest.mark.asyncio
async def test_check_url_surfaces_redirect_ssrf_as_error_not_http_403():
    checker = QuickHealthCheck()
    with patch.object(checker, "_is_safe_hostname", new_callable=AsyncMock) as safe:
        safe.return_value = True
        with patch.object(checker, "_check_http", new_callable=AsyncMock) as http:
            http.return_value = {"blocked": True, "error": FORBIDDEN_INTERNAL, "healthy": False}
            result = await checker.check_url("https://example.com")

    assert result["status"] == "error"
    assert result["healthy"] is False
    assert "Forbidden" in result["error"]
    assert result.get("status_code") is None


@pytest.mark.asyncio
async def test_check_ssl_rejects_loopback():
    result = await QuickHealthCheck()._check_ssl("https://127.0.0.1")
    assert result["valid"] is False
    assert "Forbidden" in result["error"]


@pytest.mark.asyncio
async def test_sentinel_script_health_checks_are_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SENTINEL_ALLOW_SCRIPT_CHECKS", raising=False)
    result = await CustomHealthCheckTool().execute_script_check({
        "script": "print('OK')",
        "script_type": "python",
    })
    assert result["is_healthy"] is False
    assert "disabled" in result["error"]


def test_ip_is_public_rejects_cgnat_and_embeddings():
    assert ip_is_public(ipaddress.ip_address("8.8.8.8")) is True
    assert ip_is_public(ipaddress.ip_address("100.64.0.1")) is False
    assert ip_is_public(ipaddress.ip_address("::ffff:127.0.0.1")) is False
    assert ip_is_public(ipaddress.ip_address("2002:7f00:1::1")) is False


def test_issuer_organization_reads_getpeercert_rdns():
    cert = {
        "issuer": (
            (("countryName", "US"),),
            (("organizationName", "Let's Encrypt"),),
            (("commonName", "R3"),),
        )
    }
    assert issuer_organization(cert) == "Let's Encrypt"
    assert issuer_organization({"issuer": (("organizationName", "Direct"),)}) == "Direct"
    assert issuer_organization({}) == "Unknown"
