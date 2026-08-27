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
from importlib import import_module
from pathlib import Path

import click
import httpx

# Load environment
from dotenv import load_dotenv
from httpx import HTTPError

from .. import __version__
from ..application.incidents import IncidentService


def _monitor_components():
    module = import_module("sentinel.core.monitor_runner")
    return module.MonitorRunner, module.check_url_once


# Auth module
from .auth import (
    SUPPORTED_CONFIG_KEYS,
    enable_local_mode,
    get_current_user,
    get_storage_mode,
    is_logged_in,
    load_user_config_into_env,
    login,
    logout,
    mask_secret,
    remove_user_config,
    set_user_config,
    upsert_project_env,
    user_config_values,
    whoami,
)
from .db import get_db

# Projects and Services modules
from .projects import projects
from .services import services

load_dotenv(dotenv_path=Path.cwd() / ".env")
# Project/process environment wins over user-level persisted settings.
load_user_config_into_env()


def _render(name, *args):
    return getattr(import_module("sentinel.cli.render"), name)(*args)


def console():
    return _render("console")


def _parse_expect(status, body, json_path, json_equals, ssl_min_days):
    from ..core.health_spec import HealthExpect

    return HealthExpect.from_mapping(
        {
            "status": status,
            "body": body,
            "json_path": json_path,
            "json_equals": json_equals,
            "ssl_min_days": ssl_min_days,
        }
    )


def print_incident_card(result: dict) -> None:
    incident_id = result.get("incident_id")
    click.echo()
    click.echo(click.style("  INCIDENT OPENED", fg="red", bold=True))
    click.echo(f"  id:       {incident_id}")
    click.echo(f"  severity: {result.get('incident_severity') or 'unknown'}")
    click.echo(f"  service:  {result.get('service')}")
    click.echo(f"  detail:   {result.get('error') or 'threshold exceeded'}")
    click.echo("  next:")
    click.echo(f"    sentinel incidents show {incident_id}")
    click.echo(f"    sentinel incidents ack {incident_id}")
    click.echo(f"    sentinel postmortem generate {incident_id}")
    click.echo()


def incidents_table(items):
    return _render("incidents_table", items)


def incident_detail(incident, events):
    return _render("incident_detail", incident, events)


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
    """Print branded startup banner for an interactive terminal session."""
    banner = r"""
+--------------------------------------------+
|        WELCOME TO DEVOPS SENTINEL          |
|                                            |
|  Observe services - Investigate incidents  |
|  Coordinate agents - Ship safer            |
+--------------------------------------------+
"""
    click.echo(click.style(banner, fg="cyan"))
    mode = get_storage_mode()
    if mode == "none":
        click.echo("  Not initialized. Next:")
        click.echo("    sentinel init                 # local SQLite, no account")
        click.echo("    sentinel init --mode supabase # your Supabase project")
    elif mode == "local":
        click.echo("  Local SQLite identity is active. Login is not required.")
        click.echo("    sentinel demo")
        click.echo("    sentinel health https://example.com")
        click.echo("    sentinel services add api https://example.com/health")
    else:
        click.echo("  Supabase compatibility mode uses YOUR project, not a Sentinel-hosted DB.")
        if is_logged_in():
            click.echo("    sentinel services list")
            click.echo("    sentinel monitor --all")
        else:
            click.echo("    sentinel login")
            click.echo("    sentinel schema --print")
    click.echo("    sentinel doctor")
    click.echo("    sentinel --help")
    click.echo()


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="DevOps Sentinel")
@click.option("--json", "output_json", is_flag=True, help="Output as JSON")
@click.pass_context
def cli(ctx, output_json):
    """
    DevOps Sentinel - local-first SRE CLI.

    Health checks, incident memory, multi-agent response, and postmortems.
    Default store is SQLite. Optional login talks to YOUR Supabase project.

    Quick start:
      sentinel init
      sentinel demo
      sentinel health https://api.example.com/health
      sentinel services add api https://api.example.com/health
      sentinel monitor api
    """
    ctx.ensure_object(dict)
    ctx.obj["json"] = output_json
    if ctx.invoked_subcommand is None and not output_json:
        print_banner()


