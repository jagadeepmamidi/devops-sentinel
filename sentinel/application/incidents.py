"""Authenticated incident operations independent of transport adapters."""

from __future__ import annotations

import builtins

from sentinel.cli.db import SentinelDB


class IncidentService:
    """Use shared persistence with explicit user ownership checks."""

    def __init__(self, db: SentinelDB, user_id: str):
        if not user_id:
            raise ValueError("user_id is required")
        self.db = db
        self.user_id = user_id

    def list(
        self, limit: int = 10, severity: str | None = None, status: str | None = None
    ) -> builtins.list[dict]:
        limit = max(1, min(limit, 100))
        return self.db.list_incidents(self.user_id, limit=limit, severity=severity, status=status)

    def get(self, incident_id: str) -> dict | None:
        incident = self.db.get_incident(incident_id)
        if not incident or incident.get("user_id") != self.user_id:
            return None
        return incident

    def events(self, incident_id: str) -> builtins.list[dict] | None:
        if self.get(incident_id) is None:
            return None
        return self.db.list_incident_events(incident_id)
