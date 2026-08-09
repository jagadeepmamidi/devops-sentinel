"""
MVP monitoring routes backed by Supabase.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from sentinel.auth.auth_service import get_current_user, security
from sentinel.cli.db import SentinelDB
from sentinel.core.postmortem_generator import PostmortemGenerator


router = APIRouter(tags=["monitoring"])


class ServiceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    url: str = Field(..., min_length=1)
    check_interval: int = Field(default=30, ge=1, le=3600)
    project_id: Optional[str] = None


class PostmortemGenerateRequest(BaseModel):
    incident_id: str
    resolution_notes: Optional[str] = None


def get_request_db(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> SentinelDB:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return SentinelDB(access_token=credentials.credentials)


def _service_payload(service: Dict) -> Dict:
    return {
        "id": service.get("id"),
        "name": service.get("name"),
        "url": service.get("url"),
        "check_interval": service.get("check_interval"),
        "is_active": service.get("is_active", True),
        "last_status": service.get("last_status", "unknown"),
        "last_checked_at": service.get("last_checked_at"),
        "last_response_time_ms": service.get("last_response_time_ms"),
    }


def _incident_payload(incident: Dict) -> Dict:
    service = incident.get("services") or {}
    return {
        "id": incident.get("id"),
        "service_id": incident.get("service_id"),
        "service_name": service.get("name") or incident.get("service_name"),
        "service_url": service.get("url") or incident.get("service_url"),
        "status": incident.get("status"),
        "severity": incident.get("severity"),
        "detected_at": incident.get("detected_at"),
        "resolved_at": incident.get("resolved_at"),
        "error_code": incident.get("error_code"),
        "error_message": incident.get("error_message"),
        "action_plan": incident.get("action_plan"),
        "postmortem": incident.get("postmortem"),
    }


def _timeline_for_incident(incident: Dict) -> List[Dict]:
    events = [
        {
            "timestamp": incident.get("detected_at"),
            "description": f"Incident detected for service {incident.get('service_id')}",
        }
    ]
    if incident.get("resolved_at"):
        events.append(
            {
                "timestamp": incident.get("resolved_at"),
                "description": "Incident resolved",
            }
        )
    return events


def _event_payload(event: Dict) -> Dict:
    return {
        "id": event.get("id"),
        "incident_id": event.get("incident_id"),
        "service_id": event.get("service_id"),
        "event_type": event.get("event_type"),
        "description": event.get("description"),
        "metadata": event.get("metadata") or {},
        "created_at": event.get("created_at"),
    }


@router.get("/api/services")
async def list_services(
    current_user: Dict = Depends(get_current_user),
    db: SentinelDB = Depends(get_request_db),
):
    services = db.list_services(current_user["id"])
    return {"services": [_service_payload(service) for service in services], "total": len(services)}


@router.post("/api/services")
async def create_service(
    request: ServiceCreateRequest,
    current_user: Dict = Depends(get_current_user),
    db: SentinelDB = Depends(get_request_db),
):
    service = db.add_service(
        current_user["id"],
        request.name,
        request.url,
        project_id=request.project_id,
        check_interval=request.check_interval,
    )
    if not service:
        raise HTTPException(status_code=400, detail="Failed to create service")
    return _service_payload(service)


@router.delete("/api/services/{service_id}")
async def delete_service(
    service_id: str,
    current_user: Dict = Depends(get_current_user),
    db: SentinelDB = Depends(get_request_db),
):
    service = db.get_service(service_id)
    if not service or service.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Service not found")
    db.delete_service(service_id)
    return {"status": "deleted", "service_id": service_id}


@router.get("/api/incidents")
async def list_incidents(
    limit: int = 50,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Dict = Depends(get_current_user),
    db: SentinelDB = Depends(get_request_db),
):
    incidents = db.list_incidents(current_user["id"], limit=limit, severity=severity, status=status)
    return {"incidents": [_incident_payload(incident) for incident in incidents], "total": len(incidents)}


@router.get("/api/incidents/{incident_id}")
async def get_incident(
    incident_id: str,
    current_user: Dict = Depends(get_current_user),
    db: SentinelDB = Depends(get_request_db),
):
    incident = db.get_incident(incident_id)
    if not incident or incident.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Incident not found")
    return _incident_payload(incident)


@router.get("/api/incidents/{incident_id}/events")
async def list_incident_events(
    incident_id: str,
    current_user: Dict = Depends(get_current_user),
    db: SentinelDB = Depends(get_request_db),
):
    incident = db.get_incident(incident_id)
    if not incident or incident.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Incident not found")
    events = db.list_incident_events(incident_id)
    return {"events": [_event_payload(event) for event in events], "total": len(events)}


@router.post("/api/postmortems/generate")
async def generate_postmortem(
    request: PostmortemGenerateRequest,
    current_user: Dict = Depends(get_current_user),
    db: SentinelDB = Depends(get_request_db),
):
    incident = db.get_incident(request.incident_id)
    if not incident or incident.get("user_id") != current_user["id"]:
        raise HTTPException(status_code=404, detail="Incident not found")

    generator = PostmortemGenerator()
    events = db.list_incident_events(request.incident_id)
    postmortem = await generator.generate(
        incident={
            "id": incident["id"],
            "title": incident.get("error_message") or f"Incident {incident['id']}",
            "severity": incident.get("severity", "medium"),
            "service_name": (incident.get("services") or {}).get("name", "Unknown service"),
            "description": incident.get("error_message") or "",
            "detected_at": incident.get("detected_at"),
            "resolved_at": incident.get("resolved_at") or datetime.utcnow().isoformat(),
        },
        events=events or _timeline_for_incident(incident),
        resolution=request.resolution_notes or incident.get("action_plan"),
    )
    db.save_postmortem(request.incident_id, postmortem["markdown"])
    return {
        "incident_id": request.incident_id,
        "postmortem": postmortem["markdown"],
        "generated_at": postmortem["generated_at"],
        "status": postmortem["status"],
    }