@cli.command()
@click.argument("target", required=False)
@click.option("--all", "monitor_all", is_flag=True, help="Monitor all registered active services")
@click.option("--interval", "-i", type=float, default=None, help="Check interval in seconds")
@click.option("--timeout", "-t", type=float, default=10, show_default=True)
@click.option("--notify", is_flag=True, help="Reserved for notification integrations")
@click.option("--failure-threshold", default=3, type=click.IntRange(1, 20), show_default=True)
@click.option("--recovery-threshold", default=2, type=click.IntRange(1, 20), show_default=True)
@click.option("--expect", "expect_status", help="Expected status codes, comma-separated")
@click.option("--body", help="Substring that must appear in the response body")
@click.option("--json-path", help="Dotted JSON path that must exist, e.g. status or data.ok")
@click.option("--json-equals", help="Expected value at --json-path")
@click.option("--ssl-min-days", type=int, help="Fail when TLS remaining days are below this")
@click.option("--once", is_flag=True, help="Run one check per target then exit.")
@click.pass_context
def monitor(
    ctx,
    target,
    monitor_all,
    interval,
    timeout,
    notify,
    failure_threshold,
    recovery_threshold,
    expect_status,
    body,
    json_path,
    json_equals,
    ssl_min_days,
    once,
):
    """Monitor registered service by name, URL, or sentinel.yaml (--all)."""
    del notify
    from ..core.project_file import expect_for_url, load_project_config

    MonitorRunner = _monitor_components()[0]
    output_json = ctx.obj.get("json", False)
    db = get_db()
    user = get_current_user() if is_logged_in() else None
    registered = db.list_services(user["id"]) if user and db.connected else []
    project = load_project_config()
    cli_expect = _parse_expect(expect_status, body, json_path, json_equals, ssl_min_days)
    if monitor_all:
        if target:
            raise click.UsageError("TARGET cannot be used with --all")
        targets = [svc for svc in registered if svc.get("is_active", True)]
        if not targets:
            targets = [
                {
                    "name": item["name"],
                    "url": item["url"],
                    "check_interval": item["interval"],
                    "failure_threshold": item["failure_threshold"],
                    "recovery_threshold": item["recovery_threshold"],
                    "expect": item["expect"],
                }
                for item in project.get("services") or []
            ]
        if not targets:
            raise click.ClickException(
                "No active services. Add one or put them in sentinel.yaml, then `sentinel up`."
            )
    elif not target:
        raise click.UsageError("Provide a service name, URL, or --all")
    else:
        service = None
        if user and db.connected:
            service = db.get_service_by_name(user["id"], target) or db.get_service_by_url(
                user["id"], target
            )
        if service:
            targets = [service]
        elif target.startswith(("http://", "https://")):
            targets = [{"name": target, "url": target, "check_interval": interval or 30}]
        else:
            yaml_match = next(
                (item for item in project.get("services") or [] if item["name"] == target),
                None,
            )
            if not yaml_match:
                raise click.ClickException(f"Registered service not found: {target}")
            targets = [
                {
                    "name": yaml_match["name"],
                    "url": yaml_match["url"],
                    "check_interval": yaml_match["interval"],
                    "expect": yaml_match["expect"],
                }
            ]

    async def run_target(service):
        yaml_expect = service.get("expect") or expect_for_url(
            project, service["url"], service.get("name")
        )
        expect = cli_expect if any([expect_status, body, json_path, json_equals, ssl_min_days]) else yaml_expect
        try:
            runner = MonitorRunner(
                service["url"],
                interval=interval
                if interval is not None
                else float(service.get("check_interval") or 30),
                timeout=timeout,
                db=db if service.get("id") else None,
                user_id=user["id"] if user and service.get("id") else None,
                service=service if service.get("id") else None,
                failure_threshold=int(service.get("failure_threshold") or failure_threshold),
                recovery_threshold=int(service.get("recovery_threshold") or recovery_threshold),
                expect=expect,
            )
        except (TypeError, ValueError) as error:
            raise click.ClickException(f"Invalid monitor configuration: {error}") from error

        def render(result):
            result["service"] = service.get("name", service["url"])
            if output_json:
                click.echo(json.dumps(result, default=str))
                return
            state = (
                "HEALTHY"
                if result["healthy"]
                else ("DEGRADED" if result.get("status_code") else "DOWN")
            )
            click.echo(
                f"{result['service']} {click.style(state, fg='green' if result['healthy'] else 'yellow')} | {result.get('status_code') or result.get('error', '')} | {result.get('latency_ms', 0):.0f}ms | check #{result['check']}"
            )
            if result.get("incident_opened"):
                print_incident_card(result)

        await runner.run_forever(render, once=once)

    async def run_all():
        await asyncio.gather(*(run_target(service) for service in targets))

    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        if not output_json:
            click.echo("Monitoring stopped.")


