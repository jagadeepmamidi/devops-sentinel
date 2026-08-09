"""
DevOps Sentinel shared Supabase data access.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Dict, List, Optional

try:
    from supabase import Client, create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    Client = None
    SUPABASE_AVAILABLE = False

from .auth import load_credentials


def get_supabase_client(
    access_token: Optional[str] = None,
    refresh_token: Optional[str] = None,
) -> Optional[Client]:
    """Create a Supabase client scoped to the current or provided user token."""
    if not SUPABASE_AVAILABLE:
        return None

    url = os.getenv("SUPABASE_URL")
    anon_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not anon_key:
        return None

    client = create_client(url, anon_key)

    creds = load_credentials() or {}
    token = access_token or creds.get("access_token")
    token_refresh = refresh_token or creds.get("refresh_token")
    if not token:
        return client

    try:
        if token_refresh:
            client.auth.set_session(token, token_refresh)
        else:
            client.postgrest.auth(token)
    except Exception:
        try:
            client.postgrest.auth(token)
        except Exception:
            pass

    return client


class SentinelDB:
    """Database operations shared by the CLI and API layers."""

    def __init__(
        self,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        client: Optional[Client] = None,
    ):
        self.client = client or get_supabase_client(access_token, refresh_token)

    @property
    def connected(self) -> bool:
        return self.client is not None

    def _execute(self, builder):
        return builder.execute() if builder is not None else None

    def list_projects(self, user_id: str) -> List[Dict]:
        if not self.client:
            return []
        result = self._execute(
            self.client.table("projects").select("*").eq("user_id", user_id).order("created_at", desc=True)
        )
        return result.data or []

    def create_project(self, user_id: str, name: str, description: str = "") -> Optional[Dict]:
        if not self.client:
            return None
        result = self._execute(
            self.client.table("projects").insert(
                {
                    "user_id": user_id,
                    "name": name,
                    "description": description,
                }
            )
        )
        return result.data[0] if result and result.data else None

    def delete_project(self, project_id: str) -> bool:
        if not self.client:
            return False
        self._execute(self.client.table("projects").delete().eq("id", project_id))
        return True

    def list_services(self, user_id: str, project_id: Optional[str] = None) -> List[Dict]:
        if not self.client:
            return []
        query = self.client.table("services").select("*").eq("user_id", user_id)
        if project_id:
            query = query.eq("project_id", project_id)
        result = self._execute(query.order("created_at", desc=True))
        return result.data or []

    def get_service(self, service_id: str) -> Optional[Dict]:
        if not self.client:
            return None
        result = self._execute(self.client.table("services").select("*").eq("id", service_id).limit(1))
        return result.data[0] if result and result.data else None

    def get_service_by_url(self, user_id: str, url: str) -> Optional[Dict]:
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
        project_id: Optional[str] = None,
        check_interval: int = 30,
    ) -> Optional[Dict]:
        if not self.client:
            return None
        data = {
            "user_id": user_id,
            "name": name,
            "url": url,
            "check_interval": check_interval,
        }
        if project_id:
            data["project_id"] = project_id
        result = self._execute(self.client.table("services").insert(data))
        return result.data[0] if result and result.data else None

    def delete_service(self, service_id: str) -> bool:
        if not self.client:
            return False
        self._execute(self.client.table("services").delete().eq("id", service_id))
        return True

    def update_service_status(self, service_id: str, status: str, response_time_ms: int) -> bool:
        if not self.client:
            return False
        self._execute(
            self.client.table("services")
            .update(
                {
                    "last_status": status,
                    "last_response_time_ms": response_time_ms,
                    "last_checked_at": datetime.utcnow().isoformat(),
                }
            )
            .eq("id", service_id)
        )
        return True

    def list_incidents(
        self,
        user_id: str,
        limit: int = 10,
        severity: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict]:
        if not self.client:
            return []
        query = self.client.table("incidents").select("*, services(name, url)").eq("user_id", user_id)
        if severity:
            query = query.eq("severity", severity)
        if status:
            query = query.eq("status", status)
        result = self._execute(query.order("detected_at", desc=True).limit(limit))
        return result.data or []

    def get_incident(self, incident_id: str) -> Optional[Dict]:
        if not self.client:
            return None
        result = self._execute(
            self.client.table("incidents").select("*, services(name, url)").eq("id", incident_id).limit(1)
        )
        return result.data[0] if result and result.data else None

    def get_active_incident_for_service(self, user_id: str, service_id: str) -> Optional[Dict]:
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
        error_code: Optional[int] = None,
        status: str = "detecting",
    ) -> Optional[Dict]:
        if not self.client:
            return None
        result = self._execute(
            self.client.table("incidents").insert(
                {
                    "user_id": user_id,
                    "service_id": service_id,
                    "severity": severity,
                    "status": status,
                    "error_code": error_code,
                    "error_message": error_message,
                    "detected_at": datetime.utcnow().isoformat(),
                }
            )
        )
        incident = result.data[0] if result and result.data else None
        if incident:
            self.create_incident_event(
                user_id=user_id,
                incident_id=incident["id"],
                service_id=service_id,
                event_type="detected",
                description=error_message,
                metadata={"severity": severity, "status": status, "error_code": error_code},
            )
        return incident

    def update_incident(self, incident_id: str, updates: Dict) -> bool:
        if not self.client:
            return False
        self._execute(self.client.table("incidents").update(updates).eq("id", incident_id))
        return True

    def resolve_incident(
        self,
        incident_id: str,
        action_plan: Optional[str] = None,
        postmortem: Optional[str] = None,
    ) -> bool:
        detected_at = None
        user_id = None
        service_id = None
        incident = self.get_incident(incident_id)
        if incident:
            detected_at = incident.get("detected_at")
            user_id = incident.get("user_id")
            service_id = incident.get("service_id")
        updates: Dict[str, object] = {
            "status": "resolved",
            "resolved_at": datetime.utcnow().isoformat(),
        }
        if action_plan is not None:
            updates["action_plan"] = action_plan
        if postmortem is not None:
            updates["postmortem"] = postmortem
        if detected_at:
            try:
                start = datetime.fromisoformat(str(detected_at).replace("Z", "+00:00"))
                end = datetime.fromisoformat(str(updates["resolved_at"]).replace("Z", "+00:00"))
                updates["mttr_seconds"] = (end - start).total_seconds()
            except ValueError:
                pass
        updated = self.update_incident(incident_id, updates)
        if updated and user_id and service_id:
            self.create_incident_event(
                user_id=user_id,
                incident_id=incident_id,
                service_id=service_id,
                event_type="resolved",
                description=action_plan or "Incident resolved after recovery checks passed.",
                metadata={"resolved_at": updates["resolved_at"]},
            )
        return updated

    def log_health_check(
        self,
        service_id: str,
        status_code: int,
        response_time_ms: int,
        is_healthy: bool,
        error: str = "",
    ) -> bool:
        if not self.client:
            return False
        self._execute(
            self.client.table("health_checks").insert(
                {
                    "service_id": service_id,
                    "status_code": status_code,
                    "response_time_ms": response_time_ms,
                    "is_healthy": is_healthy,
                    "error_message": error,
                }
            )
        )
        return True

    def get_latest_health_checks(self, service_id: str, limit: int = 10) -> List[Dict]:
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

    def list_incident_events(self, incident_id: str) -> List[Dict]:
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
        except Exception:
            return []

    def create_incident_event(
        self,
        user_id: str,
        incident_id: str,
        service_id: str,
        event_type: str,
        description: str,
        metadata: Optional[Dict] = None,
    ) -> bool:
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
        except Exception:
            return False

    def save_postmortem(self, incident_id: str, markdown: str) -> bool:
        updated = self.update_incident(incident_id, {"postmortem": markdown})
        if not updated:
            return False
        incident = self.get_incident(incident_id)
        if incident and incident.get("user_id") and incident.get("service_id"):
            self.create_incident_event(
                user_id=incident["user_id"],
                incident_id=incident_id,
                service_id=incident["service_id"],
                event_type="postmortem_generated",
                description="Postmortem generated and saved on the incident record.",
            )
        return True


_db: Optional[SentinelDB] = None


def get_db() -> SentinelDB:
    """Get a cached CLI database client."""
    global _db
    if _db is None:
        _db = SentinelDB()
    return _db
