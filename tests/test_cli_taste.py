"""Contracts for phosphor CLI chrome."""

from click.testing import CliRunner

from sentinel.cli.main import cli
from sentinel.cli.render import check_state, render_check_line, status_lamp
from sentinel.core.demo_server import DemoServer


def test_banner_is_session_not_ascii_box():
    result = CliRunner().invoke(cli, [])
    assert result.exit_code == 0, result.output
    assert "sentinel" in result.output.lower()
    assert "v0.1.7" in result.output
    assert "WELCOME TO DEVOPS SENTINEL" not in result.output
    assert "Observe services" not in result.output
    assert "SSSSSSS" not in result.output
    assert "+-----" not in result.output
    assert "$ sentinel doctor" in result.output or "sentinel doctor" in result.output
    assert "sentinel --help" in result.output


def test_status_lamp_and_check_line_keep_operator_words():
    healthy = render_check_line(
        {
            "healthy": True,
            "status_code": 200,
            "latency_ms": 12,
            "check": 1,
            "diag": "unknown",
            "model_id": "warmup",
            "anomaly_score": None,
        },
        service="site-demo",
    )
    text = healthy.plain
    assert "HEALTHY" in text
    assert "HTTP 200" in text
    assert "site-demo" in text
    assert "diag=unknown" in text
    assert check_state({"healthy": False, "status_code": 503}) == "DEGRADED"
    assert "DEGRADED" in status_lamp("DEGRADED").plain


def test_monitor_once_uses_phosphor_check_line():
    with DemoServer() as server:
        result = CliRunner().invoke(cli, ["monitor", server.ok_url, "--once", "--timeout", "5"])
    assert result.exit_code == 0, result.output
    assert "HEALTHY" in result.output
    assert "HTTP 200" in result.output
    assert "sentinel monitor" in result.output
    assert "diag=" in result.output


def test_demo_incident_card_still_actionable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SENTINEL_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("SENTINEL_MODE", raising=False)
    from sentinel.cli.db import reset_db

    reset_db()
    result = CliRunner().invoke(cli, ["demo"])
    assert result.exit_code == 0, result.output
    assert "INCIDENT OPENED" in result.output
    assert "HTTP 200" in result.output
    assert "demo-fail" in result.output
    assert "sentinel incidents show" in result.output
    assert "sentinel incidents ack" in result.output