@cli.command()
@click.argument("url")
@click.option("--timeout", "-t", default=10, show_default=True)
@click.option("--expect", "expect_status", help="Expected status codes, comma-separated")
@click.option("--body", help="Substring that must appear in the response body")
@click.option("--json-path", help="Dotted JSON path that must exist")
@click.option("--json-equals", help="Expected value at --json-path")
@click.option("--ssl-min-days", type=int, help="Fail when TLS remaining days are below this")
@click.pass_context
def health(ctx, url, timeout, expect_status, body, json_path, json_equals, ssl_min_days):
    """Run one health check. Exit 1 when unhealthy or unreachable."""
    check_url_once = _monitor_components()[1]
    expect = _parse_expect(expect_status, body, json_path, json_equals, ssl_min_days)
    result = asyncio.run(check_url_once(url, timeout, expect=expect)).as_dict()
    if ctx.obj.get("json"):
        click.echo(json.dumps(result, indent=2, default=str))
    elif result["healthy"]:
        extra = f" | TLS {result['ssl_days']}d" if result.get("ssl_days") is not None else ""
        click.echo(
            f"{click.style('OK', fg='green')} {url} | HTTP {result['status_code']} | {result['latency_ms']:.0f}ms{extra}"
        )
    elif result.get("status_code"):
        click.echo(
            f"{click.style('WARN', fg='yellow')} {url} | HTTP {result['status_code']} | {result['latency_ms']:.0f}ms | {result.get('error', '')}"
        )
    else:
        click.echo(f"{click.style('X', fg='red')} {url} | UNREACHABLE | {result.get('error', '')}")
    if not result["healthy"]:
        raise click.exceptions.Exit(1)


def _incident_service_or_fail() -> IncidentService:
    user = get_current_user() if is_logged_in() else None
    db = get_db()
    if not user or not db.connected:
        raise click.ClickException(
            "Storage or identity unavailable. Run `sentinel init --mode local`."
        )
    return IncidentService(db, user["id"])


@cli.group()
def incidents():
    """Manage and view incidents."""


@incidents.command("list")
@click.option("--limit", "-n", default=10, show_default=True)
@click.option("--severity", "-s", type=click.Choice(["critical", "high", "medium", "low"]))
@click.option("--status", type=click.Choice(["detecting", "alerting", "investigating", "resolved"]))
@click.pass_context
def incidents_list(ctx, limit, severity, status):
    """List recent incidents."""
    data = _incident_service_or_fail().list(limit, severity, status)
    if ctx.obj.get("json"):
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        console().print(incidents_table(data))


@incidents.command("show")
@click.argument("incident_id")
@click.pass_context
def incidents_show(ctx, incident_id):
    """Show incident details and event timeline."""
    service = _incident_service_or_fail()
    incident = service.get(incident_id)
    if not incident:
        raise click.ClickException("Incident not found.")
    events = service.events(incident_id) or []
    if ctx.obj.get("json"):
        click.echo(json.dumps({"incident": incident, "events": events}, indent=2, default=str))
    else:
        console().print(incident_detail(incident, events))


@incidents.command("ack")
@click.argument("incident_id")
@click.option("--note")
@click.pass_context
def incidents_ack(ctx, incident_id, note):
    """Acknowledge incident and move it to investigating."""
    if not _incident_service_or_fail().acknowledge(incident_id, note):
        raise click.ClickException("Incident not found, or already resolved.")
    result = {"incident_id": incident_id, "status": "investigating"}
    click.echo(
        json.dumps(result)
        if ctx.obj.get("json")
        else f"Acknowledged {incident_id}; status: investigating"
    )


