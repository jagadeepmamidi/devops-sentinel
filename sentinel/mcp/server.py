"""Read-only MCP adapter for DevOps Sentinel operations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from sentinel.api.quick_health_check import QuickHealthCheck
from sentinel.application.incidents import IncidentService
from sentinel.core.detect import detect_check
from sentinel.core.doctor import run_doctor
from sentinel.core.postmortem_generator import PostmortemGenerator

load_dotenv(dotenv_path=Path.cwd() / ".env")
mcp = FastMCP("devops-sentinel")


def _error(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def _incident_service() -> IncidentService | dict[str, Any]:
    from sentinel.cli.auth import get_current_user, get_storage_mode, is_logged_in
    from sentinel.cli.db import get_db

    mode = get_storage_mode()
    if mode == "none":
        return _error("not_configured", "Run `sentinel init` before using MCP tools.")
    if mode == "supabase" and not os.getenv("SUPABASE_URL"):
        return _error("not_configured", "Configure SUPABASE_URL for Supabase mode.")
    if not is_logged_in():
        return _error(
            "not_logged_in",
            "Run `sentinel login` in Supabase mode before using account-scoped tools.",
        )
    user = get_current_user()
    if not user or not user.get("id"):
        return _error("invalid_session", "Run `sentinel login` again in Supabase mode.")
    db = get_db()
    if not db.connected:
        return _error("db_not_connected", "Check credentials and run `sentinel doctor`.")
    return IncidentService(db, user["id"])


@mcp.tool()
async def health_check(url: str, timeout: int = 10) -> dict:
    """Check one URL for HTTP health, latency, and SSL status."""
    return await QuickHealthCheck().check_url(url, timeout)


@mcp.tool()
async def health_check_batch(urls: list, timeout: int = 10) -> dict:
    """Check up to 10 URLs in parallel."""
    if not urls or len(urls) > 10:
        return _error("invalid_input", "Provide between 1 and 10 URLs.")
    results = await QuickHealthCheck().check_multiple(urls, timeout)
    return {"results": results, "count": len(results)}


@mcp.tool()
def doctor(strict: bool = False) -> dict:
    """Run environment and connectivity diagnostics."""
    return run_doctor(strict=strict)


@mcp.tool()
def list_incidents(limit: int = 10, severity: str = "", status: str = "") -> dict:
    """List recent incidents belonging to current authenticated user."""
    service = _incident_service()
    if isinstance(service, dict):
        return service
    incidents = service.list(limit, severity or None, status or None)
    return {"incidents": incidents, "count": len(incidents)}


@mcp.tool()
def get_incident(incident_id: str) -> dict:
    """Get one incident only when current user owns it."""
    service = _incident_service()
    if isinstance(service, dict):
        return service
    incident = service.get(incident_id)
    return {"incident": incident} if incident else _error("not_found", "Incident not found.")


@mcp.tool()
def get_incident_events(incident_id: str) -> dict:
    """Get auditable timeline events for an owned incident."""
    service = _incident_service()
    if isinstance(service, dict):
        return service
    events = service.events(incident_id)
    return (
        {"events": events, "count": len(events)}
        if events is not None
        else _error("not_found", "Incident not found.")
    )


@mcp.tool()
async def generate_postmortem(incident_id: str) -> dict:
    """Generate a postmortem for an owned incident."""
    service = _incident_service()
    if isinstance(service, dict):
        return service
    incident = service.get(incident_id)
    if not incident:
        return _error("not_found", "Incident not found.")
    events = service.events(incident_id) or []
    return await PostmortemGenerator().generate(incident, events)


@mcp.tool()
def acknowledge_incident(incident_id: str, note: str = "") -> dict:
    """Acknowledge owned incident and start investigation."""
    service = _incident_service()
    if isinstance(service, dict):
        return service
    if not service.acknowledge(incident_id, note or None):
        return _error("not_found", "Incident not found, or already resolved.")
    return {"incident_id": incident_id, "status": "investigating"}


@mcp.tool()
def resolve_incident(incident_id: str, action_plan: str = "") -> dict:
    """Resolve owned incident and record resolution notes."""
    service = _incident_service()
    if isinstance(service, dict):
        return service
    if not service.resolve(incident_id, action_plan or None):
        return _error("not_found", "Incident not found, or resolution failed.")
    return {"incident_id": incident_id, "status": "resolved"}


@mcp.tool()
def analyze_anomaly(metric_name: str, current_value: float, historical_values: list) -> dict:
    """Score a metric with the same local detector as `sentinel monitor` (warmup until 20 samples)."""
    if len(historical_values) < 3:
        return _error("invalid_input", "Provide at least 3 historical values.")
    history = [
        {"response_time_ms": float(value), "status_code": 200, "is_healthy": True}
        for value in historical_values
    ]
    detection = detect_check(
        history,
        healthy=True,
        status_code=200,
        latency_ms=float(current_value),
        service_id=f"mcp-{metric_name}",
    )
    payload = detection.as_dict()
    payload["metric_name"] = metric_name
    payload["current_value"] = current_value
    return payload


def main() -> None:
    """Run MCP over stdio for local hosts such as Claude Desktop and Cursor."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
