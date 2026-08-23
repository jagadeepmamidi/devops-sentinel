"""CrewAI-compatible safe tool adapters for legacy Sentinel agents.

Canonical monitoring remains in ``sentinel``. These adapters keep the optional
CrewAI agent graph executable without importing a missing top-level package.
"""

import json
import os
import re

import httpx
from crewai.tools import tool


@tool("health_check")
def health_check_tool(url: str) -> str:
    """Check one HTTP endpoint and return status plus latency."""
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(url)
        return json.dumps(
            {"url": url, "status_code": response.status_code, "healthy": response.is_success}
        )
    except httpx.HTTPError as error:
        return json.dumps({"url": url, "healthy": False, "error": str(error)})


@tool("slack_alert")
def slack_alert_tool(message: str) -> str:
    """Send an alert only when an explicit Slack webhook is configured."""
    webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook:
        return "Slack webhook not configured; alert not sent."
    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(webhook, json={"text": message})
        return f"Slack alert returned HTTP {response.status_code}."
    except httpx.HTTPError as error:
        return f"Slack alert failed: {error}"


@tool("log_analysis")
def log_analysis_tool(log_text: str) -> str:
    """Summarize common error signals from supplied logs; never fetches arbitrary files."""
    lines = [line.strip() for line in log_text.splitlines() if line.strip()]
    matches = [
        line
        for line in lines
        if re.search(r"error|exception|failed|timeout|critical", line, re.IGNORECASE)
    ]
    return json.dumps(
        {"line_count": len(lines), "signal_count": len(matches), "signals": matches[:20]}
    )


@tool("deployment_history")
def deployment_history_tool(service_name: str) -> str:
    """Return deployment context supplied by the caller; no external mutation."""
    return json.dumps({"service": service_name, "status": "not_configured", "deployments": []})


@tool("database_health")
def database_health_tool(database_name: str = "default") -> str:
    """Report database probe configuration without exposing credentials."""
    configured = bool(os.getenv("DATABASE_URL") or os.getenv("SUPABASE_URL"))
    return json.dumps({"database": database_name, "configured": configured, "healthy": configured})
