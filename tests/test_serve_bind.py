from unittest.mock import patch

from click.testing import CliRunner

from sentinel.cli.main import _serve_bind_is_public, cli


def test_localhost_is_not_public_bind():
    assert not _serve_bind_is_public("127.0.0.1")
    assert not _serve_bind_is_public("localhost")
    assert _serve_bind_is_public("0.0.0.0")
    assert _serve_bind_is_public("::")


def test_serve_defaults_to_localhost():
    called = {}

    def fake_call(cmd):
        called["cmd"] = cmd
        return 0

    with patch("sentinel.cli.main.subprocess.call", fake_call):
        result = CliRunner().invoke(cli, ["serve"])

    assert result.exit_code == 0, result.output
    assert called["cmd"][called["cmd"].index("--host") + 1] == "127.0.0.1"
    assert "WARNING" not in result.output
    assert "WARNING" not in result.stderr


def test_serve_warns_when_binding_all_interfaces():
    with patch("sentinel.cli.main.subprocess.call", lambda cmd: 0):
        result = CliRunner().invoke(cli, ["serve", "--host", "0.0.0.0"])

    combined = result.output + result.stderr
    assert result.exit_code == 0, combined
    assert "WARNING" in combined
    assert "0.0.0.0" in combined
    assert "bearer token" in combined
