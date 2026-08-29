from fastapi.testclient import TestClient

from sentinel.api.app import create_app
from sentinel.api.mvp_routes import get_request_db
from sentinel.auth.auth_service import get_current_user


class FakeDB:
    def __init__(self):
        self.saved_postmortem = None

    def list_services(self, user_id):
        return [
            {
                "id": "svc-1",
                "name": "API",
                "url": "https://example.com/health",
                "check_interval": 30,
                "is_active": True,
                "last_status": "healthy",
                "last_checked_at": "2026-03-01T10:00:00+00:00",
                "last_response_time_ms": 88,
            }
        ]

    def add_service(self, user_id, name, url, project_id=None, check_interval=30):
        return {
            "id": "svc-2",
            "name": name,
            "url": url,
            "check_interval": check_interval,
            "is_active": True,
            "last_status": "unknown",
            "last_checked_at": None,
            "last_response_time_ms": None,
        }

    def get_service(self, service_id):
        return {"id": service_id, "user_id": "user-1"}

    def delete_service(self, service_id):
        return True

    def list_incidents(self, user_id, limit=50, severity=None, status=None):
        return [
            {
                "id": "inc-1",
                "service_id": "svc-1",
                "status": "detecting",
                "severity": "high",
                "detected_at": "2026-03-01T10:00:00+00:00",
                "resolved_at": None,
                "error_code": 503,
                "error_message": "HTTP 503",
                "action_plan": None,
                "postmortem": None,
                "services": {"name": "API", "url": "https://example.com/health"},
            }
        ]

    def get_incident(self, incident_id):
        return {
            "id": incident_id,
            "user_id": "user-1",
            "service_id": "svc-1",
            "status": "detecting",
            "severity": "high",
            "detected_at": "2026-03-01T10:00:00+00:00",
            "resolved_at": "2026-03-01T10:10:00+00:00",
            "error_code": 503,
            "error_message": "HTTP 503",
            "action_plan": "Rollback deploy",
            "postmortem": None,
            "services": {"name": "API", "url": "https://example.com/health"},
        }

    def list_incident_events(self, incident_id):
        return [
            {
                "id": "evt-1",
                "incident_id": incident_id,
                "service_id": "svc-1",
                "event_type": "detected",
                "description": "HTTP 503",
                "metadata": {"severity": "high"},
                "created_at": "2026-03-01T10:00:00+00:00",
            },
            {
                "id": "evt-2",
                "incident_id": incident_id,
                "service_id": "svc-1",
                "event_type": "resolved",
                "description": "Recovered automatically.",
                "metadata": {},
                "created_at": "2026-03-01T10:10:00+00:00",
            },
        ]

    def save_postmortem(self, incident_id, markdown):
        self.saved_postmortem = (incident_id, markdown)
        return True


def build_client():
    app = create_app()
    fake_db = FakeDB()
    app.dependency_overrides[get_current_user] = lambda: {"id": "user-1", "email": "test@example.com"}
    app.dependency_overrides[get_request_db] = lambda: fake_db
    return TestClient(app), fake_db


def test_list_services_contract():
    client, _ = build_client()

    response = client.get("/api/services")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["services"][0]["last_status"] == "healthy"


def test_generate_postmortem_persists_markdown(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("SENTINEL_LLM_API_KEY", raising=False)
    client, fake_db = build_client()

    response = client.post(
        "/api/postmortems/generate",
        json={"incident_id": "inc-1", "resolution_notes": "Rollback completed"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["incident_id"] == "inc-1"
    assert "Rollback completed" in payload["postmortem"]
    assert fake_db.saved_postmortem[0] == "inc-1"


def test_list_incident_events_returns_stored_timeline():
    client, _ = build_client()

    response = client.get("/api/incidents/inc-1/events")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["events"][0]["event_type"] == "detected"


def test_local_mode_services_require_no_bearer(tmp_path, monkeypatch):
    monkeypatch.setenv("SENTINEL_MODE", "local")
    monkeypatch.setenv("SENTINEL_DATA_DIR", str(tmp_path / ".sentinel"))
    from sentinel.cli.db import reset_db

    reset_db()
    client = TestClient(create_app())
    response = client.get("/api/services")
    assert response.status_code == 200
    assert "services" in response.json()
