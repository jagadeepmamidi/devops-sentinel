"""Click entry point for the DevOps Sentinel operator console."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import click
import httpx
from dotenv import load_dotenv

from .. import __version__
from .auth import (
    ensure_default_user,
    get_active_user,
    get_current_user,
    is_logged_in,
    load_user_config,
    load_local_config_into_env,
    login,
    logout,
    save_user_config,
    whoami,
)
from .db import get_db
from .projects import projects
from .render import (
    emit_error,
    emit_json,
    emit_warning,
    format_timestamp,
    marker,
    presentation_from_context,
    render_config,
    render_dashboard,
    render_doctor,
    render_health,
    render_incidents,
    render_root,
    render_status,
)
from .services import services

load_dotenv()
load_local_config_into_env()


def _mode() -> str:
    configured_mode = load_user_config().get("mode")
    if configured_mode in {"local", "supabase"}:
        return configured_mode
    return "supabase" if os.getenv("SUPABASE_URL") and (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")) else "local"


def print_banner() -> None:
    """Compatibility wrapper retained for callers of the old helper."""
    p = presentation_from_context()
    if not p.json:
        render_root(mode=_mode(), data_path=str(Path.cwd()), initialized=Path(".env").exists(), p=p)


def _api_url() -> str:
    return os.getenv("API_URL", "http://localhost:8000").rstrip("/")


def _settings(ctx: click.Context):
    return presentation_from_context(ctx)


@click.group(
    invoke_without_command=True,
    context_settings={"max_content_width": 100, "help_option_names": ["-h", "--help"]},
)
@click.version_option(version=__version__, prog_name="DevOps Sentinel")
@click.option("--json", "output_json", is_flag=True, help="Emit machine-readable JSON on stdout.")
@click.option("--plain", is_flag=True, help="Stable human-readable output without styling.")
@click.option("--no-color", is_flag=True, help="Disable ANSI color output.")
@click.option("--quiet", "quiet", "-q", is_flag=True, help="Print only essential results.")
@click.option("--verbose", "verbose", "-v", is_flag=True, help="Show additional diagnostic details.")
@click.pass_context
def cli(ctx: click.Context, output_json: bool, plain: bool, no_color: bool, quiet: bool, verbose: bool) -> None:
    """DevOps Sentinel — local-first SRE monitoring and incident response.

    OBSERVE
      health, monitor, dashboard

    MANAGE
      services, projects

    RESPOND
      incidents, postmortem

    CONFIGURE
      init, setup, config, login, logout

    DIAGNOSE / INTEGRATE
      status, doctor, serve, whoami

    Examples:
      sentinel health https://api.example.com/health
      sentinel --json status
      sentinel services list --plain
    """
    ctx.ensure_object(dict)
    ctx.obj.update({"json": output_json, "plain": plain, "no_color": no_color, "quiet": quiet, "verbose": verbose})
    ctx.obj["interactive"] = not plain and not output_json and click.get_text_stream("stdout").isatty()
    if ctx.invoked_subcommand is None:
        p = _settings(ctx)
        if p.json:
            return
        if p.interactive:
            render_root(mode=_mode(), data_path=str(Path.cwd()), initialized=Path(".env").exists(), p=p)
        elif not p.quiet:
            click.echo("DevOps Sentinel — run `sentinel --help` to get started.")


async def _health_request(url: str, timeout: int) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
        elapsed = (datetime.now(timezone.utc) - started).total_seconds() * 1000
        healthy = response.status_code == 200
        return {
            "url": url, "status": "healthy" if healthy else "degraded", "status_code": response.status_code,
            "latency_ms": round(elapsed, 2), "healthy": healthy,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:  # noqa: BLE001 - network clients expose varied transport errors
        return {
            "url": url, "status": "unreachable", "healthy": False, "error": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "suggestion": "verify DNS, network access, and the configured timeout",
        }


@cli.command()
@click.argument("url")
@click.option("--timeout", "-t", default=10, type=click.IntRange(min=1), show_default=True, help="Request timeout in seconds.")
@click.pass_context
def health(ctx: click.Context, url: str, timeout: int) -> None:
    """Run one health check on URL."""
    result = asyncio.run(_health_request(url, timeout))
    render_health(result, _settings(ctx))
    if not result["healthy"]:
        raise click.exceptions.Exit(1)


@cli.command()
@click.argument("url")
@click.option("--interval", "-i", default=30, type=click.IntRange(min=1), show_default=True, help="Check interval in seconds.")
@click.option("--timeout", "-t", default=10, type=click.IntRange(min=1), show_default=True, help="Request timeout in seconds.")
@click.option("--notify", is_flag=True, help="Send Slack notification on state changes.")
@click.pass_context
def monitor(ctx: click.Context, url: str, interval: int, timeout: int, notify: bool) -> None:
    """Monitor a URL continuously; Ctrl+C leaves a clean summary."""
    p = _settings(ctx)
    check_count = 0
    started = datetime.now(timezone.utc)

    async def run() -> None:
        nonlocal check_count
        last_state = None
        notify_warned = False
        async with httpx.AsyncClient(timeout=timeout) as client:
            while True:
                check_count += 1
                check_started = datetime.now(timezone.utc)
                try:
                    response = await client.get(url)
                    latency = (datetime.now(timezone.utc) - check_started).total_seconds() * 1000
                    state = "healthy" if response.status_code == 200 else "degraded"
                    result = {"url": url, "status": state, "status_code": response.status_code, "latency_ms": round(latency, 2), "check": check_count, "timestamp": datetime.now(timezone.utc).isoformat()}
                except Exception as exc:  # noqa: BLE001 - network clients expose varied transport errors
                    state = "down"
                    result = {"url": url, "status": state, "error": str(exc), "check": check_count, "timestamp": datetime.now(timezone.utc).isoformat()}
                if last_state and last_state != state:
                    result["transition"] = f"{last_state.upper()} → {state.upper()}"
                render_health(result, p)
                if notify and not os.getenv("SLACK_WEBHOOK_URL") and not notify_warned:
                    emit_warning("--notify was set but SLACK_WEBHOOK_URL is missing.")
                    notify_warned = True
                last_state = state
                await asyncio.sleep(interval)

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        if not p.json:
            duration = datetime.now(timezone.utc) - started
            click.echo(f"Stopped after {check_count} checks ({duration}).")


@cli.group()
def incidents() -> None:
    """List and respond to incidents."""


def _logged_in_incidents(limit: int = 10, severity: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
    user = get_active_user()
    db = get_db()
    if not user or not db.connected:
        return []
    return db.list_incidents(user["id"], limit=limit, severity=severity, status=status)


@incidents.command("list")
@click.option("--limit", "-n", default=10, type=click.IntRange(min=1), show_default=True, help="Number of incidents to show.")
@click.option("--severity", "-s", type=click.Choice(["P0", "P1", "P2", "P3"]), help="Filter by severity.")
@click.option("--status", type=click.Choice(["open", "acknowledged", "resolved"]), help="Filter by status.")
@click.pass_context
def incidents_list(ctx: click.Context, limit: int, severity: str | None, status: str | None) -> None:
    """List recent incidents."""
    render_incidents(_logged_in_incidents(limit, severity, status), _settings(ctx), severity=severity, status=status)


def _get_incident_or_fail(incident_id: str):
    if not get_db().connected:
        emit_error("incident storage is unavailable", "run `sentinel setup` or configure Supabase")
    incident = get_db().get_incident(incident_id)
    if not incident:
        emit_error(f"incident {incident_id} was not found", "run `sentinel incidents list`")
    return incident


@incidents.command("show")
@click.argument("incident_id")
@click.pass_context
def incidents_show(ctx: click.Context, incident_id: str) -> None:
    """Show incident facts and the response timeline."""
    incident = _get_incident_or_fail(incident_id)
    p = _settings(ctx)
    if p.json:
        emit_json(incident)
        return
    service = incident.get("services") or {}
    click.echo(f"{marker(incident.get('severity', 'warning'), p)}  {incident.get('title') or incident.get('summary', 'Incident')}")
    click.echo(f"  ID: {incident.get('id', incident_id)}")
    click.echo(f"  Service: {service.get('name', 'unknown')}  Status: {str(incident.get('status', 'unknown')).upper()}")
    click.echo(f"  Endpoint: {service.get('url', '—')}")
    click.echo(f"  Detected: {format_timestamp(incident.get('detected_at') or incident.get('created_at'))}")
    click.echo(f"  Error: {incident.get('latest_error') or incident.get('description') or '—'}")
    events = incident.get("timeline") or incident.get("events") or []
    if events:
        click.echo("\nTimeline")
        for event in events:
            click.echo(f"  {format_timestamp(event.get('timestamp'))}  {event.get('type', 'event')}: {event.get('description', '')}")
    if not p.quiet:
        click.echo("\nNext: sentinel incidents acknowledge <id>  or  sentinel incidents resolve <id>")


def _incident_action(ctx: click.Context, incident_id: str, updates: dict[str, Any], action: str) -> None:
    incident = _get_incident_or_fail(incident_id)
    if not get_db().update_incident(incident_id, updates):
        emit_error(f"could not {action} incident {incident_id}", "run `sentinel incidents show <id>`")
    result = {**incident, **updates}
    p = _settings(ctx)
    if p.json:
        emit_json(result)
        return
    click.echo(f"{marker(updates['status'], p)}  Incident {incident_id} is now {updates['status']}.")
    click.echo(f"Next: sentinel incidents show {incident_id}")


@incidents.command("acknowledge")
@click.argument("incident_id")
@click.pass_context
def incidents_acknowledge(ctx: click.Context, incident_id: str) -> None:
    """Acknowledge an open incident."""
    _incident_action(ctx, incident_id, {"status": "acknowledged"}, "acknowledge")


@incidents.command("resolve")
@click.argument("incident_id")
@click.pass_context
def incidents_resolve(ctx: click.Context, incident_id: str) -> None:
    """Resolve an incident."""
    _incident_action(ctx, incident_id, {"status": "resolved", "resolved_at": datetime.now(timezone.utc).isoformat()}, "resolve")


@incidents.command("export")
@click.argument("incident_id")
@click.option("--output", "-o", type=click.Path(dir_okay=False), required=True, help="Output JSON file.")
@click.pass_context
def incidents_export(ctx: click.Context, incident_id: str, output: str) -> None:
    """Export an incident as JSON."""
    incident = _get_incident_or_fail(incident_id)
    path = Path(output).expanduser().resolve()
    path.write_text(json.dumps(incident, indent=2, default=str), encoding="utf-8")
    p = _settings(ctx)
    if p.json:
        emit_json({"incident_id": incident_id, "output": str(path)})
    else:
        click.echo(f"{marker('ready', p)} Incident exported to {path}")


@cli.group()
def postmortem() -> None:
    """Generate and view incident postmortems."""


@postmortem.command("generate")
@click.argument("incident_id")
@click.option("--output", "-o", type=click.Path(dir_okay=False), help="Save Markdown to a file.")
@click.pass_context
def postmortem_generate(ctx: click.Context, incident_id: str, output: str | None) -> None:
    """Generate an incident postmortem."""
    text = f"""# Incident Postmortem: {incident_id}

