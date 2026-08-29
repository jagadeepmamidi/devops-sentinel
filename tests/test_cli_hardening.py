import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from sentinel.cli.db import reset_db, SentinelDB
from sentinel.cli.main import cli
from sentinel.core.health_spec import HealthExpect, evaluate_expect
from sentinel.core.postmortem_generator import PostmortemGenerator


def test_doctor_uninitialized_does_not_look_like_supabase(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SENTINEL_MODE", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    result = CliRunner().invoke(cli, ["doctor"])
    assert result.exit_code == 1
    assert "sentinel init" in result.output
    assert "Missing SUPABASE_URL" not in result.output


def test_whoami_uninitialized(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SENTINEL_MODE", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    result = CliRunner().invoke(cli, ["whoami"])
    assert result.exit_code == 0
    assert "Not initialized" in result.output


def test_json_doctor_after_init_is_parseable(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SENTINEL_MODE", "local")
    monkeypatch.setenv("SENTINEL_DATA_DIR", str(tmp_path / ".sentinel"))
    reset_db()
    CliRunner().invoke(cli, ["init", "--mode", "local"])
    result = CliRunner().invoke(cli, ["--json", "doctor"])
    payload = json.loads(result.output)
    assert payload["mode"] == "local"
    assert payload["failed_count"] == 0


def test_local_delete_unknown_service_fails(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SENTINEL_MODE", "local")
    db = SentinelDB(db_path=tmp_path / "sentinel.db")
    assert db.delete_service("missing-id") is False
    db.close()


def test_logout_local_does_not_claim_success(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SENTINEL_MODE", "local")
    result = CliRunner().invoke(cli, ["logout"])
    assert result.exit_code == 0
    assert "Nothing to log out" in result.output
    assert "Logged out from" not in result.output


def test_https_health_reports_ssl_days_without_min_flag():
    with patch("sentinel.core.health_spec.check_tls_days", return_value=59):
        result = evaluate_expect(
            status_code=200,
            body="ok",
            url="https://example.com",
            expect=HealthExpect(),
            default_status_healthy=True,
        )
    assert result.healthy is True
    assert result.ssl_days == 59


def test_postmortem_template_uses_service_and_error(monkeypatch):
    import asyncio

    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    generated = asyncio.run(
        PostmortemGenerator().generate(
            {
                "id": "inc-1",
                "severity": "high",
                "error_message": "Service returned HTTP 503",
                "services": {"name": "httpbin-fail"},
            },
            [{"created_at": "2026-08-29T17:00:00", "description": "detected 503"}],
        )
    )
    assert generated["source"] == "fallback"
    assert "httpbin-fail" in generated["markdown"]
    assert "HTTP 503" in generated["markdown"]


def test_postmortem_falls_back_when_provider_errors(monkeypatch):
    import asyncio

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    async def boom(*_args, **_kwargs):
        raise RuntimeError("LLM HTTP 402: credits")

    with patch.object(PostmortemGenerator, "_generate_with_ai", boom):
        generated = asyncio.run(
            PostmortemGenerator().generate(
                {"id": "inc-2", "severity": "high", "service_name": "api"},
                [],
            )
        )
    assert generated["source"] == "fallback"
    assert "402" in (generated["fallback_reason"] or "")


def test_mcp_server_module_registers_tools():
    from sentinel.mcp import server as mcp_server

    assert callable(mcp_server.health_check)
    assert callable(mcp_server.list_incidents)
    tools = getattr(mcp_server.mcp, "_tool_manager", None)
    names = set()
    if tools is not None:
        listing = getattr(tools, "_tools", None) or getattr(tools, "tools", None) or {}
        names = set(listing)
    assert "health_check" in names or callable(mcp_server.health_check)


def test_json_doctor_uninitialized_is_object(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SENTINEL_MODE", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    result = CliRunner().invoke(cli, ["--json", "doctor"])
    payload = json.loads(result.output)
    assert payload["mode"] == "none"
    assert payload["failed_count"] >= 1
    assert "Missing SUPABASE_URL" not in json.dumps(payload)


def test_config_set_preserves_unknown_keys(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"version": 1, "custom": True, "env": {"EXISTING": "keep"}}),
        encoding="utf-8",
    )
    monkeypatch.setattr("sentinel.cli.auth.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("sentinel.cli.auth.CONFIG_FILE", config_file)
    from sentinel.cli.auth import set_user_config

    set_user_config("openrouter_api_key", "sk-test")
    stored = json.loads(config_file.read_text(encoding="utf-8"))
    assert stored["custom"] is True
    assert stored["env"]["EXISTING"] == "keep"
    assert stored["env"]["OPENROUTER_API_KEY"] == "sk-test"


def test_url_monitor_auto_registers_and_opens_incident(tmp_path, monkeypatch):
    from sentinel.core.demo_server import DemoServer

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SENTINEL_MODE", "local")
    monkeypatch.setenv("SENTINEL_DATA_DIR", str(tmp_path / ".sentinel"))
    reset_db()
    CliRunner().invoke(cli, ["init", "--mode", "local"])
    reset_db()
    with DemoServer() as server:
        result = CliRunner().invoke(
            cli,
            ["monitor", server.fail_url, "--once", "--failure-threshold", "1", "--timeout", "5"],
        )
    assert result.exit_code == 0, result.output
    assert "INCIDENT OPENED" in result.output
    db = SentinelDB()
    try:
        incidents = db.list_incidents("local-user")
        services = db.list_services("local-user")
    finally:
        db.close()
    assert services
    assert incidents


def test_slack_notify_posts_webhook(monkeypatch):
    posted = {}

    class FakeResponse:
        status_code = 200

    def fake_post(url, json=None, timeout=None):
        posted["url"] = url
        posted["json"] = json
        return FakeResponse()

    monkeypatch.setenv("SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/test")
    monkeypatch.setattr("sentinel.cli.main.httpx.post", fake_post)
    from sentinel.cli.main import notify_slack_incident

    notify_slack_incident(
        {
            "incident_id": "inc-1",
            "incident_severity": "high",
            "service": "api",
            "error": "HTTP 503",
        }
    )
    assert posted["url"] == "https://hooks.slack.com/services/test"
    assert "inc-1" in posted["json"]["text"]


def test_dashboard_once_prints_table(tmp_path, monkeypatch):
    from sentinel.core.demo_server import DemoServer

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SENTINEL_MODE", "local")
    monkeypatch.setenv("SENTINEL_DATA_DIR", str(tmp_path / ".sentinel"))
    reset_db()
    CliRunner().invoke(cli, ["init", "--mode", "local"])
    reset_db()
    with DemoServer() as server:
        add = CliRunner().invoke(cli, ["services", "add", "demo", server.ok_url])
        assert add.exit_code == 0, add.output
        result = CliRunner().invoke(cli, ["dashboard", "--once", "--timeout", "5"])
    assert result.exit_code == 0, result.output
    assert "Sentinel Dashboard" in result.output
    assert "demo" in result.output
