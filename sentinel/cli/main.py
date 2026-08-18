"""
DevOps Sentinel CLI - Main Entry Point
=======================================

Usage:
    sentinel login                   - Authenticate with browser
    sentinel monitor <url>           - Monitor a URL for health
    sentinel incidents list          - List recent incidents
    sentinel postmortem <id>         - View/generate postmortem
    sentinel status                  - Show configuration and connectivity
    sentinel config                  - Show configuration
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import click
import httpx

# Load environment
from dotenv import load_dotenv

from .. import __version__
from ..core.monitoring_policy import (
    MonitoringState,
    MonitoringThresholds,
    advance_monitoring_state,
    seed_monitoring_state,
    should_open_incident,
    should_resolve_incident,
)
from ..core.postmortem_generator import PostmortemGenerator

# Auth module
from .auth import (
    get_current_user,
    get_storage_mode,
    is_logged_in,
    login,
    logout,
    whoami,
)
from .db import get_db

# Projects and Services modules
from .projects import projects
from .services import services

load_dotenv()


def classify_incident(response_code: int | None, error: str = "") -> tuple[str, str]:
    """Map an observed failure into a severity and incident summary."""
    if response_code is None or response_code == 0:
        return "critical", error or "Service unreachable"
    if response_code >= 500:
        return "high", f"Service returned HTTP {response_code}"
    if response_code >= 400:
        return "medium", f"Service returned HTTP {response_code}"
    return "low", error or "Degraded service response"


def print_banner():
    """Print ASCII banner"""
    banner = """
========================================
      DEVOPS SENTINEL - SRE AGENT