@incidents.command("resolve")
@click.argument("incident_id")
@click.option("--action-plan")
@click.pass_context
def incidents_resolve(ctx, incident_id, action_plan):
    """Resolve incident and append resolution event."""
    if not _incident_service_or_fail().resolve(incident_id, action_plan):
        raise click.ClickException("Incident not found, or resolution failed.")
    result = {"incident_id": incident_id, "status": "resolved"}
    click.echo(json.dumps(result) if ctx.obj.get("json") else f"Resolved {incident_id}")


@incidents.command("export")
@click.argument("incident_id")
@click.option(
    "--format", "export_format", type=click.Choice(["md", "json"]), default="md", show_default=True
)
@click.option("--output", "-o", type=click.Path())
def incidents_export(incident_id, export_format, output):
    """Export incident detail and timeline."""
    service = _incident_service_or_fail()
    incident = service.get(incident_id)
    if not incident:
        raise click.ClickException("Incident not found.")
    events = service.events(incident_id) or []
    if export_format == "json":
        content = json.dumps({"incident": incident, "events": events}, indent=2, default=str)
    else:
        content = "\n".join(
            [
                f"# Incident {incident_id}",
                f"- Status: {incident.get('status')}",
                f"- Severity: {incident.get('severity')}",
                f"- Error: {incident.get('error_message') or 'n/a'}",
                "",
                "## Timeline",
                *[
                    f"- {event.get('created_at', '')}: {event.get('description', '')}"
                    for event in events
                ],
            ]
        )
    if output:
        Path(output).write_text(content, encoding="utf-8")
        click.echo(f"Exported incident to {output}")
    else:
        click.echo(content)


@cli.group()
def postmortem():
    """Generate and view postmortems."""


@postmortem.command("generate")
@click.argument("incident_id")
@click.option("--output", "-o", type=click.Path())
@click.pass_context
def postmortem_generate(ctx, incident_id, output):
    """Generate and save postmortem for incident."""
    from ..core.postmortem_generator import PostmortemGenerator

    service = _incident_service_or_fail()
    incident = service.get(incident_id)
    if not incident:
        raise click.ClickException("Incident not found.")
    generated = asyncio.run(
        PostmortemGenerator().generate(
            incident, service.events(incident_id) or [], incident.get("action_plan")
        )
    )
    markdown = generated["markdown"]
    if not service.db.save_postmortem(incident_id, markdown):
        raise click.ClickException("Failed to save postmortem.")
    if output:
        Path(output).write_text(markdown, encoding="utf-8")
    if ctx.obj.get("json"):
        click.echo(
            json.dumps({"incident_id": incident_id, **generated, "output": output}, default=str)
        )
    elif output:
        click.echo(f"Postmortem saved to {output}")
    else:
        click.echo(markdown)


@postmortem.command("list")
@click.option("--limit", "-n", default=50, show_default=True)
@click.pass_context
def postmortem_list(ctx, limit):
    """List generated postmortems."""
    service = _incident_service_or_fail()
    data = service.db.list_postmortems(service.user_id, limit)
    if ctx.obj.get("json"):
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        console().print(incidents_table(data))


@postmortem.command("view")
@click.argument("incident_id")
@click.pass_context
def postmortem_view(ctx, incident_id):
    """View saved postmortem."""
    incident = _incident_service_or_fail().get(incident_id)
    if not incident or not incident.get("postmortem"):
        raise click.ClickException("Postmortem not found.")
    if ctx.obj.get("json"):
        click.echo(json.dumps({"incident_id": incident_id, "postmortem": incident["postmortem"]}))
    else:
        click.echo(incident["postmortem"])


