from unittest.mock import MagicMock

from sentinel.cli.db import SentinelDB


def build_mock_client():
    client = MagicMock()
    client.table.return_value = client
    client.select.return_value = client
    client.insert.return_value = client
    client.update.return_value = client
    client.delete.return_value = client
    client.eq.return_value = client
    client.neq.return_value = client
    client.order.return_value = client
    client.limit.return_value = client
    client.execute.return_value = MagicMock(data=[{"id": "inc-1", "detected_at": "2026-03-01T00:00:00+00:00"}])
    return client


def test_update_service_status_uses_mvp_schema_fields():
    client = build_mock_client()
    db = SentinelDB(client=client)

    db.update_service_status("svc-1", "healthy", 123)

    update_payload = client.update.call_args.args[0]
    assert update_payload["last_status"] == "healthy"
    assert update_payload["last_response_time_ms"] == 123
    assert "last_checked_at" in update_payload


def test_save_postmortem_updates_incident_record():
    client = build_mock_client()
    db = SentinelDB(client=client)

    assert db.save_postmortem("inc-1", "# Postmortem") is True
    assert client.update.call_args.args[0] == {"postmortem": "# Postmortem"}


def test_create_incident_writes_detected_event():
    client = build_mock_client()
    db = SentinelDB(client=client)

    db.create_incident("user-1", "svc-1", "high", "HTTP 503", error_code=503, status="alerting")

    insert_payloads = [call.args[0] for call in client.insert.call_args_list]
    assert any(payload.get("service_id") == "svc-1" and payload.get("status") == "alerting" for payload in insert_payloads)
    assert any(payload.get("event_type") == "detected" for payload in insert_payloads)


def test_list_incident_events_uses_incident_events_table():
    client = build_mock_client()
    db = SentinelDB(client=client)

    db.list_incident_events("inc-1")

    assert client.table.call_args.args[0] == "incident_events"