========================================
"""
    click.echo(click.style(banner, fg="cyan"))


@click.group()
@click.version_option(version=__version__, prog_name="DevOps Sentinel")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def cli(ctx, output_json):
    """
    DevOps Sentinel - Autonomous SRE Agent

    Monitor services, detect anomalies, and generate AI-powered postmortems.

    Quick start:
    sentinel monitor https://api.example.com/health
    sentinel incidents list
    sentinel postmortem generate <incident-id>
    """
    ctx.ensure_object(dict)
    ctx.obj["json"] = output_json


@cli.command()
@click.argument("url")
@click.option("--interval", "-i", default=30, help="Check interval in seconds")
@click.option("--timeout", "-t", default=10, help="Request timeout in seconds")
@click.option("--notify", is_flag=True, help="Send Slack notification on failure")
@click.option(
    "--failure-threshold",
    default=3,
    type=click.IntRange(1, 20),
    show_default=True,
    help="Failures required before opening an incident",
)
@click.option(
    "--recovery-threshold",
    default=2,
    type=click.IntRange(1, 20),
    show_default=True,
    help="Healthy checks required before resolving an incident",
)
@click.pass_context
def monitor(ctx, url, interval, timeout, notify, failure_threshold, recovery_threshold):
    """
    Monitor a URL for health status.

    Examples:

        sentinel monitor https://api.example.com/health

        sentinel monitor https://httpbin.org/status/200 --interval 60
    """

    async def _monitor():
        if not ctx.obj.get("json"):
            click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Monitoring: {url}")
            click.echo(f"  Interval: {interval}s | Timeout: {timeout}s")
            click.echo("  Press Ctrl+C to stop\n")
            if notify:
                click.echo("  Notifications: enabled")

        check_count = 0
        notify_warned = False
        db = get_db()
        user = get_current_user() if is_logged_in() else None
        service = None
        active_incident_id = None
        thresholds = MonitoringThresholds(
            failure_threshold=failure_threshold,
            recovery_threshold=recovery_threshold,
        )
        state = MonitoringState()

        if user and db.connected:
            service = db.get_service_by_url(user["id"], url)
            if service:
                active_incident = db.get_active_incident_for_service(user["id"], service["id"])
                active_incident_id = active_incident["id"] if active_incident else None
                recent_checks = db.get_latest_health_checks(
                    service["id"],
                    limit=max(failure_threshold, recovery_threshold),
                )
                state = seed_monitoring_state(recent_checks)

        async with httpx.AsyncClient(timeout=timeout) as client:

            async def send_notification(message: str):
                nonlocal notify_warned
                if not notify:
                    return
                webhook = os.getenv("SLACK_WEBHOOK_URL")
                if not webhook:
                    if not notify_warned and not ctx.obj.get("json"):
                        click.echo(
                            click.style(
                                "  WARN --notify set, but SLACK_WEBHOOK_URL is missing.",
                                fg="yellow",
                            )
                        )
                    notify_warned = True
                    return
                try:
                    await client.post(webhook, json={"text": message}, timeout=5)
                except httpx.HTTPError:
                    if not ctx.obj.get("json"):
                        click.echo(
                            click.style("  WARN Failed to send Slack notification.", fg="yellow")
                        )

            while True:
                check_count += 1
                start = datetime.now(timezone.utc).replace(tzinfo=None)

                try:
                    response = await client.get(url)
                    elapsed = (
                        datetime.now(timezone.utc).replace(tzinfo=None) - start
                    ).total_seconds() * 1000
                    status_code = response.status_code
                    is_healthy = status_code == 200
                    state = advance_monitoring_state(state, is_healthy)

                    if service and db.connected:
                        db.log_health_check(service["id"], status_code, int(elapsed), is_healthy)
                        db.update_service_status(
                            service["id"],
                            "healthy" if is_healthy else "degraded",
                            int(elapsed),
                        )

                    if is_healthy:
                        status = click.style("OK HEALTHY", fg="green")
                        if (
                            active_incident_id
                            and db.connected
                            and should_resolve_incident(
                                state,
                                thresholds,
                                has_active_incident=True,
                            )
                        ):
                            db.resolve_incident(
                                active_incident_id,
                                action_plan=(
                                    f"Recovered automatically after {state.consecutive_healthy} "
                                    "consecutive healthy checks."
                                ),
                            )
                            if notify:
                                await send_notification(
                                    f"[DevOps Sentinel] Recovered: {url} is healthy again."
                                )
                            active_incident_id = None
                        if ctx.obj.get("json"):
                            click.echo(
                                json.dumps(
                                    {
                                        "status": "healthy",
                                        "code": status_code,
                                        "latency_ms": round(elapsed, 2),
                                        "healthy_streak": state.consecutive_healthy,
                                        "recovery_threshold": recovery_threshold,
                                        "check": check_count,
                                    }
                                )
                            )
                        else:
                            click.echo(
                                f"  {status} | {status_code} | {elapsed:.0f}ms | "
                                f"Healthy streak {state.consecutive_healthy}/{recovery_threshold} | "
                                f"Check #{check_count}"
                            )
                    else:
                        status = click.style("WARN WARNING", fg="yellow")
                        opened_incident = False
                        if (
                            service
                            and user
                            and db.connected
                            and should_open_incident(
                                state,
                                thresholds,
                                has_active_incident=bool(active_incident_id),
                            )
                        ):
                            severity, detail = classify_incident(status_code)
                            incident = db.create_incident(
                                user["id"],
                                service["id"],
                                severity,
                                detail,
                                error_code=status_code,
                                status="alerting",
                            )
                            active_incident_id = incident["id"] if incident else None
                            opened_incident = active_incident_id is not None
                        if ctx.obj.get("json"):
                            click.echo(
                                json.dumps(
                                    {
                                        "status": "warning",
                                        "code": status_code,
                                        "latency_ms": round(elapsed, 2),
                                        "failure_streak": state.consecutive_failures,
                                        "failure_threshold": failure_threshold,
                                        "incident_opened": opened_incident,
                                        "check": check_count,
                                    }
                                )
                            )
                        else:
                            click.echo(
                                f"  {status} | {status_code} | {elapsed:.0f}ms | "
                                f"Failure streak {state.consecutive_failures}/{failure_threshold} | "
                                f"Check #{check_count}"
                            )
                        if opened_incident:
                            await send_notification(
                                f"[DevOps Sentinel] Incident opened for {url}: HTTP {status_code} ({elapsed:.0f}ms)"
                            )

                except httpx.HTTPError as e:
                    status = click.style("X FAILED", fg="red")
                    state = advance_monitoring_state(state, False)
                    if service and db.connected:
                        db.log_health_check(service["id"], 0, 0, False, str(e))
                        db.update_service_status(service["id"], "down", 0)
                    opened_incident = False
                    if (
                        service
                        and user
                        and db.connected
                        and should_open_incident(
                            state,
                            thresholds,
                            has_active_incident=bool(active_incident_id),
                        )
                    ):
                        severity, detail = classify_incident(None, str(e))
                        incident = db.create_incident(
                            user["id"],
                            service["id"],
                            severity,
                            detail,
                            error_code=None,
                            status="alerting",
                        )
                        active_incident_id = incident["id"] if incident else None
                        opened_incident = active_incident_id is not None
                    if ctx.obj.get("json"):
                        click.echo(
                            json.dumps(
                                {
                                    "status": "failed",
                                    "error": str(e),
                                    "failure_streak": state.consecutive_failures,
                                    "failure_threshold": failure_threshold,
                                    "incident_opened": opened_incident,
                                    "check": check_count,
                                }
                            )
                        )
                    else:
                        click.echo(
                            f"  {status} | {str(e)[:50]} | Failure streak {state.consecutive_failures}/"
                            f"{failure_threshold} | Check #{check_count}"
                        )
                    if opened_incident:
                        await send_notification(
                            f"[DevOps Sentinel] Failure for {url}: {str(e)[:180]}"
                        )

                await asyncio.sleep(interval)

    try:
        asyncio.run(_monitor())
    except KeyboardInterrupt:
        click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Monitoring stopped.")


@cli.command()
@click.argument("url")
@click.option("--timeout", "-t", default=10, help="Request timeout in seconds")
@click.pass_context
def health(ctx, url, timeout):
    """
    Run a single health check on a URL.

    Examples:

        sentinel health https://api.example.com/health

        sentinel health https://httpbin.org/status/200
    """

    async def _check():
        async with httpx.AsyncClient(timeout=timeout) as client:
            start = datetime.now(timezone.utc).replace(tzinfo=None)
            try:
                response = await client.get(url)
                elapsed = (
                    datetime.now(timezone.utc).replace(tzinfo=None) - start
                ).total_seconds() * 1000

                result = {
                    "url": url,
                    "status_code": response.status_code,
                    "latency_ms": round(elapsed, 2),
                    "healthy": response.status_code == 200,
                    "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
                }

                if ctx.obj.get("json"):
                    click.echo(json.dumps(result, indent=2))
                else:
                    if result["healthy"]:
                        click.echo(f"\n{click.style('OK', fg='green')} {url}")
                        click.echo(f"  Status: {click.style('HEALTHY', fg='green')}")
                    else:
                        click.echo(f"\n{click.style('WARN', fg='yellow')} {url}")
                        click.echo(f"  Status: {click.style('DEGRADED', fg='yellow')}")

                    click.echo(f"  Response: {result['status_code']}")
                    click.echo(f"  Latency: {result['latency_ms']}ms")
                    click.echo()

            except httpx.HTTPError as e:
                if ctx.obj.get("json"):
                    click.echo(
                        json.dumps({"url": url, "healthy": False, "error": str(e)}, indent=2)
                    )
                else:
                    click.echo(f"\n{click.style('X', fg='red')} {url}")
                    click.echo(f"  Status: {click.style('UNREACHABLE', fg='red')}")
                    click.echo(f"  Error: {e!s}")
                    click.echo()

    asyncio.run(_check())


@cli.group()
def incidents():
    """Manage and view incidents."""
    return


@incidents.command("list")
@click.option("--limit", "-n", default=10, help="Number of incidents to show")
@click.option(
    "--severity",
    "-s",
    type=click.Choice(["critical", "high", "medium", "low"]),
    help="Filter by severity",
)
@click.option(
    "--status",
    type=click.Choice(["detecting", "alerting", "investigating", "resolved"]),
    help="Filter by status",
)
@click.pass_context
def incidents_list(ctx, limit, severity, status):
    """List recent incidents."""
    incidents_data = []
    if is_logged_in():
        user = get_current_user()
        if user:
            db = get_db()
            if db.connected:
                incidents_data = db.list_incidents(
                    user["id"],
                    limit=limit,
                    severity=severity,
                    status=status,
                )
    if ctx.obj.get("json"):
        click.echo(json.dumps(incidents_data, indent=2, default=str))
        return
    click.echo(f"\n{click.style('Recent Incidents', bold=True)}")
    click.echo("-" * 70)
    click.echo(f"{'ID':<12} {'Severity':<10} {'Service':<20} {'Status':<12} {'Created'}")
    click.echo("-" * 70)
    if not incidents_data:
        click.echo("No incidents found. Add a service and run monitoring to collect incidents.")
        click.echo()
        return
    for inc in incidents_data:
        sev_raw = str(inc.get("severity", "unknown")).lower()
        sev_color = {"critical": "red", "high": "yellow", "medium": "blue", "low": "white"}.get(
            sev_raw, "white"
        )
        sev = click.style(sev_raw, fg=sev_color, bold=True)
        service = (inc.get("services") or {}).get("name", "unknown")[:19]
        created = str(inc.get("detected_at", ""))[:19].replace("T", " ")
        click.echo(
            f"{str(inc.get('id', ''))[:12]:<12} "
            f"{sev:<19} "
            f"{service:<20} "
            f"{inc.get('status', 'unknown'):<12} "
            f"{created}"
        )
    click.echo()


@cli.group()
def postmortem():
    """Generate and view postmortems."""
    return


@postmortem.command("generate")
@click.argument("incident_id")
@click.option("--output", "-o", type=click.Path(), help="Save to file")
@click.pass_context
def postmortem_generate(ctx, incident_id, output):
    """Generate an AI-powered postmortem for an incident."""
    click.echo(
        f"\n{click.style('[SENTINEL]', fg='cyan')} Generating postmortem for {incident_id}..."
    )
    db = get_db()
    incident = db.get_incident(incident_id) if db.connected else None
    if not incident:
        click.echo(click.style("Error: Incident not found or database not configured.", fg="red"))
        raise SystemExit(1)

    postmortem = asyncio.run(
        PostmortemGenerator().generate(
            incident={
                "id": incident["id"],
                "title": incident.get("error_message") or f"Incident {incident['id']}",
                "severity": incident.get("severity", "medium"),
                "service_name": (incident.get("services") or {}).get("name", "Unknown service"),
                "description": incident.get("error_message") or "",
                "detected_at": incident.get("detected_at"),
                "resolved_at": incident.get("resolved_at")
                or datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
            },
            events=[
                {"timestamp": incident.get("detected_at"), "description": "Incident detected"},
                {"timestamp": incident.get("resolved_at"), "description": "Incident resolved"},
            ],
            resolution=incident.get("action_plan"),
        )
    )
    postmortem_text = postmortem["markdown"]
    db.save_postmortem(incident_id, postmortem_text)

    if output:
        Path(output).write_text(postmortem_text)
        click.echo(f"\n{click.style('OK', fg='green')} Postmortem saved to {output}")
    else:
        click.echo(postmortem_text)


@cli.command()
@click.pass_context
def status(ctx):
    """Show current system status."""
    click.echo(f"\n{click.style('DevOps Sentinel Status', bold=True)}")
    click.echo("-" * 40)

    # Check API connection
    api_url = os.getenv("API_URL", "http://localhost:8000")

    async def check_api():
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{api_url}/health")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    api_ok = asyncio.run(check_api())

    storage_mode = get_storage_mode()
    storage_configured = bool(
        storage_mode == "local"
        or (
            os.getenv("SUPABASE_URL")
            and (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY"))
        )
    )
    llm_configured = bool(os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY"))
    slack_configured = bool(os.getenv("SLACK_WEBHOOK_URL") or os.getenv("SLACK_CLIENT_ID"))

    def status_icon(ok):
        return click.style("OK", fg="green") if ok else click.style("X", fg="red")

    click.echo(f"  {status_icon(api_ok)} API Server: {'Connected' if api_ok else 'Not running'}")
    storage_label = "SQLite (local)" if storage_mode == "local" else "Supabase"
    click.echo(
        f"  {status_icon(storage_configured)} Storage [{storage_label}]: {'Ready' if storage_configured else 'Not configured'}"
    )
    click.echo(
        f"  {status_icon(llm_configured)} LLM Provider: {'Configured' if llm_configured else 'Not configured'}"
    )
    click.echo(
        f"  {status_icon(slack_configured)} Slack: {'Configured' if slack_configured else 'Not configured'}"
    )
    click.echo()


@cli.command()
def config():
    """Show current configuration."""
    click.echo(f"\n{click.style('Configuration', bold=True)}")
    click.echo("-" * 40)

    storage_mode = get_storage_mode()
    db = get_db() if storage_mode == "local" else None
    configs = [
        ("SENTINEL_MODE", storage_mode),
        ("SENTINEL_DATA_DIR", os.getenv("SENTINEL_DATA_DIR", "default user data directory")),
        (
            "SENTINEL_DB_PATH",
            str(db.path) if db and db.path else os.getenv("SENTINEL_DB_PATH", "Not set"),
        ),
        ("API_URL", os.getenv("API_URL", "http://localhost:8000")),
        ("SENTINEL_WEB_URL", os.getenv("SENTINEL_WEB_URL", "Not set")),
        (
            "SUPABASE_URL",
            os.getenv("SUPABASE_URL", "Not set")[:50] + "..."
            if os.getenv("SUPABASE_URL")
            else "Not set",
        ),
        (
            "SUPABASE_KEY",
            "***" if (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")) else "Not set",
        ),
        ("OPENROUTER_API_KEY", "***" if os.getenv("OPENROUTER_API_KEY") else "Not set"),
        ("OPENAI_API_KEY", "***" if os.getenv("OPENAI_API_KEY") else "Not set"),
        ("SLACK_WEBHOOK_URL", "***" if os.getenv("SLACK_WEBHOOK_URL") else "Not set"),
    ]

    for key, value in configs:
        click.echo(f"  {key}: {value}")
    click.echo()


@cli.command()
@click.option(
    "--mode",
    type=click.Choice(["local", "supabase"]),
    default="local",
    show_default=True,
    help="Storage mode for this project",
)
def init(mode):
    """Initialize DevOps Sentinel in current directory."""
    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Initializing DevOps Sentinel...")

    env_path = Path(".env")
    env_content = """# DevOps Sentinel Configuration
