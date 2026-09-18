"""Phosphor terminal chrome shared by CLI commands.

Brand tokens match the site terminals: off-black surface, one green accent,
sharp boxes, status lamps. JSON and CI output stay unstyled.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

BRAND_GREEN = "#46c48a"
BRAND_RED = "#c45b4a"
BRAND_MUTED = "#7f8c86"
BRAND_FG = "#d8e4de"

THEME = Theme(
    {
        "ok": f"bold {BRAND_GREEN}",
        "bad": f"bold {BRAND_RED}",
        "warn": f"bold {BRAND_MUTED}",
        "muted": BRAND_MUTED,
        "ink": BRAND_FG,
        "label": f"bold {BRAND_FG}",
        "prompt": BRAND_GREEN,
    }
)

_STATE_STYLE = {
    "HEALTHY": "ok",
    "OK": "ok",
    "WATCH": "warn",
    "DEGRADED": "bad",
    "DOWN": "bad",
    "UNREACHABLE": "bad",
    "INCIDENT": "bad",
}

_LAMP = {"HEALTHY": "ok", "OK": "ok", "WATCH": "warn"}


def _want_unicode() -> bool:
    encoding = (getattr(sys.stdout, "encoding", None) or "").lower().replace("-", "")
    if encoding in {"ascii", "usascii"}:
        return False
    if os.getenv("TERM") == "dumb":
        return False
    return True


def _lamp_glyph() -> str:
    return "●" if _want_unicode() else "*"


def console() -> Console:
    no_color = "NO_COLOR" in os.environ or os.getenv("TERM") == "dumb"
    return Console(theme=THEME, highlight=False, soft_wrap=True, no_color=no_color)


def status_lamp(state: str) -> Text:
    """Semantic lamp plus label. Lamp is state, not decoration."""
    key = str(state or "UNKNOWN").upper()
    style = _STATE_STYLE.get(key, "muted")
    lamp_style = _LAMP.get(key, "bad" if style == "bad" else "muted")
    out = Text()
    out.append(_lamp_glyph(), style=lamp_style)
    out.append(" ")
    out.append(key, style=style)
    return out


def _session_panel(body, *, title: str, meta: str | None = None) -> Panel:
    subtitle = Text(meta, style="muted") if meta else None
    return Panel(
        body,
        title=Text(title, style="ink"),
        title_align="left",
        subtitle=subtitle,
        subtitle_align="right",
        box=box.SQUARE,
        border_style="muted",
        padding=(0, 1),
        style="ink",
    )


def _prompt_line(command: str) -> Text:
    line = Text()
    line.append("$", style="prompt")
    line.append(" ")
    line.append(command, style="ink")
    return line


def _service_name(item: dict) -> str:
    return (item.get("services") or {}).get("name") or item.get("service_name") or "unknown"


def lamp_state_for_check(status: str) -> str:
    return {"ok": "HEALTHY", "warn": "WATCH", "fail": "DEGRADED", "error": "DOWN"}.get(
        str(status or "").lower(), "WATCH"
    )


def check_state(result: dict) -> str:
    if result.get("watch") and result.get("healthy"):
        return "WATCH"
    if result.get("healthy"):
        return "HEALTHY"
    if result.get("status_code"):
        return "DEGRADED"
    return "DOWN"


def format_http(result: dict) -> str:
    code = result.get("status_code")
    if code:
        return f"HTTP {code}"
    if result.get("error"):
        return "UNREACHABLE"
    return "no response"


def format_latency(result: dict) -> str:
    value = result.get("latency_ms")
    try:
        return f"{float(value or 0):.0f}ms"
    except (TypeError, ValueError):
        return "0ms"


def render_check_line(result: dict, *, service: str | None = None) -> Text:
    """One live probe line. Streaming friendly: no box per check."""
    from ..core.detect import format_detect_fields

    state = check_state(result)
    name = service or result.get("service") or result.get("url") or "unknown"
    line = status_lamp(state)
    line.append("  ")
    line.append(str(name), style="ink")
    line.append("  ")
    line.append(format_http(result), style="muted")
    line.append("  ")
    line.append(format_latency(result), style="muted")
    if result.get("check") is not None:
        line.append("  ")
        line.append(f"#{result['check']}", style="muted")
    extra = []
    if result.get("ssl_days") is not None:
        extra.append(f"tls {result['ssl_days']}d")
    detect = format_detect_fields(result)
    if detect:
        extra.append(detect)
    if result.get("error") and not result.get("healthy"):
        extra.append(str(result["error"]))
    elif result.get("error") and result.get("healthy"):
        extra.append(str(result["error"]))
    if extra:
        line.append("  ")
        line.append("  ".join(extra), style="muted")
    return line


def print_check_line(result: dict, *, service: str | None = None) -> None:
    console().print(render_check_line(result, service=service))


def print_monitor_header(
    *,
    name: str,
    interval: float,
    failure_threshold: int,
    recovery_threshold: int,
) -> None:
    meta = (
        f"fail {failure_threshold}  recover {recovery_threshold}  "
        f"every {interval:g}s"
    )
    body = Text()
    body.append("watching ", style="muted")
    body.append(str(name), style="ink")
    console().print(_session_panel(body, title="sentinel monitor", meta=meta))


def print_banner() -> None:
    from .auth import get_storage_mode, is_logged_in

    mode = get_storage_mode()
    lines: list[Text] = []
    if mode == "none":
        meta = "not initialized"
        lines.append(Text("No store yet. Next:", style="muted"))
        lines.append(_prompt_line("sentinel init"))
        lines.append(_prompt_line("sentinel init --mode supabase"))
    elif mode == "local":
        meta = "local sqlite"
        lines.append(Text("Local identity is active. Login is not required.", style="muted"))
        lines.append(_prompt_line("sentinel demo"))
        lines.append(_prompt_line("sentinel health https://example.com"))
        lines.append(_prompt_line("sentinel services add api https://example.com/health"))
    else:
        meta = "supabase (your project)"
        lines.append(Text("Uses YOUR Supabase project, not a Sentinel-hosted DB.", style="muted"))
        if is_logged_in():
            lines.append(_prompt_line("sentinel services list"))
            lines.append(_prompt_line("sentinel monitor --all"))
        else:
            lines.append(_prompt_line("sentinel login"))
            lines.append(_prompt_line("sentinel schema --print"))
    lines.append(_prompt_line("sentinel doctor"))
    lines.append(_prompt_line("sentinel --help"))
    console().print(_session_panel(Group(*lines), title="sentinel", meta=meta))


def print_incident_card(result: dict) -> None:
    incident_id = result.get("incident_id")
    body = Text()
    body.append_text(status_lamp("INCIDENT"))
    body.append(" OPENED\n", style="bad")
    rows = [
        ("id", str(incident_id)),
        ("severity", str(result.get("incident_severity") or "unknown")),
        ("service", str(result.get("service"))),
        ("detail", str(result.get("error") or "threshold exceeded")),
    ]
    if result.get("diag") or result.get("model_id"):
        rows.append(
            (
                "detect",
                f"diag={result.get('diag') or 'unknown'} "
                f"model={result.get('model_id') or 'warmup'}",
            )
        )
    label_width = max(len(key) for key, _ in rows)
    for key, value in rows:
        body.append(f"{key:<{label_width}}  ", style="muted")
        body.append(f"{value}\n", style="ink")
    body.append("next\n", style="muted")
    commands = (
        f"sentinel incidents show {incident_id}",
        f"sentinel incidents ack {incident_id}",
        f"sentinel postmortem generate {incident_id}",
    )
    for index, command in enumerate(commands):
        body.append_text(_prompt_line(command))
        if index < len(commands) - 1:
            body.append("\n")
    console().print(_session_panel(body, title="incident", meta="opened"))


def print_section(title: str, rows: list[tuple[str, str, str]]) -> None:
    """Doctor/status list: lamp, name, detail."""
    body = Text()
    for state, name, detail in rows:
        body.append_text(status_lamp(state))
        body.append("  ")
        body.append(f"{name}: ", style="ink")
        body.append(f"{detail}\n", style="muted")
    console().print(_session_panel(body, title=title))


def phosphor_table(title: str) -> Table:
    return Table(
        title=title,
        title_style="ink",
        box=box.SIMPLE,
        border_style="muted",
        header_style="ok",
        pad_edge=False,
        expand=True,
        show_lines=False,
    )


def services_table(items: list[dict]) -> Table:
    table = phosphor_table("services")
    table.add_column("Name", style="label")
    table.add_column("URL", overflow="fold", style="muted")
    table.add_column("Status")
    table.add_column("Latency", justify="right", style="muted")
    table.add_column("Checked", style="muted")
    for item in items:
        status = str(item.get("last_status", "unknown"))
        table.add_row(
            str(item.get("name", "Unnamed")),
            str(item.get("url", "")),
            status_lamp(status),
            f"{item.get('last_response_time_ms') or 0}ms",
            str(item.get("last_checked_at") or "never")[:19].replace("T", " "),
        )
    return table


def projects_table(items: list[dict]) -> Table:
    table = phosphor_table("projects")
    table.add_column("Name", style="label")
    table.add_column("Description", style="muted")
    table.add_column("Created", style="muted")
    for item in items:
        table.add_row(
            str(item.get("name", "Unnamed")),
            str(item.get("description", "")),
            str(item.get("created_at", ""))[:10],
        )
    return table


def incidents_table(items: list[dict]) -> Table:
    table = phosphor_table("incidents")
    table.add_column("ID", no_wrap=True, style="muted")
    table.add_column("Severity")
    table.add_column("Service", style="ink")
    table.add_column("Status", style="muted")
    table.add_column("Detected", style="muted")
    for item in items:
        severity = str(item.get("severity", "unknown")).lower()
        lamp_state = "DEGRADED" if severity in {"critical", "high"} else "WATCH"
        if severity in {"low"}:
            lamp_state = "HEALTHY"
        sev = Text()
        sev.append_text(status_lamp(lamp_state))
        sev.append(" ")
        sev.append(severity, style=_STATE_STYLE.get(lamp_state, "muted"))
        table.add_row(
            str(item.get("id", ""))[:12],
            sev,
            _service_name(item),
            str(item.get("status", "unknown")),
            str(item.get("detected_at", ""))[:19].replace("T", " "),
        )
    return table


def incident_detail(incident: dict, events: list[dict]) -> Group:
    service = incident.get("services") or {}
    body = Text()
    fields = [
        ("id", incident.get("id")),
        ("service", service.get("name") or incident.get("service_name", "unknown")),
        ("url", service.get("url") or incident.get("service_url", "unknown")),
        ("status", incident.get("status")),
        ("severity", incident.get("severity")),
        ("error", incident.get("error_message") or "n/a"),
    ]
    label_width = max(len(key) for key, _ in fields)
    for key, value in fields:
        body.append(f"{key:<{label_width}}  ", style="muted")
        body.append(f"{value}\n", style="ink")
    timeline = phosphor_table("timeline")
    timeline.add_column("Time", style="muted")
    timeline.add_column("Event", style="ink")
    for event in events:
        timeline.add_row(
            str(event.get("created_at") or event.get("timestamp") or "")[:19].replace("T", " "),
            f"{event.get('event_type', 'event')}: {event.get('description', '')}",
        )
    return Group(_session_panel(body, title="incident"), timeline)


def dashboard_table(items: list[dict]) -> Table:
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
    table = phosphor_table(f"dashboard  {stamp}")
    table.add_column("Service", style="label")
    table.add_column("URL", overflow="fold", style="muted")
    table.add_column("Status")
    table.add_column("Latency", justify="right", style="muted")
    table.add_column("Detail", style="muted")
    for item in items:
        healthy = item.get("healthy", False)
        state = "HEALTHY" if healthy else ("DEGRADED" if item.get("status_code") else "DOWN")
        table.add_row(
            str(item.get("name", "unknown")),
            str(item.get("url", "")),
            status_lamp(state),
            f"{item.get('latency_ms') or 0:.0f}ms",
            str(item.get("error") or item.get("status_code") or ""),
        )
    return table
