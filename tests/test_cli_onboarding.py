"""Onboarding tests for local identities, provider keys, and local storage."""

import json
import os
from unittest.mock import patch

from src.cli.auth import ensure_default_user, load_local_config_into_env, save_user_config
from src.cli.db import SentinelDB


def test_default_user_and_provider_key_are_persisted_without_exposing_key(tmp_path):
    config_file = tmp_path / "config.json"
    with patch("src.cli.auth.CONFIG_DIR", tmp_path), patch("src.cli.auth.CONFIG_FILE", config_file), patch.dict(os.environ, {}, clear=True):
        user = ensure_default_user()
        save_user_config(OPENROUTER_API_KEY="sk-or-v1-secret", mode="local")
        load_local_config_into_env()

        stored = json.loads(config_file.read_text())
        loaded_key = os.environ["OPENROUTER_API_KEY"]

    assert user["id"] == "local-default-user"
    assert loaded_key == "sk-or-v1-secret"
    assert stored["OPENROUTER_API_KEY"] == "sk-or-v1-secret"


def test_local_storage_can_register_and_check_a_website(tmp_path):
    data_file = tmp_path / "data.json"
    with patch("src.cli.db.CONFIG_DIR", tmp_path), patch("src.cli.db.LOCAL_DATA_FILE", data_file), patch(
        "src.cli.db.load_user_config", return_value={"mode": "local"}
    ), patch("src.cli.db.get_supabase_client", return_value=None):
        db = SentinelDB()
        service = db.add_service("local-default-user", "example", "https://example.com", check_interval=30)
        db.update_service_status(service["id"], "healthy", 120)
        db.log_health_check(service["id"], 200, 120, True)
        services = db.list_services("local-default-user")

    assert db.connected is True
    assert services[0]["url"] == "https://example.com"
    assert services[0]["last_status"] == "healthy"
