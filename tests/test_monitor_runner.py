from sentinel.core.monitor_runner import MonitorRunner, classify_incident


class FakeMonitorDB:
    connected = True

    def __init__(self):
        self.health_checks = []
        self.status_updates = []
        self.incidents = []
        self.resolved = []
        self._next_id = 1

    def get_active_incident_for_service(self, user_id, service_id):
        return None

    def get_latest_health_checks(self, service_id, limit=3):
        return []

    def log_health_check(self, service_id, status_code, latency_ms, is_healthy, error):
        self.health_checks.append(
            {
                "service_id": service_id,
                "status_code": status_code,
                "is_healthy": is_healthy,
                "error": error,
            }
        )

    def update_service_status(self, service_id, status, latency_ms):
        self.status_updates.append((service_id, status, latency_ms))

    def create_incident(self, user_id, service_id, severity, detail, error_code=None, status="alerting"):
        incident = {
            "id": f"inc-{self._next_id}",
            "user_id": user_id,
            "service_id": service_id,
            "severity": severity,
            "detail": detail,
            "error_code": error_code,
            "status": status,
        }
        self._next_id += 1
        self.incidents.append(incident)
        return incident

    def resolve_incident(self, incident_id):
        self.resolved.append(incident_id)
        return True


class FakeResponse:
    def __init__(self, status_code, text="", content_type="application/json"):
        self.status_code = status_code
        self.text = text
        self.headers = {"content-type": content_type}


class SequenceClient:
    def __init__(self, codes):
        self.codes = list(codes)

    async def get(self, url):
        code = self.codes.pop(0) if self.codes else 200
        return FakeResponse(code, text=f'{{"ok": {code == 200}}}')


def test_classify_incident_maps_status_codes():
    assert classify_incident(None)[0] == "critical"
    assert classify_incident(503)[0] == "high"
    assert classify_incident(404)[0] == "medium"


def test_monitor_runner_does_not_open_before_failure_threshold():
    import asyncio

    async def run():
        db = FakeMonitorDB()
        runner = MonitorRunner(
            url="https://example.com/health",
            db=db,
            user_id="user-1",
            service={"id": "svc-1"},
            failure_threshold=3,
            recovery_threshold=2,
        )
        client = SequenceClient([503, 503])
        first = await runner.check(client)
        second = await runner.check(client)
        return db, first, second

    db, first, second = asyncio.run(run())
    assert first["incident_opened"] is False
    assert second["incident_opened"] is False
    assert db.incidents == []
    assert second["failure_streak"] == 2


def test_monitor_runner_opens_incident_on_threshold():
    import asyncio

    async def run():
        db = FakeMonitorDB()
        runner = MonitorRunner(
            url="https://example.com/health",
            db=db,
            user_id="user-1",
            service={"id": "svc-1"},
            failure_threshold=2,
            recovery_threshold=2,
        )
        client = SequenceClient([503, 503])
        await runner.check(client)
        opened = await runner.check(client)
        return db, opened, runner

    db, opened, runner = asyncio.run(run())
    assert opened["incident_opened"] is True
    assert opened["incident_id"] == "inc-1"
    assert db.incidents[0]["severity"] == "high"
    assert runner.active_incident_id == "inc-1"


def test_monitor_runner_does_not_open_duplicate_while_active():
    import asyncio

    async def run():
        db = FakeMonitorDB()
        runner = MonitorRunner(
            url="https://example.com/health",
            db=db,
            user_id="user-1",
            service={"id": "svc-1"},
            failure_threshold=1,
            recovery_threshold=2,
        )
        client = SequenceClient([503, 503, 503])
        await runner.check(client)
        second = await runner.check(client)
        third = await runner.check(client)
        return db, second, third

    db, second, third = asyncio.run(run())
    assert len(db.incidents) == 1
    assert second["incident_opened"] is False
    assert third["incident_opened"] is False


def test_monitor_runner_resolves_after_recovery_threshold():
    import asyncio

    async def run():
        db = FakeMonitorDB()
        runner = MonitorRunner(
            url="https://example.com/health",
            db=db,
            user_id="user-1",
            service={"id": "svc-1"},
            failure_threshold=1,
            recovery_threshold=2,
        )
        client = SequenceClient([503, 200, 200])
        await runner.check(client)
        recovering = await runner.check(client)
        resolved = await runner.check(client)
        return db, recovering, resolved, runner

    db, recovering, resolved, runner = asyncio.run(run())
    assert recovering["incident_resolved"] is False
    assert resolved["incident_resolved"] is True
    assert db.resolved == ["inc-1"]
    assert runner.active_incident_id is None
