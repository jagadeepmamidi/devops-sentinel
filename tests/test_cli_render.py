"""Focused contracts for the terminal presentation layer."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

from click.testing import CliRunner

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli.main import cli
from src.cli.render import Presentation


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class FakeClient:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return False

    async def get(self, url):
        return self.response


def test_help_describes_output_controls():
    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "local-first SRE monitoring" in result.output
    assert "--json" in result.output
    assert "--plain" in result.output
    assert "--no-color" in result.output


def test_no_command_is_compact_and_has_no_banner():
    result = CliRunner().invoke(cli, [])

    assert result.exit_code == 0
    assert "DevOps Sentinel" in result.output
    assert "====" not in result.output
    assert "--help" in result.output


def test_json_health_is_valid_and_unstyled():
    with patch("src.cli.main.httpx.AsyncClient", return_value=FakeClient(FakeResponse(200))):
        result = CliRunner().invoke(cli, ["--json", "health", "https://example.com/health"])

    payload = json.loads(result.output)
    assert result.exit_code == 0
    assert payload["status"] == "healthy"
    assert "\x1b[" not in result.output


def test_degraded_health_has_action_and_nonzero_exit():
    with patch("src.cli.main.httpx.AsyncClient", return_value=FakeClient(FakeResponse(503))):
        result = CliRunner().invoke(cli, ["--plain", "health", "https://example.com/health"])

    assert result.exit_code == 1
    assert "DEGRADED" in result.output
    assert "HTTP 503" in result.output
    assert "Next:" in result.output
    assert "\x1b[" not in result.output


def test_unreachable_health_explains_recovery():
    class BrokenClient(FakeClient):
        async def get(self, url):
            raise TimeoutError("connection timed out")

    with patch("src.cli.main.httpx.AsyncClient", return_value=BrokenClient(None)):
        result = CliRunner().invoke(cli, ["--no-color", "health", "https://example.com/health"])

    assert result.exit_code == 1
    assert "UNREACHABLE" in result.output
    assert "connection timed out" in result.output
    assert "verify DNS" in result.output


def test_services_empty_state_uses_operator_guidance():
    class EmptyDB:
        connected = True

        def list_services(self, user_id, project=None):
            return []

    with patch("src.cli.services._require_user", return_value={"id": "user-1"}), patch(
        "src.cli.services._require_db", return_value=EmptyDB()
    ):
        result = CliRunner().invoke(cli, ["services", "list"])

    assert result.exit_code == 0
    assert "No monitored services yet." in result.output
    assert "sentinel services add my-api" in result.output


def test_incidents_empty_state_mentions_filters():
    with patch("src.cli.main._logged_in_incidents", return_value=[]):
        result = CliRunner().invoke(cli, ["incidents", "list", "--severity", "P1"])

    assert result.exit_code == 0
    assert "No incidents match the current filters." in result.output
    assert "severity=P1" in result.output


def test_status_keeps_optional_integrations_noncritical():
    with patch.dict(os.environ, {}, clear=True), patch("src.cli.main.httpx.AsyncClient", return_value=FakeClient(FakeResponse(503))), patch(
        "src.cli.main.is_logged_in", return_value=False
    ):
        result = CliRunner().invoke(cli, ["--plain", "status"])

    assert result.exit_code == 0
    assert "Optional integrations" in result.output
    assert "NOT RUNNING" in result.output
    assert "NOT CONFIGURED" in result.output
    assert "FAILED" not in result.output
    assert "✕" not in result.output


def test_setup_assigns_local_identity_saves_key_and_adds_website():
    class LocalDB:
        connected = True

        def add_service(self, user_id, name, url, check_interval=30):
            return {"id": "service-1", "user_id": user_id, "name": name, "url": url, "check_interval": check_interval}

    runner = CliRunner()
    with (
        runner.isolated_filesystem(),
        patch.dict(os.environ, {}, clear=True),
        patch("src.cli.main._settings", return_value=Presentation(interactive=True, no_color=True)),
        patch("src.cli.main.is_logged_in", return_value=False),
        patch(
            "src.cli.main.ensure_default_user",
            return_value={"id": "local-default-user", "email": "local@devops-sentinel"},
        ),
        patch("src.cli.main.save_user_config") as save_config,
        patch("src.cli.main.get_db", return_value=LocalDB()),
        patch(
            "src.cli.main._health_request",
            new=AsyncMock(return_value={"status": "healthy", "healthy": True}),
        ),
    ):
        result = runner.invoke(cli, ["setup"], input="n\nlocal-key\nmy-api\nexample.com\n30\nn\n")

    assert result.exit_code == 0, result.output
    assert "local@devops-sentinel" in result.output
    assert "https://openrouter.ai/keys" in result.output
    assert "OpenRouter key saved securely" in result.output
    assert "Initial health check passed" in result.output
    assert save_config.call_args_list[-1].kwargs == {"OPENROUTER_API_KEY": "local-key", "mode": "local"}


def test_setup_uses_supabase_storage_after_login():
    class SupabaseDB:
        connected = True

        def add_service(self, user_id, name, url, check_interval=30):
            return {"id": "service-1", "user_id": user_id, "name": name, "url": url, "check_interval": check_interval}

    runner = CliRunner()
    with (
        runner.isolated_filesystem(),
        patch.dict(os.environ, {}, clear=True),
        patch("src.cli.main._settings", return_value=Presentation(interactive=True, no_color=True)),
        patch("src.cli.main.is_logged_in", return_value=True),
        patch("src.cli.main.get_current_user", return_value={"id": "supabase-user", "email": "user@example.com"}),
        patch("src.cli.main.save_user_config") as save_config,
        patch("src.cli.main.get_db", return_value=SupabaseDB()),
        patch(
            "src.cli.main._health_request",
            new=AsyncMock(return_value={"status": "healthy", "healthy": True}),
        ),
    ):
        result = runner.invoke(cli, ["setup"], input="supabase-key\nmy-api\nexample.com\n30\nn\n")

    assert result.exit_code == 0, result.output
    assert "Supabase account connected" in result.output
    assert "Registered service in Supabase" in result.output
    assert save_config.call_args_list[-1].kwargs == {"OPENROUTER_API_KEY": "supabase-key", "mode": "supabase"}
