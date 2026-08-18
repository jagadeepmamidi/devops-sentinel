from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from sentinel.cli import auth
from sentinel.cli.main import cli


def test_user_config_round_trip_and_masking(tmp_path: Path):
    config_file = tmp_path / "config.json"
    with patch.object(auth, "CONFIG_DIR", tmp_path), patch.object(auth, "CONFIG_FILE", config_file):
        result = CliRunner().invoke(
            cli,
            ["config", "set", "openrouter_api_key", "--value", "sk-test-1234"],
        )
        assert result.exit_code == 0
        assert "sk-test-1234" not in result.output

        listed = CliRunner().invoke(cli, ["config", "list"])
        assert listed.exit_code == 0
        assert "OPENROUTER_API_KEY" in listed.output
        assert "1234" in listed.output
        assert "sk-test-1234" not in listed.output
        assert config_file.exists()

        removed = CliRunner().invoke(cli, ["config", "remove", "openrouter_api_key"])
        assert removed.exit_code == 0
        assert "Removed OPENROUTER_API_KEY" in removed.output


def test_user_config_does_not_override_environment(tmp_path: Path, monkeypatch):
    config_file = tmp_path / "config.json"
    with patch.object(auth, "CONFIG_DIR", tmp_path), patch.object(auth, "CONFIG_FILE", config_file):
        auth.set_user_config("openrouter_api_key", "saved-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "process-key")
        auth.load_user_config_into_env()
        assert auth.user_config_values()["OPENROUTER_API_KEY"] == "saved-key"
        assert __import__("os").environ["OPENROUTER_API_KEY"] == "process-key"
