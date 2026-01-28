"""
DevOps Sentinel - Supabase Client
=================================
Database layer for persisting services, incidents, and postmortems.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from config import settings
from models import ServiceConfig, Incident, Postmortem, HealthCheckResult


class SupabaseClient:
    """
    Supabase database client for DevOps Sentinel.
    
    Handles persistence for:
    - Monitored services
    - Health check history
    - Incidents and timelines
    - Generated postmortems
    """
    
    _instance: Optional["SupabaseClient"] = None
    _client = None
    
    def __new__(cls) -> "SupabaseClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None and settings.has_supabase:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Supabase client."""
        try:
            from supabase import create_client
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            if settings.enable_privacy_logging:
                print(f"[PRIVACY] Connected to Supabase: {settings.supabase_url}")
        except Exception as e:
            print(f"[WARNING] Supabase initialization failed: {e}")
            self._client = None
    
    @property
    def is_connected(self) -> bool:
        """Check if Supabase is connected."""
        return self._client is not None
    
    # ===== Services CRUD =====
    
    def add_service(self, service: ServiceConfig) -> Optional[ServiceConfig]:
        """Add a new service to monitor."""
        if not self.is_connected:
            return None
        
        data = {
            "id": str(service.id),
            "name": service.name,
            "url": service.url,
            "check_interval": service.check_interval,
            "is_active": service.is_active,
            "created_at": service.created_at.isoformat()
        }
        
        result = self._client.table("services").insert(data).execute()
        return service if result.data else None
    
    def get_services(self, active_only: bool = True) -> List[ServiceConfig]:
        """Get all monitored services."""
        if not self.is_connected:
            return []
        
        query = self._client.table("services").select("*")
        if active_only:
            query = query.eq("is_active", True)
        
        result = query.execute()
        return [ServiceConfig(**row) for row in result.data] if result.data else []
    
    def get_service(self, service_id: UUID) -> Optional[ServiceConfig]:
        """Get a service by ID."""
        if not self.is_connected:
            return None
        
        result = self._client.table("services").select("*").eq("id", str(service_id)).single().execute()
        return ServiceConfig(**result.data) if result.data else None
    
    def delete_service(self, service_id: UUID) -> bool:
        """Delete a service."""
        if not self.is_connected:
            return False
        
        result = self._client.table("services").delete().eq("id", str(service_id)).execute()
        return bool(result.data)
    
    # ===== Health Checks =====
    
    def log_health_check(self, result: HealthCheckResult) -> bool:
        """Log a health check result."""
        if not self.is_connected:
            return False
        
        data = {
            "service_id": str(result.service_id),
            "status_code": result.status_code,
            "response_time_ms": result.response_time_ms,
            "is_healthy": result.is_healthy,
            "checked_at": result.checked_at.isoformat()
        }
        
        self._client.table("health_checks").insert(data).execute()
        return True
    
    # ===== Incidents =====
    
    def create_incident(self, incident: Incident) -> Optional[Incident]:
        """Create a new incident."""
        if not self.is_connected:
            return None
        
        data = {
            "id": str(incident.id),
            "service_id": str(incident.service_id),
            "status": incident.status.value,
            "severity": incident.severity.value,
            "detected_at": incident.detected_at.isoformat(),
            "error_code": incident.error_code,
            "error_message": incident.error_message
        }
        
        result = self._client.table("incidents").insert(data).execute()
        return incident if result.data else None
    
    def update_incident(self, incident: Incident) -> bool:
        """Update an existing incident."""
        if not self.is_connected:
            return False
        
        data = {
            "status": incident.status.value,
            "alerted_at": incident.alerted_at.isoformat() if incident.alerted_at else None,
            "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
            "mttd_seconds": incident.mttd_seconds,
            "mttr_seconds": incident.mttr_seconds,
            "triage_summary": incident.triage_summary,
            "investigation_report": incident.investigation_report,
            "action_plan": incident.action_plan,
            "postmortem": incident.action_plan  # Will be replaced with full postmortem
        }
        
        result = self._client.table("incidents").update(data).eq("id", str(incident.id)).execute()
        return bool(result.data)
    
    def get_incidents(self, limit: int = 50) -> List[Incident]:
        """Get recent incidents."""
        if not self.is_connected:
            return []
        
        result = self._client.table("incidents").select("*").order("detected_at", desc=True).limit(limit).execute()
        
        incidents = []
        for row in result.data or []:
            incidents.append(Incident(
                id=UUID(row["id"]),
                service_id=UUID(row["service_id"]),
                service_name=row.get("service_name", "Unknown"),
                service_url=row.get("service_url", ""),
                status=row["status"],
                detected_at=datetime.fromisoformat(row["detected_at"]),
                error_code=row.get("error_code"),
                error_message=row.get("error_message")
            ))
        
        return incidents
    
    def get_incident(self, incident_id: UUID) -> Optional[Incident]:
        """Get an incident by ID."""
        if not self.is_connected:
            return None
        
        result = self._client.table("incidents").select("*").eq("id", str(incident_id)).single().execute()
        if not result.data:
            return None
        
        row = result.data
        return Incident(
            id=UUID(row["id"]),
            service_id=UUID(row["service_id"]),
            service_name=row.get("service_name", "Unknown"),
            service_url=row.get("service_url", ""),
            status=row["status"],
            detected_at=datetime.fromisoformat(row["detected_at"]),
            error_code=row.get("error_code"),
            error_message=row.get("error_message"),
            action_plan=row.get("postmortem")
        )
    
    # ===== Postmortems =====
    
    def save_postmortem(self, postmortem: Postmortem) -> bool:
        """Save a generated postmortem."""
        if not self.is_connected:
            return False
        
        # Update the incident with the full postmortem markdown
        data = {
            "postmortem": postmortem.to_markdown()
        }
        
        result = self._client.table("incidents").update(data).eq("id", str(postmortem.incident_id)).execute()
        return bool(result.data)


# Singleton instance
supabase_client = SupabaseClient()
