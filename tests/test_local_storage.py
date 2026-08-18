from pathlib import Path

from sentinel.cli.auth import get_current_user, get_storage_mode, is_logged_in
from sentinel.cli.db import SentinelDB


def test_local_storage_round_trip(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SENTINEL_MODE", "local")
    db = SentinelDB(db_path=tmp_path / "sentinel.db")

    assert db.connected
    assert db.local
    user = get_current_user()
    assert get_storage_mode() == "local"
    assert is_logged_in()
    assert user is not None
    assert user["id"] == "local-user"

    project = db.create_project(user["id"], "production", "Primary services")
    assert project is not None
    service = db.add_service(user["id"], "api", "https://example.com/health", project["id"], 30)
    assert project["name"] == "production"
    assert service is not None
    assert service["project_id"] == project["id"]
    assert db.list_services(user["id"])[0]["url"] == "https://example.com/health"

    db.log_health_check(service["id"], 503, 120, False, "upstream unavailable")
    incident = db.create_incident(user["id"], service["id"], "high", "HTTP 503", 503, "alerting")
    active_incident = db.get_active_incident_for_service(user["id"], service["id"])
    assert incident is not None
    assert active_incident is not None
    assert active_incident["id"] == incident["id"]
    assert db.list_incident_events(incident["id"])[0]["event_type"] == "detected"

    assert db.resolve_incident(incident["id"], "Service recovered")
    resolved_incident = db.get_incident(incident["id"])
    assert resolved_incident is not None
    assert resolved_incident["status"] == "resolved"
    db.close()


def test_local_mode_does_not_open_supabase(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("SENTINEL_MODE", "local")
    monkeypatch.setenv("SUPABASE_URL", "https://unused.example")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "unused")
    db = SentinelDB(db_path=tmp_path / "local.db")
    assert db.local
    assert db.client is None
    db.close()
