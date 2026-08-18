"""Regression tests for remediation safety controls."""

from unittest.mock import MagicMock

import pytest

from src.core.auto_runbook_executor import AutoRunbookExecutor
from src.tools.custom_health_check_tool import CustomHealthCheckTool


@pytest.fixture
def executor():
    return AutoRunbookExecutor(MagicMock(), approval_required=True)


@pytest.mark.asyncio
async def test_destructive_steps_are_denied_without_explicit_approval(executor):
    result = await executor._execute_step(
        execution_id="exec-1",
        step_number=1,
        step={
            "action_type": "restart_service",
            "params": {"service_name": "api"},
            "destructive": True,
        },
        incident={"service_name": "api"},
        auto_approve=False,
    )

    assert result["status"] == "denied"


def test_command_identifiers_reject_shell_metacharacters(executor):
    with pytest.raises(ValueError):
        executor._safe_identifier("api;whoami", "service name")


@pytest.mark.asyncio
async def test_arbitrary_commands_are_disabled_by_default(executor, monkeypatch):
    monkeypatch.delenv("SENTINEL_ALLOW_ARBITRARY_COMMANDS", raising=False)

    with pytest.raises(PermissionError):
        await executor._run_command("echo unsafe")


@pytest.mark.asyncio
async def test_script_health_checks_are_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SENTINEL_ALLOW_SCRIPT_CHECKS", raising=False)

    result = await CustomHealthCheckTool().execute_script_check({
        "script": "print('OK')",
        "script_type": "python",
    })

    assert result["is_healthy"] is False
    assert "disabled" in result["error"]