# Local mode needs no hosted database or account.
SENTINEL_MODE=local
SENTINEL_DATA_DIR=.sentinel

# Supabase compatibility mode (use `sentinel init --mode supabase`)
SUPABASE_URL=
SUPABASE_ANON_KEY=

# Hosted web app used by server-mode browser auth
SENTINEL_WEB_URL=

# AI Provider (optional)
OPENROUTER_API_KEY=
# OPENAI_API_KEY=

# Slack Integration (optional)
SLACK_WEBHOOK_URL=
"""
    if not env_path.exists():
        env_path.write_text(env_content)
        click.echo(f"  {click.style('OK', fg='green')} Created .env file")
    else:
        existing = env_path.read_text(encoding="utf-8")
        lines = existing.splitlines()
        mode_line_found = False
        for index, line in enumerate(lines):
            if line.startswith("SENTINEL_MODE="):
                lines[index] = f"SENTINEL_MODE={mode}"
                mode_line_found = True
                break
        if not mode_line_found:
            lines.append(f"SENTINEL_MODE={mode}")
        if mode == "local" and not any(line.startswith("SENTINEL_DATA_DIR=") for line in lines):
            lines.append("SENTINEL_DATA_DIR=.sentinel")
        env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
        click.echo(f"  {click.style('*', fg='yellow')} .env already exists")
    os.environ["SENTINEL_MODE"] = mode
    if mode == "local":
        os.environ.setdefault("SENTINEL_DATA_DIR", ".sentinel")

    # Create sentinel.yaml config
    config_path = Path("sentinel.yaml")
    if not config_path.exists():
        config_content = """# DevOps Sentinel Configuration