## Summary
Service degradation affecting API response times.

## Timeline
- Detection and response details are available in the incident record.

## Root Cause
Investigation required.

## Action Items
1. [ ] Confirm root cause
2. [ ] Add a regression check
"""
    resolved_output = None
    if output:
        resolved_output = str(Path(output).expanduser().resolve())
        Path(resolved_output).write_text(text, encoding="utf-8")
    p = _settings(ctx)
    if p.json:
        emit_json({"incident_id": incident_id, "output": resolved_output, "stored": False, "markdown": text})
    elif resolved_output:
        click.echo(f"{marker('ready', p)} Postmortem saved to {resolved_output} (not stored in Sentinel)")
    else:
        click.echo(text.rstrip())


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show core state and optional integrations."""
    async def check_api() -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                return (await client.get(f"{_api_url()}/health")).status_code == 200
        except Exception:  # noqa: BLE001 - an unavailable optional integration is a status
            return False

    api_ok = asyncio.run(check_api())
    user = get_current_user() if is_logged_in() else ensure_default_user()
    configured = {
        "supabase": bool(os.getenv("SUPABASE_URL") and (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY"))),
        "ai": bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")),
        "slack": bool(os.getenv("SLACK_WEBHOOK_URL") or os.getenv("SLACK_CLIENT_ID")),
    }
    data = {
        "core": {"mode": _mode(), "identity": user.get("email", "not authenticated") if user else "not authenticated", "storage": "Supabase" if _mode() == "supabase" else "local", "project_path": str(Path.cwd())},
        "optional": {
            "API server": {"state": "connected" if api_ok else "not running", "detail": _api_url()},
            "AI provider": {"state": "ready" if configured["ai"] else "not configured", "detail": "configured" if configured["ai"] else "optional"},
            "Slack": {"state": "ready" if configured["slack"] else "not configured", "detail": "configured" if configured["slack"] else "optional"},
            "Supabase": {"state": "ready" if configured["supabase"] else "not configured", "detail": "configured" if configured["supabase"] else "optional in local mode"},
        },
    }
    render_status(data, _settings(ctx))


def _env_source(key: str) -> str:
    env_file = Path(".env")
    if key in os.environ and env_file.exists() and any(line.lstrip().startswith(f"{key}=") for line in env_file.read_text(errors="ignore").splitlines()):
        return "process environment/.env"
    return "process environment" if key in os.environ else "default"


def _masked(key: str, default: str = "Not set") -> str:
    return "Configured" if os.getenv(key) else default


@cli.command()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Show safe configuration values and their sources."""
    items = []
    for key, default, required in [
        ("API_URL", "http://localhost:8000", "optional"), ("SENTINEL_WEB_URL", "Not set", "optional"),
        ("SUPABASE_URL", "Not set", "optional"), ("SUPABASE_KEY", "Not set", "optional"),
        ("SUPABASE_ANON_KEY", "Not set", "optional"), ("OPENROUTER_API_KEY", "Not set", "optional"),
        ("OPENAI_API_KEY", "Not set", "optional"), ("SLACK_WEBHOOK_URL", "Not set", "optional"),
    ]:
        value = default if key == "API_URL" else _masked(key, default)
        items.append({"setting": key, "value": value, "source": _env_source(key) if value != default or key in os.environ else "default", "required": required})
    render_config(items, _settings(ctx))


@cli.command()
@click.option("--mode", type=click.Choice(["local", "supabase"]), default="local", show_default=True, help="Storage mode to initialize.")
@click.pass_context
def init(ctx: click.Context, mode: str) -> None:
    """Initialize local Sentinel files without prompts."""
    env_path = Path(".env")
    config_path = Path("sentinel.yaml")
    created = []
    if not env_path.exists():
        env_path.write_text("""# DevOps Sentinel Configuration\nSUPABASE_URL=\nSUPABASE_ANON_KEY=\nSENTINEL_WEB_URL=\nOPENROUTER_API_KEY=\nOPENAI_API_KEY=\nSLACK_WEBHOOK_URL=\n""", encoding="utf-8")
        created.append(str(env_path.resolve()))
    if not config_path.exists():
        config_path.write_text(f"version: 1\nmode: {mode}\n\nservices: []\n", encoding="utf-8")
        created.append(str(config_path.resolve()))
    result = {"mode": mode, "created": created, "existing": [str(path.resolve()) for path in (env_path, config_path) if str(path.resolve()) not in created]}
    save_user_config(mode=mode)
    p = _settings(ctx)
    if p.json:
        emit_json(result)
        return
    click.echo("Initializing DevOps Sentinel")
    for path in created:
        click.echo(f"{marker('ready', p)} Created {path}")
    for path in result["existing"]:
        click.echo(f"{marker('warning', p)} Kept existing {path}")
    click.echo("\nNext:\n  sentinel status\n  sentinel health https://example.com/health\n  sentinel doctor")


@cli.command()
@click.pass_context
def setup(ctx: click.Context) -> None:
    """Guide an interactive first-run service setup."""
    p = _settings(ctx)
    if not p.interactive or p.json:
        emit_error("guided setup requires an interactive terminal", "run `sentinel init --mode local` for automation")
    if not Path(".env").exists():
        ctx.invoke(init, mode="local")
    click.echo("Guided setup\n  Configure a first service and run a verification check.\n")
    if not is_logged_in() and click.confirm("Connect a Supabase account now?", default=True):
        ctx.invoke(
            login,
            token=None,
            device=False,
            supabase_url=os.getenv("SUPABASE_URL"),
            web_url=os.getenv("SENTINEL_WEB_URL"),
        )
    authenticated = is_logged_in()
    mode = "supabase" if authenticated else "local"
    if authenticated:
        save_user_config(mode=mode)
        click.echo(f"{marker('ready', p)} Supabase account connected")
    else:
        user = ensure_default_user()
        click.echo(f"{marker('ready', p)} Using local identity {user['email']}")

    if os.getenv("OPENROUTER_API_KEY"):
        click.echo(f"{marker('ready', p)} OpenRouter key is already configured")
    else:
        click.echo("\nOpenRouter provides the AI key used by Sentinel agents:")
        click.echo("  https://openrouter.ai/keys")
        api_key = click.prompt("Paste your OpenRouter API key (leave blank to skip)", default="", hide_input=True, show_default=False)
        if api_key.strip():
            save_user_config(OPENROUTER_API_KEY=api_key.strip(), mode=mode)
            os.environ["OPENROUTER_API_KEY"] = api_key.strip()
            click.echo(f"{marker('ready', p)} OpenRouter key saved securely in the user config")
        else:
            click.echo(f"{marker('warning', p)} No AI key saved; health monitoring still works")
    name = click.prompt("Service name", default="my-api")
    url = click.prompt("Service health URL", default="https://api.example.com/health")
    if "://" not in url:
        url = f"https://{url}"
    if not url.startswith(("http://", "https://")):
        emit_error("service URL must start with http:// or https://", "enter a valid health endpoint")
    interval = click.prompt("Check interval seconds", type=click.IntRange(min=1), default=30)
    registered = False
    if get_db().connected:
        user = get_current_user() or ensure_default_user()
        service = get_db().add_service(user["id"], name, url, check_interval=interval)
        registered = bool(service)
        storage = "Supabase" if is_logged_in() else "local storage"
        click.echo(f"{marker('ready' if registered else 'warning', p)} {'Registered service in ' + storage if registered else 'Could not register service'}")
    else:
        click.echo(f"{marker('warning', p)} Could not register service")
    result = asyncio.run(_health_request(url, 10))
    click.echo(f"{marker(result['status'], p)} Initial health check {'passed' if result['healthy'] else 'needs attention'}")
    click.echo("\nNext:\n  sentinel services list\n  sentinel doctor")
    if click.confirm("Start monitoring this website now?", default=True):
        click.echo(f"Starting monitor for {url}; press Ctrl+C to stop.")
        ctx.invoke(monitor, url=url, interval=interval, timeout=10, notify=False)


@cli.command()
@click.option("--strict", is_flag=True, help="Treat warnings as failures.")
@click.pass_context
def doctor(ctx: click.Context, strict: bool) -> None:
    """Run environment and connectivity diagnostics."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    supabase_partial = bool(supabase_url) != bool(supabase_key)
    api_url = _api_url()

    async def check_api() -> bool:
        try:
            async with httpx.AsyncClient(timeout=4) as client:
                return (await client.get(f"{api_url}/health")).status_code == 200
        except Exception:  # noqa: BLE001 - an unavailable optional integration is a status
            return False

    api_ok = asyncio.run(check_api())
    auth_ok = is_logged_in()
    user = get_current_user() if auth_ok else None
    ai_configured = bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"))
    checks = [
        {"name": "Storage mode", "status": "ready", "detail": f"{_mode()} (local storage is supported)"},
        {"name": "Supabase configuration", "status": "fail" if supabase_partial else ("ready" if supabase_url and supabase_key else "warn"), "detail": "Configured" if supabase_url and supabase_key else "Optional in local mode", "remediation": "set SUPABASE_URL and SUPABASE_ANON_KEY together" if supabase_partial else None},
        {"name": "CLI login", "status": "ready" if auth_ok else "warn", "detail": f"Logged in as {user.get('email', 'unknown')}" if user else "Not logged in (optional for local mode)", "remediation": "sentinel login" if not auth_ok else None},
        {"name": "API health", "status": "ready" if api_ok else "warn", "detail": f"{api_url}/health reachable" if api_ok else f"API not reachable at {api_url}/health", "remediation": "sentinel serve" if not api_ok else None},
        {"name": "AI provider", "status": "ready" if ai_configured else "warn", "detail": "Configured" if ai_configured else "Optional and not configured", "remediation": "set OPENROUTER_API_KEY or OPENAI_API_KEY" if not ai_configured else None},
    ]
    failed_count = sum(item["status"] == "fail" for item in checks)
    warning_count = sum(item["status"] == "warn" for item in checks)
    passed = failed_count == 0 and (warning_count == 0 if strict else True)
    data = {"checks": checks, "strict": strict, "passed": passed, "passed_count": len(checks) - failed_count - warning_count, "failed_count": failed_count, "warning_count": warning_count}
    render_doctor(data, _settings(ctx))
    if not passed:
        raise click.exceptions.Exit(1)


@cli.command()
@click.option("--refresh", default=10, type=click.IntRange(min=1), show_default=True, help="Refresh interval in seconds.")
@click.option("--once", is_flag=True, help="Render one snapshot and exit.")
@click.pass_context
def dashboard(ctx: click.Context, refresh: int, once: bool) -> None:
    """Show a live service health dashboard in interactive terminals."""
    p = _settings(ctx)
    if not p.interactive or p.json:
        once = True
    try:
        while True:
            items = []
            if get_db().connected:
                user = get_current_user() or ensure_default_user()
                if user:
                    items = get_db().list_services(user["id"])
            render_dashboard(items, refresh=refresh, p=p)
            if once:
                return
            import time
            time.sleep(refresh)
    except KeyboardInterrupt:
        if not p.json:
            click.echo("Dashboard stopped.")


@cli.command()
@click.option(
    "--host",
    default=lambda: os.getenv("API_HOST", "127.0.0.1"),
    show_default="127.0.0.1",
    help="Bind address. Defaults to localhost.",
)
@click.option("--port", default=lambda: int(os.getenv("API_PORT", os.getenv("PORT", "8000"))), show_default=True, help="API port.")
@click.option("--reload", is_flag=True, help="Enable auto-reload for local development.")
def serve(host: str, port: int, reload: bool) -> None:
    """Start the optional operator API (localhost by default)."""
    if (host or "").strip() in {"0.0.0.0", "::", "[::]", "*"}:
        click.echo(
            "WARNING: Binding to all interfaces. In local mode the operator API is unauthenticated.",
            err=True,
        )
    cmd = [sys.executable, "-m", "uvicorn", "sentinel.api.app:app", "--host", host, "--port", str(port)]
    if reload:
        cmd.append("--reload")
    click.echo(f"Starting API server on {host}:{port}")
    raise SystemExit(subprocess.call(cmd))


cli.add_command(login)
cli.add_command(logout)
cli.add_command(whoami)
cli.add_command(projects)
cli.add_command(services)


if __name__ == "__main__":
    cli()
