"""FastMCP server exposing DevOps Sentinel tools."""

from __future__ import annotations

import json
import os
from typing import List, Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from sentinel.api.quick_health_check import QuickHealthCheck
from sentinel.core.anomaly_detector import AnomalyDetector
from sentinel.core.doctor import run_doctor
from sentinel.core.postmortem_generator import PostmortemGenerator

load_dotenv()

mcp = FastMCP("devops-sentinel")


def _json(data: object) -> str:
    return json.dumps(data, indent=2, default=str)


@mcp.tool()
async def health_check(url: str, timeout: int = 10) -> str:
    """Check a single URL for HTTP health, latency, and SSL status."""
    checker = QuickHealthCheck()
    result = await checker.check_url(url, timeout)
    return _json(result)


@mcp.tool()
async def health_check_batch(urls: List[str], timeout: int = 10) -> str:
    """Check multiple URLs in parallel (max 10)."""
    if len(urls) > 10:
        return _json({"error": "Maximum 10 URLs allowed", "count": len(urls)})
    checker = QuickHealthCheck()
    results = await checker.check_multiple(urls, timeout)
    return _json({"results": results, "count": len(results)})


@mcp.tool()
def doctor(strict: bool = False) -> str:
    """Run environment and connectivity diagnostics."""
    return _json(run_doctor(strict=strict))


@mcp.tool()
def list_incidents(
    limit: int = 10,
    severity: Optional[str] = None,
    status: Optional[str] = None,
) -> str:
    """List recent incidents for the authenticated CLI user."""
    from sentinel.cli.auth import get_current_user, is_logged_in
    from sentinel.cli.db import get_db

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not supabase_url or not supabase_key:
        return _json(
            {
                "error": "not_configured",
                "message": "Supabase is not configured. Set SUPABASE_URL and SUPABASE_KEY (or SUPABASE_ANON_KEY).",
            }
        )

    if not is_logged_in():
        return _json(
            {
                "error": "not_logged_in",
                "message": "Not logged in. Run `sentinel login` before listing incidents.",
            }
        )

    db = get_db()
    if not db.connected:
        return _json(
            {
                "error": "db_not_connected",
                "message": "Could not connect to Supabase. Check credentials and run `sentinel doctor`.",
            }
        )

    user = get_current_user()
    if not user or not user.get("id"):
        return _json(
            {
                "error": "invalid_session",
                "message": "Login session is invalid. Run `sentinel login` again.",
            }
        )

    incidents = db.list_incidents(
        user["id"],
        limit=limit,
        severity=severity,
        status=status,
    )
    return _json({"incidents": incidents, "count": len(incidents)})


@mcp.tool()
async def generate_postmortem(incident_id: str) -> str:
    """Generate a postmortem for an incident (DB fetch or template fallback)."""
    from sentinel.cli.auth import is_logged_in
    from sentinel.cli.db import get_db

    generator = PostmortemGenerator()
    incident = None
    events: List[dict] = []

    if is_logged_in():
        db = get_db()
        if db.connected:
            incident = db.get_incident(incident_id)
            if incident:
                events = db.list_incident_events(incident_id)

    if not incident:
        incident = {
            "id": incident_id,
            "title": f"Incident {incident_id}",
            "severity": "P2",
            "description": "No incident record found ? template postmortem generated from defaults.",
        }

    result = await generator.generate(incident, events)
    return _json(result)


@mcp.tool()
def analyze_anomaly(
    metric_name: str,
    current_value: float,
    historical_values: List[float],
) -> str:
    """Detect statistical anomalies in a metric using historical baseline values."""
    detector = AnomalyDetector()
    result = detector.detect(metric_name, current_value, historical_values)
    return _json(result)


def main() -> None:
    """Run the MCP server over stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
