"""Rich renderers shared by CLI commands."""

from __future__ import annotations

from datetime import datetime, timezone

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table


def console() -> Console:
    return Console()


def _service_name(item: dict) -> str:
    return (item.get("services") or {}).get("name") or item.get("service_name") or "unknown"


def services_table(items: list[dict]) -> Table:
    table = Table(title="Monitored Services", show_lines=False)
    table.add_column("Name", style="bold")
    table.add_column("URL", overflow="fold")
    table.add_column("Status")
    table.add_column("Latency", justify="right")
    table.add_column("Checked")
    for item in items:
        status = str(item.get("last_status", "unknown"))
        style = {"healthy": "green", "degraded": "yellow", "down": "red"}.get(status, "white")
        table.add_row(
            str(item.get("name", "Unnamed")),
            str(item.get("url", "")),
            f"[{style}]{status}[/{style}]",
            f"{item.get('last_response_time_ms') or 0}ms",
            str(item.get("last_checked_at") or "never")[:19].replace("T", " "),
        )
    return table


def projects_table(items: list[dict]) -> Table:
    table = Table(title="Projects")
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Created")
    for item in items:
        table.add_row(
            str(item.get("name", "Unnamed")),
            str(item.get("description", "")),
            str(item.get("created_at", ""))[:10],
        )
    return table


def incidents_table(items: list[dict]) -> Table:
    table = Table(title="Recent Incidents")
    table.add_column("ID", no_wrap=True)
    table.add_column("Severity")
    table.add_column("Service")
    table.add_column("Status")
    table.add_column("Detected")
    for item in items:
        severity = str(item.get("severity", "unknown")).lower()
        style = {"critical": "red", "high": "yellow", "medium": "blue", "low": "white"}.get(
            severity, "white"
        )
        table.add_row(
            str(item.get("id", ""))[:12],
            f"[{style}]{severity}[/{style}]",
            _service_name(item),
            str(item.get("status", "unknown")),
            str(item.get("detected_at", ""))[:19].replace("T", " "),
        )
    return table


def incident_detail(incident: dict, events: list[dict]) -> Group:
    service = incident.get("services") or {}
    details = "\n".join(
        [
            f"ID: {incident.get('id')}",
            f"Service: {service.get('name') or incident.get('service_name', 'unknown')}",
            f"URL: {service.get('url') or incident.get('service_url', 'unknown')}",
            f"Status: {incident.get('status')}",
            f"Severity: {incident.get('severity')}",
            f"Error: {incident.get('error_message') or 'n/a'}",
        ]
    )
    timeline = Table(title="Timeline")
    timeline.add_column("Time")
    timeline.add_column("Event")
    for event in events:
        timeline.add_row(
            str(event.get("created_at") or event.get("timestamp") or "")[:19].replace("T", " "),
            f"{event.get('event_type', 'event')}: {event.get('description', '')}",
        )
    return Group(Panel(details, title="Incident"), timeline)


def dashboard_table(items: list[dict]) -> Table:
    table = Table(
        title=f"Sentinel Dashboard · {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
    )
    table.add_column("Service", style="bold")
    table.add_column("URL", overflow="fold")
    table.add_column("Status")
    table.add_column("Latency", justify="right")
    table.add_column("Error")
    for item in items:
        healthy = item.get("healthy", False)
        status = "healthy" if healthy else ("degraded" if item.get("status_code") else "down")
        style = "green" if healthy else ("yellow" if item.get("status_code") else "red")
        table.add_row(
            str(item.get("name", "unknown")),
            str(item.get("url", "")),
            f"[{style}]{status}[/{style}]",
            f"{item.get('latency_ms') or 0:.0f}ms",
            str(item.get("error") or item.get("status_code") or ""),
        )
    return table
