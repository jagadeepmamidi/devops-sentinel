from sentinel.cli.main import classify_incident


def test_classify_incident_for_unreachable_service():
    severity, detail = classify_incident(None, "timeout")

    assert severity == "critical"
    assert "timeout" in detail


def test_classify_incident_for_server_error():
    severity, detail = classify_incident(503)

    assert severity == "high"
    assert "503" in detail