@cli.command()
@click.option("--interval", type=float, default=5, show_default=True)
@click.pass_context
def dashboard(ctx, interval):
    """Live status dashboard for registered services."""
    if ctx.obj.get("json"):
        raise click.UsageError("dashboard does not support --json")
    user = get_current_user() if is_logged_in() else None
    db = get_db()
    if not user or not db.connected:
        raise click.ClickException(
            "Storage or identity unavailable. Run `sentinel init --mode local`."
        )
    from rich.live import Live
    from rich.table import Table

    async def run_dashboard():
        with Live("Loading...", refresh_per_second=4) as live:
            while True:
                data = db.list_services(user["id"])

                async def check(service):
                    result = (await _monitor_components()[1](service["url"])).as_dict()
                    result["name"] = service.get("name", service["url"])
                    return result

                results = await asyncio.gather(*(check(service) for service in data))
                table = Table(title="Sentinel Dashboard")
                table.add_column("Service", style="bold")
                table.add_column("URL")
                table.add_column("Status")
                table.add_column("Latency")
                for result in results:
                    healthy = result["healthy"]
                    style = (
                        "green" if healthy else ("yellow" if result.get("status_code") else "red")
                    )
                    state = "healthy" if healthy else "down"
                    table.add_row(
                        result["name"],
                        result["url"],
                        f"[{style}]{state}[/{style}]",
                        f"{result.get('latency_ms') or 0:.0f}ms",
                    )
                live.update(table)
                await asyncio.sleep(interval)

    try:
        asyncio.run(run_dashboard())
    except KeyboardInterrupt:
        click.echo("Dashboard stopped.")


@cli.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish", "powershell"]))
def completion(shell):
    """Print shell completion script."""
    from click.shell_completion import get_completion_class

    completion_class = get_completion_class(shell)
    if completion_class is None:
        raise click.ClickException(f"Unsupported shell: {shell}")
    click.echo(completion_class(cli, {}, "sentinel", "_SENTINEL_COMPLETE").source())


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
                return resp.status_code in range(200, 400)
        except HTTPError:
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

    if storage_mode == "local":
        click.echo(
            f"  {status_icon(True)} API Server: optional (`sentinel serve` for the operator UI)"
        )
    else:
        click.echo(
            f"  {status_icon(api_ok)} API Server: {'Connected' if api_ok else 'Not running'}"
        )
    storage_label = "SQLite (local)" if storage_mode == "local" else "Supabase (your project)"
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


