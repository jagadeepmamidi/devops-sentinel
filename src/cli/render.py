"""Presentation primitives for the DevOps Sentinel CLI.

The renderer deliberately keeps data preparation separate from terminal output so
commands can remain useful in JSON, CI, and interactive terminals alike.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import click

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


@dataclass(frozen=True)
class Presentation:
    """Resolved output capabilities for one CLI invocation."""

    json: bool = False
    plain: bool = False
    no_color: bool = False
    quiet: bool = False
    verbose: bool = False
    interactive: bool = False
    width: int = 80
    unicode: bool = False

    @property
    def color(self) -> bool:
        return not self.no_color and self.interactive and not self.plain


def _is_tty() -> bool:
    try:
        return bool(click.get_text_stream("stdout").isatty())
    except (AttributeError, OSError):
        return False


def presentation_from_context(ctx: click.Context | None = None) -> Presentation:
    """Resolve flags and terminal capabilities, with safe non-TTY defaults."""
    values = (ctx.obj if ctx and isinstance(ctx.obj, dict) else {}) or {}
    interactive = bool(values.get("interactive", _is_tty()))
    no_color = bool(values.get("no_color", False))
    no_color = no_color or "NO_COLOR" in os.environ or os.getenv("TERM") == "dumb"
    encoding = getattr(sys.stdout, "encoding", "") or ""
    unicode_ok = interactive and encoding.lower().replace("-", "") not in {"ascii", "usascii"}
    return Presentation(
        json=bool(values.get("json", False)),
        plain=bool(values.get("plain", False)),
        no_color=no_color,
        quiet=bool(values.get("quiet", False)),
        verbose=bool(values.get("verbose", False)),
        interactive=interactive,
        width=max(40, int(values.get("width", shutil.get_terminal_size((80, 20)).columns))),
        unicode=unicode_ok,
    )


def emit_json(value: Any) -> None:
    """Write machine-readable data to stdout without styling or commentary."""
    click.echo(json.dumps(value, indent=2, default=str, ensure_ascii=False))


def emit_error(message: str, next_step: str | None = None, *, exit_code: int = 1) -> None:
    """Write an actionable error to stderr and stop the command."""
    click.echo(f"Error: {message}", err=True)
    if next_step:
        click.echo(f"Next: {next_step}", err=True)
    raise click.exceptions.Exit(exit_code)


def emit_warning(message: str, next_step: str | None = None) -> None:
    """Write a non-fatal diagnostic to stderr."""
    click.echo(f"! WARNING  {message}", err=True)
    if next_step:
        click.echo(f"Next: {next_step}", err=True)


def styled(text: str, color: str | None = None, *, bold: bool = False, p: Presentation | None = None) -> str:
    """Apply semantic color only when the resolved output supports it."""
    p = p or Presentation(interactive=_is_tty())
    if not p.color:
        return text
    return click.style(text, fg=color, bold=bold)


def marker(status: str, p: Presentation | None = None) -> str:
    """Return a textual status marker with an ASCII fallback."""
    p = p or Presentation(interactive=_is_tty())
    key = str(status or "unknown").lower().replace("_", " ")
    symbols = {
        "healthy": ("●", "HEALTHY", "green"),
        "ready": ("✓", "READY", "green"),
        "connected": ("✓", "CONNECTED", "green"),
        "degraded": ("▲", "DEGRADED", "yellow"),
        "warning": ("!", "WARNING", "yellow"),
        "warn": ("!", "WARNING", "yellow"),
        "down": ("✕", "DOWN", "red"),
        "fail": ("✕", "FAILED", "red"),
        "failed": ("✕", "FAILED", "red"),
        "unreachable": ("✕", "UNREACHABLE", "red"),
        "not configured": ("○", "NOT CONFIGURED", "yellow"),
        "not running": ("○", "NOT RUNNING", "yellow"),
        "optional": ("○", "OPTIONAL", "yellow"),
        "info": ("·", "INFO", "blue"),
        "ok": ("✓", "READY", "green"),
        "p0": ("✕", "P0 CRITICAL", "red"),
        "p1": ("▲", "P1 HIGH", "yellow"),
        "p2": ("!", "P2 MEDIUM", "yellow"),
        "p3": ("·", "P3 LOW", "white"),
        "unknown": ("?", "UNKNOWN", "white"),
    }
    symbol, label, color = symbols.get(key, ("?", key.upper(), "white"))
    if not p.unicode:
        symbol = {"●": "*", "✓": "OK", "▲": "!", "✕": "X", "○": "-", "·": "-"}.get(symbol, symbol)
    return styled(f"{symbol} {label}", color, bold=True, p=p)


def heading(title: str, p: Presentation | None = None) -> None:
    p = p or Presentation(interactive=_is_tty())
    click.echo(styled(title, "cyan", bold=True, p=p))


def key_values(values: Mapping[str, Any], p: Presentation | None = None) -> None:
    p = p or Presentation(interactive=_is_tty())
    if not values:
        return
    label_width = max(len(str(k)) for k in values)
    for key, value in values.items():
        click.echo(f"  {styled(str(key), 'bright_black', p=p):<{label_width}}  {value}")


def short_id(value: Any, length: int = 10) -> str:
    text = str(value or "")
    return text if len(text) <= length else f"{text[:length]}…"


def format_timestamp(value: Any) -> str:
    if not value:
        return "—"
    text = str(value).replace("T", " ").replace("+00:00", "Z")
    return text[:19] + (" UTC" if "UTC" not in text and not text.endswith("Z") else "")


def format_latency(value: Any) -> str:
    if value in (None, "", 0, "0"):
        return "—"
    try:
        number = float(value)
        return f"{number:.0f} ms" if number.is_integer() else f"{number:.2f} ms"
    except (TypeError, ValueError):
        return str(value)


def _plain_width(value: Any) -> int:
    return len(ANSI_RE.sub("", str(value)))


def _truncate(value: Any, width: int) -> str:
    text = str(value or "—")
    if width < 2 or len(text) <= width:
        return text[:width]
    return text[: width - 1] + "…"


def table(
    headers: Sequence[str],
    rows: Iterable[Sequence[Any]],
    p: Presentation | None = None,
    *,
    narrow_columns: Sequence[int] | None = None,
    min_widths: Sequence[int] | None = None,
) -> None:
    """Render a borderless, width-aware table suitable for terminals and logs."""
    p = p or Presentation(interactive=_is_tty())
    rows = [list(row) for row in rows]
    columns = list(range(len(headers)))
    if p.width < 80 and narrow_columns:
        columns = list(narrow_columns)
    visible_headers = [headers[index] for index in columns]
    visible_rows = [[row[index] if index < len(row) else "—" for index in columns] for row in rows]
    widths = [max(_plain_width(header), *(min(_plain_width(row[i]), 42) for row in visible_rows)) for i, header in enumerate(visible_headers)]
    if min_widths:
        widths = [max(width, min_widths[index]) for index, width in enumerate(widths)]
    available = max(20, p.width - (2 * (len(widths) - 1)) - 2)
    while sum(widths) > available and max(widths) > 10:
        widest = max(range(len(widths)), key=widths.__getitem__)
        widths[widest] -= 1
    formatted_headers = [styled(_truncate(header, widths[i]), "cyan", bold=True, p=p) for i, header in enumerate(visible_headers)]
    click.echo("  " + "  ".join(f"{item:<{widths[i]}}" for i, item in enumerate(formatted_headers)))
    if p.interactive and not p.plain:
        click.echo("  " + "  ".join(styled("─" * widths[i], "bright_black", p=p) for i in range(len(widths))))
    for row in visible_rows:
        values = [_truncate(row[i], widths[i]) for i in range(len(widths))]
        click.echo("  " + "  ".join(f"{value:<{widths[i]}}" for i, value in enumerate(values)))


def empty_state(message: str, next_step: str | None = None, p: Presentation | None = None) -> None:
    p = p or Presentation(interactive=_is_tty())
    click.echo(message)
    if next_step and not p.quiet:
        click.echo(f"Next: {next_step}")


def render_root(*, mode: str, data_path: str, initialized: bool, p: Presentation | None = None) -> None:
    p = p or Presentation(interactive=_is_tty())
    heading("DevOps Sentinel", p)
    click.echo("Local-first SRE monitoring and incident response")
    key_values({"Mode": mode, "Project": data_path}, p)
    if not initialized:
        click.echo()
        click.echo(styled("Get started", "cyan", bold=True, p=p))
        click.echo("  sentinel init --mode local")
    click.echo()
    click.echo(styled("Common commands", "cyan", bold=True, p=p))
    click.echo("  sentinel health <url>       Check an endpoint once")
    click.echo("  sentinel monitor <url>     Watch an endpoint continuously")
    click.echo("  sentinel services list     List registered services")
    click.echo("  sentinel incidents list    Review active incidents")
    click.echo("  sentinel --help            Show all commands")


def render_health(result: Mapping[str, Any], p: Presentation | None = None) -> None:
    p = p or Presentation(interactive=_is_tty())
    if p.json:
        emit_json(result)
        return
    status = result.get("status", "unknown")
    badge = marker(status, p)
    url = result.get("url", "")
    code = f"HTTP {result['status_code']}" if result.get("status_code") else "no response"
    latency = format_latency(result.get("latency_ms"))
    click.echo(f"{badge}  {url}  {code}  {latency}")
    if result.get("timestamp") and not p.quiet:
        click.echo(f"  Checked {format_timestamp(result['timestamp'])}")
    if result.get("error") and not p.quiet:
        click.echo(f"  Error: {result['error']}")
    if status in {"degraded", "down", "failed", "unreachable"} and not p.quiet:
        suggestion = result.get("suggestion", "verify DNS, network access, and the configured timeout")
        click.echo(f"  Next: {suggestion}.")


def render_services(items: Sequence[Mapping[str, Any]], p: Presentation | None = None) -> None:
    p = p or Presentation(interactive=_is_tty())
    if p.json:
        emit_json(list(items))
        return
    heading("Monitored services", p)
    if not items:
        empty_state("No monitored services yet.", "sentinel services add my-api https://example.com/health", p)
        return
    rank = {"down": 0, "degraded": 1, "healthy": 2}
    ordered = sorted(items, key=lambda item: rank.get(str(item.get("last_status", "unknown")).lower(), 3))
    rows = []
    for item in ordered:
        state = str(item.get("last_status", "unknown")).lower()
        rows.append([
            item.get("name", "Unnamed"), marker(state, p), item.get("url", "—"),
            format_latency(item.get("avg_response_time")),
            f"{item.get('check_interval', '—')} s", format_timestamp(item.get("last_checked_at")),
            short_id(item.get("id")),
        ])
    table(["Name", "Status", "Endpoint", "Latency", "Interval", "Last checked", "ID"], rows, p, narrow_columns=[0, 1, 3, 6])


def render_projects(items: Sequence[Mapping[str, Any]], p: Presentation | None = None) -> None:
    p = p or Presentation(interactive=_is_tty())
    if p.json:
        emit_json(list(items))
        return
    heading("Projects", p)
    if not items:
        empty_state("No projects yet.", "sentinel projects create <name>", p)
        return
    rows = [[item.get("name", "Unnamed"), short_id(item.get("id")), format_timestamp(item.get("created_at")), item.get("description", "—")] for item in items]
    table(["Name", "ID", "Created", "Description"], rows, p, narrow_columns=[0, 1, 2])


def render_incidents(items: Sequence[Mapping[str, Any]], p: Presentation | None = None, *, severity: str | None = None, status: str | None = None) -> None:
    p = p or Presentation(interactive=_is_tty())
    if p.json:
        emit_json(list(items))
        return
    heading("Incidents", p)
    if severity or status:
        filters = ", ".join(filter(None, [f"severity={severity}" if severity else "", f"status={status}" if status else ""]))
        click.echo(f"  Filter: {filters}")
    if not items:
        empty_state("No incidents match the current filters." if (severity or status) else "No incidents found.", "sentinel monitor <url>", p)
        return
    severity_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    ordered = sorted(items, key=lambda item: (str(item.get("status", "open")).lower() == "resolved", severity_rank.get(str(item.get("severity", "")).upper(), 9)))
    rows = []
    for item in ordered:
        service = item.get("services") or {}
        sev = str(item.get("severity", "unknown")).upper()
        rows.append([
            f"{sev} {marker('failed' if sev in {'P0', 'P1'} else 'warning', p).split(' ', 1)[-1]}",
            str(item.get("status", "unknown")).upper(), service.get("name", "unknown"),
            item.get("title") or item.get("summary") or item.get("description", "—"),
            format_timestamp(item.get("detected_at") or item.get("created_at")), short_id(item.get("id")),
        ])
    table(["Severity", "Status", "Service", "Summary", "Detected", "ID"], rows, p, narrow_columns=[0, 1, 2, 5])


def render_status(data: Mapping[str, Any], p: Presentation | None = None) -> None:
    p = p or Presentation(interactive=_is_tty())
    if p.json:
        emit_json(data)
        return
    heading("Sentinel status", p)
    click.echo("Core")
    key_values(data.get("core", {}), p)
    click.echo("\nOptional integrations")
    for name, item in data.get("optional", {}).items():
        click.echo(f"  {marker(item.get('state', 'unknown'), p)}  {name}: {item.get('detail', '')}")


def render_doctor(data: Mapping[str, Any], p: Presentation | None = None) -> None:
    p = p or Presentation(interactive=_is_tty())
    if p.json:
        emit_json(data)
        return
    heading("Sentinel doctor", p)
    click.echo(f"Overall: {marker('ready' if data.get('passed') else 'failed', p)}")
    click.echo(f"  Passed {data.get('passed_count', 0)}  ·  Warnings {data.get('warning_count', 0)}  ·  Failed {data.get('failed_count', 0)}")
    if data.get("strict"):
        click.echo("  Strict mode: warnings fail the command")
    for item in data.get("checks", []):
        click.echo(f"  {marker(item.get('status', 'unknown'), p)}  {item.get('name')}: {item.get('detail')}")
        if item.get("remediation") and item.get("status") in {"warn", "fail"}:
            click.echo(f"    Next: {item['remediation']}")
    if not data.get("passed"):
        click.echo("Next: sentinel doctor --strict" if not data.get("strict") else "Next: fix the failed checks, then run sentinel doctor")


def render_config(items: Sequence[Mapping[str, Any]], p: Presentation | None = None) -> None:
    p = p or Presentation(interactive=_is_tty())
    if p.json:
        emit_json(list(items))
        return
    heading("Configuration", p)
    click.echo("Precedence: process environment → project .env → user config → defaults")
    rows = [[item["setting"], item["value"], item["source"], item["required"]] for item in items]
    table(["Setting", "Value", "Source", "Required"], rows, p, narrow_columns=[0, 1, 3])


def render_dashboard(items: Sequence[Mapping[str, Any]], *, refresh: int, p: Presentation | None = None) -> None:
    p = p or Presentation(interactive=_is_tty())
    counts = {state: sum(str(item.get("last_status", "unknown")).lower() == state for item in items) for state in ("healthy", "degraded", "down")}
    data = {"services": list(items), "counts": counts, "refresh_seconds": refresh, "last_refresh": datetime.now(timezone.utc).isoformat()}
    if p.json:
        emit_json(data)
        return
    heading("Sentinel dashboard", p)
    click.echo(f"UTC {format_timestamp(data['last_refresh'])}  ·  refresh {refresh}s  ·  services {len(items)}")
    click.echo(f"  Healthy {counts['healthy']}  ·  Degraded {counts['degraded']}  ·  Down {counts['down']}")
    if not items:
        empty_state("No monitored services yet.", "sentinel services add my-api https://example.com/health", p)
        return
    rows = [[item.get("name", "Unnamed"), marker(item.get("last_status", "unknown"), p), format_latency(item.get("avg_response_time")), format_timestamp(item.get("last_checked_at"))] for item in items]
    table(["Service", "State", "Latency", "Last checked"], rows, p, narrow_columns=[0, 1, 2])
