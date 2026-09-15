import pytest

from sentinel.api.quick_health_check import QuickHealthCheck
from sentinel.tools.custom_health_check_tool import CustomHealthCheckTool


@pytest.mark.asyncio
async def test_quick_check_rejects_loopback():
    result = await QuickHealthCheck().check_url("http://127.0.0.1/")
    assert result["healthy"] is False
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
async def test_sentinel_script_health_checks_are_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SENTINEL_ALLOW_SCRIPT_CHECKS", raising=False)
    result = await CustomHealthCheckTool().execute_script_check({
        "script": "print('OK')",
        "script_type": "python",
    })
    assert result["is_healthy"] is False
    assert "disabled" in result["error"]
