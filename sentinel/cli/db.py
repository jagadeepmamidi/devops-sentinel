"""Storage adapter for DevOps Sentinel CLI and API layers.

SQLite is used in local mode. Supabase remains available as an optional
compatibility backend when ``SENTINEL_MODE=supabase`` or Supabase variables
are configured.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

# Supabase stays optional and lazy: local CLI startup must not import its Pydantic stack.
Client = Any
SUPABASE_AVAILABLE = False

from .auth import get_storage_mode, load_credentials


def get_supabase_client(
    access_token: str | None = None,
    refresh_token: str | None = None,
) -> Any:
    """Create a Supabase client when compatibility mode is configured."""
    if get_storage_mode() != "supabase":
        return None
    try:
        from supabase import create_client
    except ImportError:
        return None

    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not anon_key:
        return None

    client = create_client(url, anon_key)
    creds = load_credentials() or {}
    token = access_token or creds.get("access_token")
    token_refresh = refresh_token or creds.get("refresh_token")
    if token:
        try:
            if token_refresh:
                client.auth.set_session(token, token_refresh)
            else:
                client.postgrest.auth(token)
        except (AttributeError, RuntimeError, TypeError, ValueError):
            try:
                client.postgrest.auth(token)
            except (AttributeError, RuntimeError, TypeError, ValueError):
                return client
    return client


def get_local_db_path() -> Path:
    """Return configured SQLite path, creating no files as a side effect."""
    explicit = os.getenv("SENTINEL_DB_PATH")
    if explicit:
        return Path(explicit).expanduser()

    data_dir = os.getenv("SENTINEL_DATA_DIR")
    if data_dir:
        return Path(data_dir).expanduser() / "sentinel.db"

    if os.name == "nt":
        root = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        root = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / "sentinel" / "sentinel.db"


LOCAL_USER_ID = "local-user"


class SentinelDB:
    """Database operations shared by CLI and API layers."""

    def __init__(
        self,
        access_token: str | None = None,
        refresh_token: str | None = None,
        client: Any = None,
        db_path: Path | str | None = None,
    ):
        self.client = client or get_supabase_client(access_token, refresh_token)
        self._sqlite: sqlite3.Connection | None = None
        self.path: Path | None = None
        if client is None and self.client is None and get_storage_mode() == "local":
            self.path = Path(db_path).expanduser() if db_path else get_local_db_path()
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._sqlite = sqlite3.connect(str(self.path), check_same_thread=False)
            self._sqlite.row_factory = sqlite3.Row
            self._initialize_sqlite()

    @property
    def connected(self) -> bool:
        return self.client is not None or self._sqlite is not None

    @property
    def local(self) -> bool:
        return self._sqlite is not None

    def close(self) -> None:
        if self._sqlite:
            self._sqlite.close()
            self._sqlite = None

    def _connection(self) -> sqlite3.Connection:
        assert self._sqlite is not None
        return self._sqlite

    def _execute(self, builder: Any) -> Any:
        return builder.execute() if builder is not None else None

    def _initialize_sqlite(self) -> None:
        assert self._sqlite is not None
        self._sqlite.executescript(
            """
            PRAGMA foreign_keys = ON;
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, name TEXT NOT NULL,
                description TEXT DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS services (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, project_id TEXT,
                name TEXT NOT NULL, url TEXT NOT NULL, check_interval INTEGER NOT NULL DEFAULT 30,
                is_active INTEGER NOT NULL DEFAULT 1, last_status TEXT DEFAULT 'unknown',
                last_response_time_ms REAL, last_checked_at TEXT, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_local_services_user ON services(user_id);
            CREATE TABLE IF NOT EXISTS incidents (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, service_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'detecting', severity TEXT NOT NULL DEFAULT 'medium',
                error_code INTEGER, error_message TEXT, detected_at TEXT NOT NULL,
                resolved_at TEXT, mttr_seconds REAL, investigation_report TEXT,
                action_plan TEXT, postmortem TEXT, created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_local_incidents_user ON incidents(user_id);
            CREATE INDEX IF NOT EXISTS idx_local_incidents_status ON incidents(status);
            CREATE TABLE IF NOT EXISTS health_checks (
                id TEXT PRIMARY KEY, service_id TEXT NOT NULL, status_code INTEGER,
                response_time_ms REAL, is_healthy INTEGER NOT NULL, error_message TEXT,
                checked_at TEXT NOT NULL, diag TEXT, anomaly_score REAL, model_id TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_local_checks_service ON health_checks(service_id, checked_at DESC);
            CREATE TABLE IF NOT EXISTS incident_events (
                id TEXT PRIMARY KEY, user_id TEXT NOT NULL, incident_id TEXT NOT NULL,
                service_id TEXT NOT NULL, event_type TEXT NOT NULL, description TEXT NOT NULL,
                metadata TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_local_events_incident ON incident_events(incident_id, created_at);
            """
        )
        self._migrate_sqlite()
        self._sqlite.commit()

    def _migrate_sqlite(self) -> None:
        """Add columns introduced after the original local schema."""
        assert self._sqlite is not None
        columns = {
            row[1] for row in self._connection().execute("PRAGMA table_info(health_checks)")
        }
        if "diag" not in columns:
            self._connection().execute("ALTER TABLE health_checks ADD COLUMN diag TEXT")
        if "anomaly_score" not in columns:
            self._connection().execute("ALTER TABLE health_checks ADD COLUMN anomaly_score REAL")
        if "model_id" not in columns:
            self._connection().execute("ALTER TABLE health_checks ADD COLUMN model_id TEXT")

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

    @staticmethod
    def _dict(row: sqlite3.Row | None) -> dict | None:
        return dict(row) if row else None

    def _execute_sql(self, query: str, params: tuple = ()):
        """Execute SQL with bound parameters; callers supply constant SQL."""
        assert self._sqlite is not None
        connection = self._sqlite
        return connection.execute(query, params)  # nosec B608

    def _rows(self, query: str, params: tuple = ()) -> list[dict]:
        assert self._sqlite is not None
        return [dict(row) for row in self._execute_sql(query, params).fetchall()]

    def _row(self, query: str, params: tuple = ()) -> dict | None:
        assert self._sqlite is not None
        return self._dict(self._connection().execute(query, params).fetchone())

    def _commit(self) -> None:
        assert self._sqlite is not None
        self._sqlite.commit()

    def list_projects(self, user_id: str) -> list[dict]:
        if self.local:
            return self._rows(
                "SELECT * FROM projects WHERE user_id=? ORDER BY created_at DESC", (user_id,)
            )
        if not self.client:
            return []
        result = self._execute(
            self.client.table("projects")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )
        return result.data or []

    def create_project(self, user_id: str, name: str, description: str = "") -> dict | None:
        if self.local:
            now = self._now()
            item = {
                "id": str(uuid4()),
                "user_id": user_id,
                "name": name,
                "description": description,
                "created_at": now,
                "updated_at": now,
            }
            self._connection().execute(
                "INSERT INTO projects VALUES (:id,:user_id,:name,:description,:created_at,:updated_at)",
                item,
            )
            self._commit()
            return item
        if not self.client:
            return None
        result = self._execute(
            self.client.table("projects").insert(
                {"user_id": user_id, "name": name, "description": description}
            )
        )
        return result.data[0] if result and result.data else None

    def delete_project(self, project_id: str) -> bool:
        if self.local:
            self._connection().execute("DELETE FROM projects WHERE id=?", (project_id,))
            self._commit()
            return True
        if not self.client:
            return False
        self._execute(self.client.table("projects").delete().eq("id", project_id))
        return True

    def list_services(self, user_id: str, project_id: str | None = None) -> list[dict]:
        if self.local:
            if project_id:
                return self._rows(
                    "SELECT * FROM services WHERE user_id=? AND project_id=? ORDER BY created_at DESC",
                    (user_id, project_id),
                )
            return self._rows(
                "SELECT * FROM services WHERE user_id=? ORDER BY created_at DESC", (user_id,)
            )
        if not self.client:
            return []
        query = self.client.table("services").select("*").eq("user_id", user_id)
        if project_id:
            query = query.eq("project_id", project_id)
        result = self._execute(query.order("created_at", desc=True))
        return result.data or []

    def get_service(self, service_id: str) -> dict | None:
        if self.local:
            return self._row("SELECT * FROM services WHERE id=?", (service_id,))
        if not self.client:
            return None
        result = self._execute(
            self.client.table("services").select("*").eq("id", service_id).limit(1)
        )
        return result.data[0] if result and result.data else None

    def get_service_by_url(self, user_id: str, url: str) -> dict | None:
        if self.local:
            return self._row(
                "SELECT * FROM services WHERE user_id=? AND url=? LIMIT 1", (user_id, url)
            )
        if not self.client:
            return None
        result = self._execute(
            self.client.table("services").select("*").eq("user_id", user_id).eq("url", url).limit(1)
        )
        return result.data[0] if result and result.data else None

    def add_service(
        self,
        user_id: str,
        name: str,
        url: str,
        project_id: str | None = None,
        check_interval: int = 30,
    ) -> dict | None:
        if self.local:
            now = self._now()
            item = {
                "id": str(uuid4()),
                "user_id": user_id,
                "project_id": project_id,
                "name": name,
                "url": url,
                "check_interval": check_interval,
                "is_active": 1,
                "last_status": "unknown",
                "last_response_time_ms": None,
                "last_checked_at": None,
                "created_at": now,
                "updated_at": now,
            }
            self._connection().execute(
                "INSERT INTO services VALUES (:id,:user_id,:project_id,:name,:url,:check_interval,:is_active,:last_status,:last_response_time_ms,:last_checked_at,:created_at,:updated_at)",
                item,
            )
            self._commit()
            return item
        if not self.client:
            return None
        data = {"user_id": user_id, "name": name, "url": url, "check_interval": check_interval}
        if project_id:
            data["project_id"] = project_id
        result = self._execute(self.client.table("services").insert(data))
        return result.data[0] if result and result.data else None

    def delete_service(self, service_id: str) -> bool:
        if self.local:
            cursor = self._connection().execute("DELETE FROM services WHERE id=?", (service_id,))
            self._commit()
            return cursor.rowcount > 0
        if not self.client:
            return False
        self._execute(self.client.table("services").delete().eq("id", service_id))
        return True

    def get_service_by_name(self, user_id: str, name: str) -> dict | None:
        """Return one service owned by user, matching name case-insensitively."""
        if self.local:
            return self._row(
                "SELECT * FROM services WHERE user_id=? AND lower(name)=lower(?) LIMIT 1",
                (user_id, name),
            )
        if not self.client:
            return None
        result = self._execute(
            self.client.table("services")
            .select("*")
            .eq("user_id", user_id)
            .ilike("name", name)
            .limit(1)
        )
        return result.data[0] if result and result.data else None

    def update_service(self, service_id: str, updates: dict) -> bool:
        """Update editable service fields."""
        allowed = {"name", "url", "check_interval", "is_active", "project_id"}
        changes = {key: value for key, value in updates.items() if key in allowed}
        if not changes:
            return False
        if self.local:
            now = self._now()
            if "name" in changes:
                self._execute_sql(
                    "UPDATE services SET name=?, updated_at=? WHERE id=?",
                    (changes["name"], now, service_id),
                )
            if "url" in changes:
                self._execute_sql(
                    "UPDATE services SET url=?, updated_at=? WHERE id=?",
                    (changes["url"], now, service_id),
                )
            if "check_interval" in changes:
                self._execute_sql(
                    "UPDATE services SET check_interval=?, updated_at=? WHERE id=?",
                    (changes["check_interval"], now, service_id),
                )
            if "is_active" in changes:
                self._execute_sql(
                    "UPDATE services SET is_active=?, updated_at=? WHERE id=?",
                    (changes["is_active"], now, service_id),
                )
            if "project_id" in changes:
                self._execute_sql(
                    "UPDATE services SET project_id=?, updated_at=? WHERE id=?",
                    (changes["project_id"], now, service_id),
                )
            self._commit()
            return True
        if not self.client:
            return False
        self._execute(self.client.table("services").update(changes).eq("id", service_id))
        return True

    def update_service_status(self, service_id: str, status: str, response_time_ms: int) -> bool:
        now = self._now()
        if self.local:
            self._connection().execute(
                "UPDATE services SET last_status=?, last_response_time_ms=?, last_checked_at=?, updated_at=? WHERE id=?",
                (status, response_time_ms, now, now, service_id),
            )
            self._commit()
            return True
        if not self.client:
            return False
        self._execute(
            self.client.table("services")
            .update(
                {
                    "last_status": status,
                    "last_response_time_ms": response_time_ms,
                    "last_checked_at": now,
                }
            )
            .eq("id", service_id)
        )
        return True

    def _local_incidents(
        self,
        user_id: str | None = None,
        incident_id: str | None = None,
        limit: int = 10,
        severity: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        query = "SELECT i.*, s.name AS service_name, s.url AS service_url FROM incidents i JOIN services s ON s.id=i.service_id"
        conditions, params = [], []
        if user_id:
            conditions.append("i.user_id=?")
            params.append(user_id)
        if incident_id:
            conditions.append("i.id=?")
            params.append(incident_id)
        if severity:
            conditions.append("i.severity=?")
            params.append(severity)
        if status:
            conditions.append("i.status=?")
            params.append(status)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY i.detected_at DESC LIMIT ?"
        params.append(limit)
        items = self._rows(query, tuple(params))
        for item in items:
            item["services"] = {"name": item.pop("service_name"), "url": item.pop("service_url")}
        return items

    def list_incidents(
        self, user_id: str, limit: int = 10, severity: str | None = None, status: str | None = None
    ) -> list[dict]:
        if self.local:
            return self._local_incidents(
                user_id=user_id, limit=limit, severity=severity, status=status
            )
        if not self.client:
            return []
        query = (
            self.client.table("incidents").select("*, services(name, url)").eq("user_id", user_id)
        )
        if severity:
            query = query.eq("severity", severity)
        if status:
            query = query.eq("status", status)
        result = self._execute(query.order("detected_at", desc=True).limit(limit))
        return result.data or []

    def get_incident(self, incident_id: str) -> dict | None:
        if self.local:
            items = self._local_incidents(incident_id=incident_id, limit=1)
            return items[0] if items else None
        if not self.client:
            return None
        result = self._execute(
            self.client.table("incidents")
            .select("*, services(name, url)")
            .eq("id", incident_id)
            .limit(1)
        )
        return result.data[0] if result and result.data else None

    def get_active_incident_for_service(self, user_id: str, service_id: str) -> dict | None:
        if self.local:
            items = self._rows(
                "SELECT * FROM incidents WHERE user_id=? AND service_id=? AND status <> 'resolved' ORDER BY detected_at DESC LIMIT 1",
                (user_id, service_id),
            )
            return items[0] if items else None
        if not self.client:
            return None
        result = self._execute(
            self.client.table("incidents")
            .select("*")
            .eq("user_id", user_id)
            .eq("service_id", service_id)
            .neq("status", "resolved")
            .order("detected_at", desc=True)
            .limit(1)
        )
        return result.data[0] if result and result.data else None

    def create_incident(
        self,
        user_id: str,
        service_id: str,
        severity: str,
        error_message: str,
        error_code: int | None = None,
        status: str = "detecting",
        extra_metadata: dict | None = None,
    ) -> dict | None:
        now = self._now()
        detection_meta = extra_metadata or {}
        investigation = json.dumps(detection_meta) if detection_meta else None
        event_meta = {
            "severity": severity,
            "status": status,
            "error_code": error_code,
            **detection_meta,
        }
        if self.local:
            item = {
                "id": str(uuid4()),
                "user_id": user_id,
                "service_id": service_id,
                "status": status,
                "severity": severity,
                "error_code": error_code,
                "error_message": error_message,
                "detected_at": now,
                "resolved_at": None,
                "mttr_seconds": None,
                "investigation_report": investigation,
                "action_plan": None,
                "postmortem": None,
                "created_at": now,
            }
            self._connection().execute(
                "INSERT INTO incidents VALUES (:id,:user_id,:service_id,:status,:severity,:error_code,:error_message,:detected_at,:resolved_at,:mttr_seconds,:investigation_report,:action_plan,:postmortem,:created_at)",
                item,
            )
            self._commit()
            self.create_incident_event(
                user_id,
                item["id"],
                service_id,
                "detected",
                error_message,
                event_meta,
            )
            return item
        if not self.client:
            return None
        payload = {
            "user_id": user_id,
            "service_id": service_id,
            "severity": severity,
            "status": status,
            "error_code": error_code,
            "error_message": error_message,
            "detected_at": now,
        }
        if investigation:
            payload["investigation_report"] = investigation
        result = self._execute(self.client.table("incidents").insert(payload))
        incident = result.data[0] if result and result.data else None
        if incident:
            self.create_incident_event(
                user_id,
                incident["id"],
                service_id,
                "detected",
                error_message,
                event_meta,
            )
        return incident

    def update_incident(self, incident_id: str, updates: dict) -> bool:
        if self.local:
            changed = False
            if "status" in updates:
                self._connection().execute(
                    "UPDATE incidents SET status=? WHERE id=?", (updates["status"], incident_id)
                )
                changed = True
            if "resolved_at" in updates:
                self._connection().execute(
                    "UPDATE incidents SET resolved_at=? WHERE id=?",
                    (updates["resolved_at"], incident_id),
                )
                changed = True
            if "mttr_seconds" in updates:
                self._connection().execute(
                    "UPDATE incidents SET mttr_seconds=? WHERE id=?",
                    (updates["mttr_seconds"], incident_id),
                )
                changed = True
            if "investigation_report" in updates:
                self._connection().execute(
                    "UPDATE incidents SET investigation_report=? WHERE id=?",
                    (updates["investigation_report"], incident_id),
                )
                changed = True
            if "action_plan" in updates:
                self._connection().execute(
                    "UPDATE incidents SET action_plan=? WHERE id=?",
                    (updates["action_plan"], incident_id),
                )
                changed = True
            if "postmortem" in updates:
                self._connection().execute(
                    "UPDATE incidents SET postmortem=? WHERE id=?",
                    (updates["postmortem"], incident_id),
                )
                changed = True
            if not changed:
                return False
            self._commit()
            return True
        if not self.client:
            return False
        self._execute(self.client.table("incidents").update(updates).eq("id", incident_id))
        return True

    def resolve_incident(
        self, incident_id: str, action_plan: str | None = None, postmortem: str | None = None
    ) -> bool:
        incident = self.get_incident(incident_id)
        now = self._now()
        updates: dict[str, object] = {"status": "resolved", "resolved_at": now}
        if action_plan is not None:
            updates["action_plan"] = action_plan
        if postmortem is not None:
            updates["postmortem"] = postmortem
        if incident and incident.get("detected_at"):
            try:
                start = datetime.fromisoformat(str(incident["detected_at"]).replace("Z", "+00:00"))
                end = datetime.fromisoformat(now)
                updates["mttr_seconds"] = (end - start).total_seconds()
            except ValueError:
                pass
        updated = self.update_incident(incident_id, updates)
        if updated and incident and incident.get("user_id") and incident.get("service_id"):
            self.create_incident_event(
                incident["user_id"],
                incident_id,
                incident["service_id"],
                "resolved",
                action_plan or "Incident resolved after recovery checks passed.",
                {"resolved_at": now},
            )
        return updated

    def log_health_check(
        self,
        service_id: str,
        status_code: int,
        response_time_ms: int,
        is_healthy: bool,
        error: str = "",
        diag: str | None = None,
        anomaly_score: float | None = None,
        model_id: str | None = None,
    ) -> bool:
        if self.local:
            self._connection().execute(
                "INSERT INTO health_checks (id, service_id, status_code, response_time_ms, "
                "is_healthy, error_message, checked_at, diag, anomaly_score, model_id) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    str(uuid4()),
                    service_id,
                    status_code,
                    response_time_ms,
                    int(is_healthy),
                    error,
                    self._now(),
                    diag,
                    anomaly_score,
                    model_id,
                ),
            )
            self._commit()
            return True
        if not self.client:
            return False
        payload = {
            "service_id": service_id,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "is_healthy": is_healthy,
            "error_message": error,
        }
        if diag is not None:
            payload["diag"] = diag
        if anomaly_score is not None:
            payload["anomaly_score"] = anomaly_score
        if model_id is not None:
            payload["model_id"] = model_id
        self._execute(self.client.table("health_checks").insert(payload))
        return True

    def get_latest_health_checks(self, service_id: str, limit: int = 10) -> list[dict]:
        if self.local:
            return self._rows(
                "SELECT * FROM health_checks WHERE service_id=? ORDER BY checked_at DESC LIMIT ?",
                (service_id, limit),
            )
        if not self.client:
            return []
        result = self._execute(
            self.client.table("health_checks")
            .select("*")
            .eq("service_id", service_id)
            .order("checked_at", desc=True)
            .limit(limit)
        )
        return result.data or []

    def list_incident_events(self, incident_id: str) -> list[dict]:
        if self.local:
            items = self._rows(
                "SELECT * FROM incident_events WHERE incident_id=? ORDER BY created_at ASC",
                (incident_id,),
            )
            for item in items:
                item["metadata"] = json.loads(item.get("metadata") or "{}")
            return items
        if not self.client:
            return []
        try:
            result = self._execute(
                self.client.table("incident_events")
                .select("*")
                .eq("incident_id", incident_id)
                .order("created_at", desc=False)
            )
            return result.data or []
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return []

    def create_incident_event(
        self,
        user_id: str,
        incident_id: str,
        service_id: str,
        event_type: str,
        description: str,
        metadata: dict | None = None,
    ) -> bool:
        if self.local:
            self._connection().execute(
                "INSERT INTO incident_events VALUES (?,?,?,?,?,?,?,?)",
                (
                    str(uuid4()),
                    user_id,
                    incident_id,
                    service_id,
                    event_type,
                    description,
                    json.dumps(metadata or {}),
                    self._now(),
                ),
            )
            self._commit()
            return True
        if not self.client:
            return False
        try:
            self._execute(
                self.client.table("incident_events").insert(
                    {
                        "user_id": user_id,
                        "incident_id": incident_id,
                        "service_id": service_id,
                        "event_type": event_type,
                        "description": description,
                        "metadata": metadata or {},
                    }
                )
            )
            return True
        except (AttributeError, RuntimeError, TypeError, ValueError):
            return False

    def list_postmortems(self, user_id: str, limit: int = 50) -> list[dict]:
        """List incidents with saved postmortems for user."""
        if self.local:
            assert self._sqlite is not None
            items = self._rows(
                "SELECT i.*, s.name AS service_name, s.url AS service_url FROM incidents i JOIN services s ON s.id=i.service_id WHERE i.user_id=? AND i.postmortem IS NOT NULL ORDER BY i.detected_at DESC LIMIT ?",
                (user_id, limit),
            )
            for item in items:
                item["services"] = {
                    "name": item.pop("service_name"),
                    "url": item.pop("service_url"),
                }
            return items
        if not self.client:
            return []
        result = self._execute(
            self.client.table("incidents")
            .select("*, services(name, url)")
            .eq("user_id", user_id)
            .not_.is_("postmortem", "null")
            .order("detected_at", desc=True)
            .limit(limit)
        )
        return result.data or []

    def acknowledge_incident(self, incident_id: str, note: str | None = None) -> bool:
        incident = self.get_incident(incident_id)
        if not incident or incident.get("status") == "resolved":
            return False
        updated = self.update_incident(incident_id, {"status": "investigating"})
        if updated and incident.get("user_id") and incident.get("service_id"):
            self.create_incident_event(
                incident["user_id"],
                incident_id,
                incident["service_id"],
                "acknowledged",
                note or "Incident acknowledged and investigation started.",
            )
        return updated

    def save_postmortem(self, incident_id: str, markdown: str) -> bool:
        updated = self.update_incident(incident_id, {"postmortem": markdown})
        if not updated:
            return False
        incident = self.get_incident(incident_id)
        if incident and incident.get("user_id") and incident.get("service_id"):
            self.create_incident_event(
                incident["user_id"],
                incident_id,
                incident["service_id"],
                "postmortem_generated",
                "Postmortem generated and saved on the incident record.",
            )
        return True


_db: SentinelDB | None = None


def get_db() -> SentinelDB:
    """Return cached storage adapter."""
    global _db
    if _db is None:
        _db = SentinelDB()
    return _db


def reset_db() -> None:
    """Close and clear cached adapter; useful for tests and mode changes."""
    global _db
    if _db is not None:
        _db.close()
    _db = None