version: 1

services:
  - name: api
    url: http://localhost:8000/health
    interval: 30
    
notifications:
  slack:
    enabled: true
    channel: "#alerts"
    
monitoring:
  anomaly_detection: true
  auto_postmortem: true
"""
        config_path.write_text(config_content)
        click.echo(f"  {click.style('OK', fg='green')} Created sentinel.yaml")
    else:
        click.echo(f"  {click.style('*', fg='yellow')} sentinel.yaml already exists")

    if mode == "local":
        click.echo(
            f"\n{click.style('Done!', fg='green')} Local mode ready. No Supabase or login required."
        )
        click.echo("  sentinel health https://example.com")
        click.echo("  sentinel services add api https://example.com/health")
    else:
        click.echo(
            f"\n{click.style('Done!', fg='green')} Configure SUPABASE_URL and SUPABASE_ANON_KEY, then run:"
        )
        click.echo("  sentinel login")
    click.echo("  sentinel status")
    click.echo()


@cli.command()
@click.option("--strict", is_flag=True, help="Treat warnings as failures")
@click.pass_context
def doctor(ctx, strict):
    """Run environment and connectivity diagnostics."""
    from ..core.doctor import run_doctor

    result = run_doctor(strict=strict)
    checks = result["checks"]
    passed = result["passed"]
    failed = [c for c in checks if c["status"] == "fail"]
    # Warnings are rendered from result checks when needed.

    if ctx.obj.get("json"):
        click.echo(json.dumps(result, indent=2))
        raise SystemExit(1 if not passed else 0)

    icons = {"ok": "OK", "warn": "WARN", "fail": "FAIL"}
    colors = {"ok": "green", "warn": "yellow", "fail": "red"}

    click.echo(f"\n{click.style('Sentinel Doctor', bold=True)}")
    click.echo("-" * 40)
    for item in checks:
        marker = click.style(icons[item["status"]], fg=colors[item["status"]], bold=True)
        click.echo(f"  {marker:<6} {item['name']}: {item['detail']}")
    click.echo()

    if not passed:
        if failed:
            click.echo(
                click.style(
                    "Critical checks failed. Fix required config and re-run `sentinel doctor`.",
                    fg="red",
                )
            )
        else:
            click.echo(click.style("Warnings treated as failures in strict mode.", fg="red"))
        raise SystemExit(1)


@cli.command("mcp")
def mcp_server():
    """Start the MCP server for Cursor / Claude Desktop."""
    from sentinel.mcp.server import main

    main()


@cli.command()
@click.pass_context
def setup(ctx):
    """Guided first-run setup for CLI users."""
    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Guided setup")
    click.echo("  This will configure login, first service, and a quick verification.\n")

    if not Path(".env").exists():
        click.echo("  .env not found, creating defaults...")
        ctx.invoke(init)

    if not is_logged_in() and click.confirm(
        "  You are not logged in. Run browser login now?", default=True
    ):
        ctx.invoke(
            login,
            token=None,
            device=False,
            supabase_url=os.getenv("SUPABASE_URL"),
            web_url=os.getenv("SENTINEL_WEB_URL"),
        )

    service_name = click.prompt("  Service name", default="my-api")
    service_url = click.prompt("  Service health URL", default="https://api.example.com/health")
    check_interval = click.prompt("  Check interval seconds", type=int, default=30)

    registered = False
    db = get_db()
    if is_logged_in() and db.connected:
        user = get_current_user()
        if user and user.get("id"):
            service = db.add_service(
                user["id"], service_name, service_url, check_interval=check_interval
            )
            if service:
                registered = True
                click.echo(click.style("  OK Service registered in local storage.", fg="green"))
            else:
                click.echo(
                    click.style("  WARN Failed to register service in storage.", fg="yellow")
                )
        else:
            click.echo(
                click.style(
                    "  WARN Login state is invalid; run `sentinel login` again.", fg="yellow"
                )
            )
    else:
        click.echo(
            click.style(
                "  WARN Skipping service registration (identity or storage unavailable).",
                fg="yellow",
            )
        )

    async def quick_check():
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(service_url)
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    health_ok = asyncio.run(quick_check())
    click.echo(
        click.style(
            f"  {'OK' if health_ok else 'WARN'} Health check {'passed' if health_ok else 'failed'}",
            fg="green" if health_ok else "yellow",
        )
    )

    click.echo("\n  Next commands:")
    click.echo(f"    sentinel monitor {service_url}")
    if registered:
        click.echo("    sentinel services list")
    click.echo("    sentinel doctor")
    click.echo()


@cli.command()
@click.option(
    "--host", default=lambda: os.getenv("API_HOST", "0.0.0.0"), show_default=True, help="API host"
)
@click.option(
    "--port", default=8000, type=click.IntRange(1, 65535), show_default=True, help="API port"
)
@click.option("--reload", is_flag=True, help="Enable auto-reload for local development")
def serve(host, port, reload):
    """Start the FastAPI server."""
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "sentinel.api.app:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        cmd.append("--reload")
    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Starting API server on {host}:{port}")
    raise SystemExit(subprocess.call(cmd))


# Register auth commands
cli.add_command(login)
cli.add_command(logout)
cli.add_command(whoami)

# Register data commands
cli.add_command(projects)
cli.add_command(services)


if __name__ == "__main__":
    cli()