@cli.group(invoke_without_command=True)
@click.pass_context
def config(ctx):
    """Show or manage configuration and provider API keys."""
    if ctx.invoked_subcommand is not None:
        return

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
        ("SUPABASE_KEY", mask_secret(os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY"))),
        ("OPENROUTER_API_KEY", mask_secret(os.getenv("OPENROUTER_API_KEY"))),
        ("OPENAI_API_KEY", mask_secret(os.getenv("OPENAI_API_KEY"))),
        ("ANTHROPIC_API_KEY", mask_secret(os.getenv("ANTHROPIC_API_KEY"))),
        ("SLACK_WEBHOOK_URL", mask_secret(os.getenv("SLACK_WEBHOOK_URL"))),
    ]
    for key, value in configs:
        click.echo(f"  {key}: {value}")
    click.echo("\n  User config: ~/.sentinel/config.json")
    click.echo("  Set a key: sentinel config set openrouter_api_key")
    click.echo()


@config.command("set")
@click.argument("key", type=click.Choice(list(SUPPORTED_CONFIG_KEYS), case_sensitive=False))
@click.option("--value", help="Value for non-interactive use; avoid shell history for secrets.")
def config_set(key, value):
    """Save an API key or integration setting in the user config."""
    value = value or click.prompt(f"{key} value", hide_input=True)
    if not value.strip():
        raise click.ClickException("Value cannot be empty.")
    env_name = set_user_config(key, value.strip())
    click.echo(f"Saved {env_name} in the user config.")


@config.command("list")
def config_list():
    """List saved settings without exposing secret values."""
    values = user_config_values()
    if not values:
        click.echo("No user settings saved.\n  sentinel config set openrouter_api_key")
        return
    for key, value in sorted(values.items()):
        click.echo(f"{key}: {mask_secret(value)}")


@config.command("remove")
@click.argument("key", type=click.Choice(list(SUPPORTED_CONFIG_KEYS), case_sensitive=False))
def config_remove(key):
    """Remove a saved API key or integration setting."""
    env_name = remove_user_config(key)
    os.environ.pop(env_name, None)
    click.echo(f"Removed {env_name} from the user config.")


@cli.command()
@click.option(
    "--mode",
    type=click.Choice(["local", "supabase"]),
    default="local",
    show_default=True,
    help="Storage mode for this project",
)
@click.option("--url", "supabase_url", help="Your Supabase project URL")
@click.option("--anon-key", "anon_key", help="Your Supabase anon key")
def init(mode, supabase_url, anon_key):
    """Initialize local SQLite or connect YOUR Supabase project."""
    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Initializing DevOps Sentinel...")

    env_path = Path(".env")
    created = not env_path.exists()
    if mode == "local":
        enable_local_mode(env_path)
    else:
        supabase_url = (supabase_url or os.getenv("SUPABASE_URL") or "").strip()
        anon_key = (
            anon_key or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY") or ""
        ).strip()
        if not supabase_url:
            if sys.stdin.isatty():
                supabase_url = click.prompt("  Your Supabase URL", default="").strip()
            else:
                raise click.UsageError(
                    "Provide --url https://YOUR-PROJECT.supabase.co for supabase mode."
                )
        if not anon_key:
            if sys.stdin.isatty():
                anon_key = click.prompt(
                    "  Your Supabase anon key", hide_input=True, default=""
                ).strip()
            else:
                raise click.UsageError("Provide --anon-key for supabase mode.")
        if not supabase_url or not anon_key:
            raise click.UsageError(
                "Supabase mode needs both --url and --anon-key from YOUR project."
            )
        upsert_project_env(
            {
                "SENTINEL_MODE": "supabase",
                "SUPABASE_URL": supabase_url,
                "SUPABASE_ANON_KEY": anon_key,
            },
            env_path,
        )
        os.environ["SENTINEL_MODE"] = "supabase"
        os.environ["SUPABASE_URL"] = supabase_url
        os.environ["SUPABASE_ANON_KEY"] = anon_key
        set_user_config("supabase_url", supabase_url)
        set_user_config("supabase_anon_key", anon_key)

    if created:
        click.echo(f"  {click.style('OK', fg='green')} Created .env file")
    else:
        click.echo(f"  {click.style('*', fg='yellow')} Updated existing .env")

    from ..core.project_file import find_project_file, write_sample_project_file

    if find_project_file() is None:
        yaml_path = write_sample_project_file()
        click.echo(f"  {click.style('OK', fg='green')} Wrote {yaml_path.name}")
    else:
        click.echo(f"  {click.style('*', fg='yellow')} Existing sentinel.yaml left unchanged")

    if mode == "local":
        click.echo(
            f"\n{click.style('Done!', fg='green')} Local mode ready. No Supabase or login required."
        )
        click.echo("  sentinel demo")
        click.echo("  sentinel health https://example.com")
        click.echo("  sentinel up --once")
        click.echo("  sentinel services add api https://example.com/health")
    else:
        from ..setup.schema_files import schema_sql_path

        click.echo(
            f"\n{click.style('Done!', fg='green')} Using YOUR Supabase project. Sentinel does not store this data."
        )
        click.echo(f"  Schema SQL: {schema_sql_path()}")
        click.echo("  1. Paste that SQL into your Supabase SQL editor (or: sentinel schema --print)")
        click.echo("  2. sentinel login")
        click.echo("  3. sentinel doctor")
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


@cli.command("up")
@click.option("--interval", "-i", type=float, default=None, help="Override poll interval from sentinel.yaml.")
@click.option("--once", is_flag=True, help="Run one pass then exit.")
@click.option("--timeout", "-t", type=float, default=10, show_default=True)
@click.pass_context
def up(ctx, interval, once, timeout):
    """Register services from sentinel.yaml and start the monitor."""
    from ..core.project_file import load_project_config
    from .db import reset_db

    project = load_project_config()
    services_cfg = project.get("services") or []
    if not project.get("path") or not services_cfg:
        raise click.ClickException(
            "No sentinel.yaml with services found. Run `sentinel init` or copy examples/sentinel.yaml."
        )
    if get_storage_mode() == "none":
        ctx.invoke(init, mode="local", supabase_url=None, anon_key=None)
        reset_db()
    user = get_current_user() if is_logged_in() else None
    db = get_db()
    if not user or not db.connected:
        raise click.ClickException("Storage or identity unavailable. Run `sentinel init --mode local`.")
    existing = {(row.get("url") or "").rstrip("/") for row in db.list_services(user["id"])}
    for item in services_cfg:
        url = str(item["url"]).rstrip("/")
        name = item["name"]
        if url and url not in existing:
            added = db.add_service(user["id"], name, url, check_interval=int(item["interval"]))
            if added:
                click.echo(f"Registered {name} ({url})")
            existing.add(url)
    poll = interval if interval is not None else float(services_cfg[0].get("interval") or 30)
    ctx.invoke(
        monitor,
        target=None,
        monitor_all=True,
        interval=poll,
        timeout=timeout,
        notify=False,
        failure_threshold=3,
        recovery_threshold=2,
        expect_status=None,
        body=None,
        json_path=None,
        json_equals=None,
        ssl_min_days=None,
        once=once,
    )


@cli.command("demo")
@click.option("--keep-going", is_flag=True, help="Keep polling the failing endpoint until Ctrl+C.")
@click.pass_context
def demo(ctx, keep_going):
    """Thirty-second loop: local store, fake 503, incident card. No API key."""
    from ..core.demo_server import DemoServer
    from .db import reset_db

    MonitorRunner, check_once = _monitor_components()
    click.echo("DevOps Sentinel demo — local SQLite, no cloud, no API key.")
    click.echo("Starting an in-process HTTP server with /ok (200) and /fail (503)…")
    with DemoServer() as server:
        ctx.invoke(init, mode="local", supabase_url=None, anon_key=None)
        reset_db()
        db = get_db()
        user = get_current_user()
        if not user or not db.connected:
            raise click.ClickException("Local identity failed. Re-run `sentinel init --mode local`.")
        service = db.add_service(user["id"], "demo-fail", server.fail_url, check_interval=1)
        if not service:
            raise click.ClickException("Could not register demo service.")
        click.echo("")
        click.echo(f"Polling {server.fail_url} once (expect 503 → incident)…")
        runner = MonitorRunner(
            server.fail_url,
            interval=1,
            timeout=5,
            db=db,
            user_id=user["id"],
            service=service,
            failure_threshold=1,
            recovery_threshold=1,
        )

        def render(result):
            result["service"] = service.get("name", "demo-fail")
            state = "DOWN" if not result.get("healthy") else "HEALTHY"
            click.echo(
                f"{result['service']} {click.style(state, fg='green' if result.get('healthy') else 'yellow')} | {result.get('status_code') or result.get('error', '')} | {result.get('latency_ms', 0):.0f}ms"
            )
            if result.get("incident_opened"):
                print_incident_card(result)

        asyncio.run(runner.run_forever(render, once=True))
        click.echo("Healthy contrast check:")
        ok_result = asyncio.run(check_once(server.ok_url, 5)).as_dict()
        click.echo(
            f"{click.style('OK', fg='green')} {server.ok_url} | HTTP {ok_result.get('status_code')} | {ok_result.get('latency_ms') or 0:.0f}ms"
        )
        if keep_going:
            click.echo("keep-going: Ctrl+C to stop.")
            try:
                asyncio.run(runner.run_forever(render, once=False))
            except KeyboardInterrupt:
                click.echo("Demo stopped.")
    click.echo("")
    click.echo("Done. `sentinel incidents list` shows the demo incident.")
    click.echo("       `sentinel postmortem generate <id>` drafts from it.")


@cli.group("supabase")
def supabase_group():
    """Bring-your-own Supabase helpers."""


@supabase_group.command("doctor")
@click.option("--url", "project_url", default=None, help="Override saved project URL.")
@click.option("--anon-key", "anon_key", default=None, help="Override saved anon key.")
@click.pass_context
def supabase_doctor_cmd(ctx, project_url, anon_key):
    """Check URL, anon key, REST, tables, and RLS on *your* project."""
    from ..core.supabase_doctor import run_supabase_doctor

    report = run_supabase_doctor(project_url, anon_key)
    if ctx.obj.get("json"):
        click.echo(json.dumps(report, indent=2))
        raise SystemExit(0 if report.get("passed") else 1)

    icons = {"ok": "OK", "warn": "WARN", "fail": "FAIL"}
    colors = {"ok": "green", "warn": "yellow", "fail": "red"}
    click.echo(f"\n{click.style('Supabase doctor', bold=True)} (your project, not hosted by Sentinel)")
    click.echo("-" * 40)
    for item in report.get("checks") or []:
        marker = click.style(icons.get(item["status"], item["status"]), fg=colors.get(item["status"], "white"))
        click.echo(f"  {marker}  {item['name']}: {item['detail']}")
    click.echo()
    if not report.get("passed"):
        click.echo("Run `sentinel schema --print` and apply the SQL in your project.")
        raise SystemExit(1)


@cli.command("mcp")
def mcp_server():
    """Start the MCP server for Cursor / Claude Desktop."""
    try:
        from sentinel.mcp.server import main
    except ModuleNotFoundError as error:
        if error.name == "mcp":
            raise click.ClickException(
                'MCP dependency missing. Install with `pip install "devops-sentinel-next[mcp]"`.'
            ) from error
        raise

    main()


@cli.command()
@click.pass_context
def setup(ctx):
    """Guided first-run setup for CLI users."""
    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Guided setup")
    click.echo("  This will configure optional keys, first service, and a quick verification.\n")

    if not Path(".env").exists():
        click.echo("  .env not found, creating defaults...")
        ctx.invoke(init)

    if (
        get_storage_mode() == "supabase"
        and not is_logged_in()
        and click.confirm("  You are not logged in. Run browser login now?", default=True)
    ):
        ctx.invoke(
            login,
            token=None,
            device=False,
            supabase_url=os.getenv("SUPABASE_URL"),
            web_url=os.getenv("SENTINEL_WEB_URL"),
            force_local=False,
        )

    service_name = click.prompt("  Service name", default="my-api")
    service_url = click.prompt("  Service health URL", default="https://api.example.com/health")
    check_interval = click.prompt("  Check interval seconds", type=int, default=30)

    registered = False
    db = get_db()
    if (get_storage_mode() == "local" or is_logged_in()) and db.connected:
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
                    "  WARN Identity is invalid; run `sentinel login` again in Supabase mode.",
                    fg="yellow",
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
                return response.status_code in range(200, 400)
        except HTTPError:
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
cli.add_command(monitor, name="watch")


@cli.command("schema")
@click.option("--print", "print_sql", is_flag=True, help="Print the SQL to stdout")
@click.option("--output", "-o", type=click.Path(), help="Write schema SQL to a file")
def schema_cmd(print_sql, output):
    """Show the SQL to apply in YOUR Supabase SQL editor."""
    from ..setup.schema_files import schema_sql_path

    path = schema_sql_path()
    if not path.exists():
        raise click.ClickException("Schema file is missing from this install.")
    if print_sql or output:
        sql = path.read_text(encoding="utf-8")
        if output:
            Path(output).write_text(sql, encoding="utf-8")
            click.echo(f"Wrote schema to {output}")
            return
        click.echo(sql)
        return
    click.echo("\n[SENTINEL] Bring-your-own Supabase schema")
    click.echo(f"  File: {path}")
    click.echo("  1. Open your project SQL editor: https://supabase.com/dashboard")
    click.echo("  2. Run `sentinel schema --print` and paste the SQL")
    click.echo("  3. sentinel init --mode supabase --url <project-url>")
    click.echo("  Sentinel does not host this database.")


@cli.command()
def agents():
    """Show the multi-agent incident response workflow."""
    click.echo(
        """
Sentinel agent loop (non-destructive by default)
------------------------------------------------
  Watcher           Detect failure, latency, SSL, or anomaly
  First Responder   Open incident context and notify responders
  Investigator      Correlate checks, events, deployments, dependencies
  Strategist        Action plan, runbook suggestion, postmortem
  Human approval    Required before remediation with side effects

Start:
  sentinel monitor https://api.example.com/health --failure-threshold 3
"""
    )


# Register data commands
cli.add_command(projects)
cli.add_command(services)


if __name__ == "__main__":
    cli()
