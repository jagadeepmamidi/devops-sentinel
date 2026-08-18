"""Read-only MCP adapter for DevOps Sentinel operations."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from sentinel.api.quick_health_check import QuickHealthCheck
from sentinel.application.incidents import IncidentService
from sentinel.core.anomaly_detector import AnomalyDetector
from sentinel.core.doctor import run_doctor
from sentinel.core.postmortem_generator import PostmortemGenerator

load_dotenv(dotenv_path=Path.cwd() / ".env")
mcp = FastMCP("devops-sentinel")


def _error(code: str, message: str) -> dict[str, Any]:
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
async def health_check(url: str, timeout: int = 10) -> dict[str, Any]:
    """Check one URL for HTTP health, latency, and SSL status."""
    return await QuickHealthCheck().check_url(url, timeout)


@mcp.tool()
async def health_check_batch(urls: list[str], timeout: int = 10) -> dict[str, Any]:
    """Check up to 10 URLs in parallel."""
    if not urls or len(urls) > 10:
        return _error("invalid_input", "Provide between 1 and 10 URLs.")
    results = await QuickHealthCheck().check_multiple(urls, timeout)
    return {"results": results, "count": len(results)}


@mcp.tool()
def doctor(strict: bool = False) -> dict[str, Any]:
    """Run environment and connectivity diagnostics."""
    return run_doctor(strict=strict)


@mcp.tool()
def list_incidents(
    limit: int = 10, severity: str | None = None, status: str | None = None
) -> dict[str, Any]:
    """List recent incidents belonging to current authenticated user."""
    service = _incident_service()
    if isinstance(service, dict):
        return service
    incidents = service.list(limit, severity, status)
    return {"incidents": incidents, "count": len(incidents)}


@mcp.tool()
def get_incident(incident_id: str) -> dict[str, Any]:
    """Get one incident only when current user owns it."""
    service = _incident_service()
    if isinstance(service, dict):
        return service
    incident = service.get(incident_id)
    return {"incident": incident} if incident else _error("not_found", "Incident not found.")


@mcp.tool()
def get_incident_events(incident_id: str) -> dict[str, Any]:
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
async def generate_postmortem(incident_id: str) -> dict[str, Any]:
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
def analyze_anomaly(
    metric_name: str, current_value: float, historical_values: list[float]
) -> dict[str, Any]:
    """Detect statistical anomalies against historical baseline values."""
    if len(historical_values) < 3:
        return _error("invalid_input", "Provide at least 3 historical values.")
    return AnomalyDetector().detect(metric_name, current_value, historical_values)


def main() -> None:
    """Run MCP over stdio for local hosts such as Claude Desktop and Cursor."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
