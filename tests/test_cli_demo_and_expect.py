import json
from pathlib import Path

import httpx
import pytest
from click.testing import CliRunner

from sentinel.cli.db import reset_db
from sentinel.cli.main import cli
from sentinel.core.demo_server import DemoServer
from sentinel.core.health_spec import HealthExpect, evaluate_expect, json_at
from sentinel.core.monitor_runner import check_url_once
from sentinel.core.project_file import load_project_config, write_sample_project_file
from sentinel.core.supabase_doctor import run_supabase_doctor


@pytest.mark.asyncio
async def test_check_url_once_expect_status_mismatch():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await check_url_once(
            "https://example.test/health",
            client=client,
            expect=HealthExpect(status_codes=(201,)),
        )
    assert result.healthy is False
    assert result.status_code == 200
    assert result.expect_reasons


@pytest.mark.asyncio
async def test_check_url_once_html_page_stays_healthy_with_hint():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html; charset=utf-8"},
            text="<!doctype html><html lang='en'><body>spa</body></html>",
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await check_url_once("https://example.test/api/demo/live/x", client=client)
    assert result.healthy is True
    assert result.status_code == 200
    assert "text/html" in (result.error or "")


@pytest.mark.asyncio
async def test_check_url_once_json_path_and_body():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "ok", "nested": {"ready": True}})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await check_url_once(
            "https://example.test/health",
            client=client,
            expect=HealthExpect(
                status_codes=(200,),
                body_contains="ok",
                json_path="nested.ready",
                json_equals="true",
            ),
        )
    assert result.healthy is True


def test_json_at_nested_and_index():
    data = {"items": [{"ok": True}]}
    assert json_at(data, "items.0.ok") is True


def test_evaluate_expect_default_unhealthy_status():
    result = evaluate_expect(
        status_code=503,
        body="{}",
        url="http://localhost/fail",
        expect=HealthExpect(),
        default_status_healthy=False,
    )
    assert result.healthy is False
    assert result.reasons


def test_load_project_yaml(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    write_sample_project_file(tmp_path)
    config = load_project_config()
    assert config["path"]
    assert config["services"][0]["name"] == "example"
    assert config["services"][0]["expect"].ssl_min_days == 14


def test_load_project_json(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "sentinel.json").write_text(
        json.dumps(
            {
                "services": [
                    {
                        "name": "api",
                        "url": "https://api.example.test/health",
                        "expect": {"status": [200], "body": "ok"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    config = load_project_config()
    assert config["services"][0]["name"] == "api"
    assert config["services"][0]["expect"].body_contains == "ok"


def test_up_without_yaml(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SENTINEL_MODE", "local")
    monkeypatch.setenv("SENTINEL_DATA_DIR", str(tmp_path / "data"))
    reset_db()
    result = CliRunner().invoke(cli, ["up", "--once"])
    assert result.exit_code != 0
    assert "sentinel.yaml" in result.output


def test_supabase_doctor_fails_without_config(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    report = run_supabase_doctor()
    assert report["passed"] is False
    result = CliRunner().invoke(cli, ["supabase", "doctor"])
    assert result.exit_code != 0
    assert "Supabase URL" in result.output


def test_demo_opens_incident(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SENTINEL_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("SENTINEL_MODE", raising=False)
    reset_db()
    result = CliRunner().invoke(cli, ["demo"])
    assert result.exit_code == 0, result.output
    assert "INCIDENT OPENED" in result.output
    assert "HTTP 200" in result.output
    assert "demo-fail" in result.output
    assert "diag=" in result.output
    assert "model=" in result.output


def test_demo_server_ok_and_fail():
    with DemoServer() as server:
        ok = httpx.get(server.ok_url, timeout=5)
        fail = httpx.get(server.fail_url, timeout=5)
    assert ok.status_code == 200
    assert fail.status_code == 503


def test_health_cli_expect_mismatch_exits_one():
    with DemoServer() as server:
        result = CliRunner().invoke(cli, ["health", server.fail_url, "--expect", "200"])
    assert result.exit_code == 1
    assert "diag=" in result.output


def test_health_cli_prints_detect_fields():
    with DemoServer() as server:
        result = CliRunner().invoke(cli, ["health", server.ok_url])
    assert result.exit_code == 0, result.output
    assert "diag=" in result.output
    assert "model=warmup" in result.output
    assert "anomaly=" in result.output


def test_monitor_once_on_demo_ok():
    with DemoServer() as server:
        result = CliRunner().invoke(cli, ["monitor", server.ok_url, "--once", "--timeout", "5"])
    assert result.exit_code == 0, result.output
    assert "HEALTHY" in result.output
    assert "diag=" in result.output
