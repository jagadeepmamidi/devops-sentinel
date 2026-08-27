from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from sentinel.cli import auth
from sentinel.cli.auth import build_browser_auth_url
from sentinel.cli.main import cli


def test_init_local_creates_env_without_login(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("SENTINEL_MODE", raising=False)
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["init", "--mode", "local"])
        env_text = Path(".env").read_text(encoding="utf-8")

    assert result.exit_code == 0
    assert "Local mode ready" in result.output
    assert "SENTINEL_MODE=local" in env_text
    assert "No Supabase or login required" in result.output


def test_init_supabase_requires_project_credentials(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("SENTINEL_MODE", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["init", "--mode", "supabase"])

    assert result.exit_code != 0
    assert "--url" in result.output


def test_init_supabase_writes_byo_project(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("SENTINEL_MODE", raising=False)
    config_dir = tmp_path / "cfg"
    config_file = config_dir / "config.json"
    runner = CliRunner()
    with (
        runner.isolated_filesystem(temp_dir=tmp_path / "proj"),
        patch.object(auth, "CONFIG_DIR", config_dir),
        patch.object(auth, "CONFIG_FILE", config_file),
    ):
        result = runner.invoke(
            cli,
            [
                "init",
                "--mode",
                "supabase",
                "--url",
                "https://abc.supabase.co",
                "--anon-key",
                "anon-test-key",
            ],
        )
        env_text = Path(".env").read_text(encoding="utf-8")

    assert result.exit_code == 0, result.output
    assert "YOUR Supabase project" in result.output
    assert "SENTINEL_MODE=supabase" in env_text
    assert "https://abc.supabase.co" in env_text
    assert "anon-test-key" in env_text
    assert "does not store this data" in result.output


def test_login_local_flag_switches_mode(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("SENTINEL_MODE", raising=False)
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(cli, ["login", "--local"])
        env_text = Path(".env").read_text(encoding="utf-8")

    assert result.exit_code == 0
    assert "Local mode enabled" in result.output
    assert "SENTINEL_MODE=local" in env_text


def test_schema_print_contains_core_tables():
    result = CliRunner().invoke(cli, ["schema", "--print"])
    assert result.exit_code == 0
    assert "CREATE TABLE" in result.output
    assert "services" in result.output
    assert "incidents" in result.output


def test_agents_describes_approval_boundary():
    result = CliRunner().invoke(cli, ["agents"])
    assert result.exit_code == 0
    assert "Watcher" in result.output
    assert "Human approval" in result.output


def test_watch_is_monitor_alias():
    result = CliRunner().invoke(cli, ["watch", "--help"])
    assert result.exit_code == 0
    assert "Monitor" in result.output


def test_browser_auth_url_uses_caller_supabase_project(monkeypatch):
    monkeypatch.setenv("SUPABASE_ANON_KEY", "public-anon")
    url = build_browser_auth_url(
        "https://mine.supabase.co",
        "http://localhost:54321/callback",
        web_url="https://docs.example",
        state="abc",
    )
    assert "https://docs.example/cli-auth?" in url
    assert "supabase_url=https%3A%2F%2Fmine.supabase.co" in url
    assert "supabase_anon_key=public-anon" in url
    assert "state=abc" in url


def test_bare_cli_points_at_init_when_unconfigured(monkeypatch):
    monkeypatch.delenv("SENTINEL_MODE", raising=False)
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    result = CliRunner().invoke(cli, [])
    assert result.exit_code == 0
    assert "sentinel init" in result.output
