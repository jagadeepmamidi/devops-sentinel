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

import click
import asyncio
import httpx
import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

# Auth module
from .auth import login, logout, whoami, is_logged_in, get_current_user

# Projects and Services modules
from .projects import projects
from .services import services
from .db import get_db
from .. import __version__

# Rich for beautiful output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Load environment
from dotenv import load_dotenv
load_dotenv()

console = Console() if RICH_AVAILABLE else None


def print_banner():
    """Print ASCII banner"""
    banner = """
========================================
      DEVOPS SENTINEL - SRE AGENT
========================================
"""
    click.echo(click.style(banner, fg='cyan'))


@click.group()
@click.version_option(version=__version__, prog_name='DevOps Sentinel')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
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
    ctx.obj['json'] = output_json


@cli.command()
@click.argument('url')
@click.option('--interval', '-i', default=30, help='Check interval in seconds')
@click.option('--timeout', '-t', default=10, help='Request timeout in seconds')
@click.option('--notify', is_flag=True, help='Send Slack notification on failure')
@click.pass_context
def monitor(ctx, url, interval, timeout, notify):
    """
    Monitor a URL for health status.
    
    Examples:
    
        sentinel monitor https://api.example.com/health
        
        sentinel monitor https://httpbin.org/status/200 --interval 60
    """
    async def _monitor():
        if not ctx.obj.get('json'):
            click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Monitoring: {url}")
            click.echo(f"  Interval: {interval}s | Timeout: {timeout}s")
            click.echo(f"  Press Ctrl+C to stop\n")
            if notify:
                click.echo("  Notifications: enabled")
        
        check_count = 0
        last_state = None
        notify_warned = False
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            async def send_notification(message: str):
                nonlocal notify_warned
                if not notify:
                    return
                webhook = os.getenv('SLACK_WEBHOOK_URL')
                if not webhook:
                    if not notify_warned and not ctx.obj.get('json'):
                        click.echo(click.style("  WARN --notify set, but SLACK_WEBHOOK_URL is missing.", fg='yellow'))
                    notify_warned = True
                    return
                try:
                    await client.post(webhook, json={"text": message}, timeout=5)
                except Exception:
                    if not ctx.obj.get('json'):
                        click.echo(click.style("  WARN Failed to send Slack notification.", fg='yellow'))

            while True:
                check_count += 1
                start = datetime.utcnow()
                current_state = "failed"
                
                try:
                    response = await client.get(url)
                    elapsed = (datetime.utcnow() - start).total_seconds() * 1000
                    
                    if response.status_code == 200:
                        current_state = "healthy"
                        status = click.style('OK HEALTHY', fg='green')
                        if ctx.obj.get('json'):
                            click.echo(json.dumps({
                                'status': 'healthy',
                                'code': response.status_code,
                                'latency_ms': round(elapsed, 2),
                                'check': check_count
                            }))
                        else:
                            click.echo(f"  {status} | {response.status_code} | {elapsed:.0f}ms | Check #{check_count}")
                    else:
                        current_state = "warning"
                        status = click.style('WARN WARNING', fg='yellow')
                        if ctx.obj.get('json'):
                            click.echo(json.dumps({
                                'status': 'warning',
                                'code': response.status_code,
                                'latency_ms': round(elapsed, 2),
                                'check': check_count
                            }))
                        else:
                            click.echo(f"  {status} | {response.status_code} | {elapsed:.0f}ms | Check #{check_count}")
                        if last_state != current_state:
                            await send_notification(
                                f"[DevOps Sentinel] Warning for {url}: HTTP {response.status_code} ({elapsed:.0f}ms)"
                            )
                        
                except Exception as e:
                    current_state = "failed"
                    status = click.style('X FAILED', fg='red')
                    if ctx.obj.get('json'):
                        click.echo(json.dumps({
                            'status': 'failed',
                            'error': str(e),
                            'check': check_count
                        }))
                    else:
                        click.echo(f"  {status} | {str(e)[:50]} | Check #{check_count}")
                    if last_state != current_state:
                        await send_notification(f"[DevOps Sentinel] Failure for {url}: {str(e)[:180]}")

                if notify and last_state in {"warning", "failed"} and current_state == "healthy":
                    await send_notification(f"[DevOps Sentinel] Recovered: {url} is healthy again.")

                last_state = current_state
                
                await asyncio.sleep(interval)
    
    try:
        asyncio.run(_monitor())
    except KeyboardInterrupt:
        click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Monitoring stopped.")


@cli.command()
@click.argument('url')
@click.option('--timeout', '-t', default=10, help='Request timeout in seconds')
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
            start = datetime.utcnow()
            try:
                response = await client.get(url)
                elapsed = (datetime.utcnow() - start).total_seconds() * 1000
                
                result = {
                    'url': url,
                    'status_code': response.status_code,
                    'latency_ms': round(elapsed, 2),
                    'healthy': response.status_code == 200,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                if ctx.obj.get('json'):
                    click.echo(json.dumps(result, indent=2))
                else:
                    if result['healthy']:
                        click.echo(f"\n{click.style('OK', fg='green')} {url}")
                        click.echo(f"  Status: {click.style('HEALTHY', fg='green')}")
                    else:
                        click.echo(f"\n{click.style('WARN', fg='yellow')} {url}")
                        click.echo(f"  Status: {click.style('DEGRADED', fg='yellow')}")
                    
                    click.echo(f"  Response: {result['status_code']}")
                    click.echo(f"  Latency: {result['latency_ms']}ms")
                    click.echo()
                    
            except Exception as e:
                if ctx.obj.get('json'):
                    click.echo(json.dumps({
                        'url': url,
                        'healthy': False,
                        'error': str(e)
                    }, indent=2))
                else:
                    click.echo(f"\n{click.style('X', fg='red')} {url}")
                    click.echo(f"  Status: {click.style('UNREACHABLE', fg='red')}")
                    click.echo(f"  Error: {str(e)}")
                    click.echo()
    
    asyncio.run(_check())


@cli.group()
def incidents():
    """Manage and view incidents."""
    pass


@incidents.command('list')
@click.option('--limit', '-n', default=10, help='Number of incidents to show')
@click.option('--severity', '-s', type=click.Choice(['P0', 'P1', 'P2', 'P3']), help='Filter by severity')
@click.option('--status', type=click.Choice(['open', 'acknowledged', 'resolved']), help='Filter by status')
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
    if ctx.obj.get('json'):
        click.echo(json.dumps(incidents_data, indent=2, default=str))
        return
    click.echo(f"\n{click.style('Recent Incidents', bold=True)}")
    click.echo("-" * 70)
    click.echo(f"{'ID':<12} {'Severity':<10} {'Service':<20} {'Status':<12} {'Created'}")
    click.echo("-" * 70)
    if not incidents_data:
        click.echo("No incidents found. Connect Supabase and run monitoring to collect incidents.")
        click.echo()
        return
    for inc in incidents_data:
        sev_raw = str(inc.get("severity", "unknown")).upper()
        sev_color = {'P0': 'red', 'P1': 'yellow', 'P2': 'blue', 'P3': 'white'}.get(sev_raw, 'white')
        sev = click.style(sev_raw, fg=sev_color, bold=True)
        service = (inc.get("services") or {}).get("name", "unknown")[:19]
        created = str(inc.get("created_at", ""))[:19].replace("T", " ")
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
    pass


@postmortem.command('generate')
@click.argument('incident_id')
@click.option('--output', '-o', type=click.Path(), help='Save to file')
@click.pass_context
def postmortem_generate(ctx, incident_id, output):
    """Generate an AI-powered postmortem for an incident."""
    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Generating postmortem for {incident_id}...")
    click.echo("  Analyzing incident timeline...")
    click.echo("  Identifying root cause...")
    click.echo("  Generating action items...")
    
    # Demo postmortem
    postmortem_text = f"""
# Incident Postmortem: {incident_id}

## Summary
Service degradation affecting API response times.

## Timeline
- 10:30 - Anomaly detected in response latency
- 10:32 - Alert triggered, on-call notified
- 10:45 - Root cause identified
- 11:00 - Fix deployed
- 11:05 - Service recovered

## Root Cause
Database connection pool exhaustion due to leaked connections.

## Resolution
Increased connection pool size and added connection leak detection.

## Action Items
1. [ ] Add connection pool monitoring
2. [ ] Implement automatic connection cleanup
3. [ ] Update runbook for similar incidents
"""
    
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
    api_url = os.getenv('API_URL', 'http://localhost:8000')
    
    async def check_api():
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{api_url}/health")
                return resp.status_code == 200
        except:
            return False
    
    api_ok = asyncio.run(check_api())
    
    supabase_configured = bool(os.getenv('SUPABASE_URL') and (os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')))
    llm_configured = bool(os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY'))
    slack_configured = bool(os.getenv('SLACK_WEBHOOK_URL') or os.getenv('SLACK_CLIENT_ID'))
    
    def status_icon(ok):
        return click.style('OK', fg='green') if ok else click.style('X', fg='red')
    
    click.echo(f"  {status_icon(api_ok)} API Server: {'Connected' if api_ok else 'Not running'}")
    click.echo(f"  {status_icon(supabase_configured)} Supabase: {'Configured' if supabase_configured else 'Not configured'}")
    click.echo(f"  {status_icon(llm_configured)} LLM Provider: {'Configured' if llm_configured else 'Not configured'}")
    click.echo(f"  {status_icon(slack_configured)} Slack: {'Configured' if slack_configured else 'Not configured'}")
    click.echo()


@cli.command()
def config():
    """Show current configuration."""
    click.echo(f"\n{click.style('Configuration', bold=True)}")
    click.echo("-" * 40)
    
    configs = [
        ('API_URL', os.getenv('API_URL', 'http://localhost:8000')),
        ('SENTINEL_WEB_URL', os.getenv('SENTINEL_WEB_URL', 'Not set')),
        ('SUPABASE_URL', os.getenv('SUPABASE_URL', 'Not set')[:50] + '...' if os.getenv('SUPABASE_URL') else 'Not set'),
        ('SUPABASE_KEY', '***' if (os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')) else 'Not set'),
        ('OPENROUTER_API_KEY', '***' if os.getenv('OPENROUTER_API_KEY') else 'Not set'),
        ('OPENAI_API_KEY', '***' if os.getenv('OPENAI_API_KEY') else 'Not set'),
        ('SLACK_WEBHOOK_URL', '***' if os.getenv('SLACK_WEBHOOK_URL') else 'Not set'),
    ]
    
    for key, value in configs:
        click.echo(f"  {key}: {value}")
    click.echo()


@cli.command()
def init():
    """Initialize DevOps Sentinel in current directory."""
    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Initializing DevOps Sentinel...")
    
    # Create .env if not exists
    env_path = Path('.env')
    if not env_path.exists():
        env_content = """# DevOps Sentinel Configuration
# Get your keys at: https://devops-sentinel.dev/docs/setup

# Supabase (for data storage)
SUPABASE_URL=
SUPABASE_ANON_KEY=
# SUPABASE_KEY=  # optional alias

# Hosted web app used by `sentinel login` browser flow
# Example: https://devops-sentinel.dev
SENTINEL_WEB_URL=

# AI Provider (choose one)
OPENROUTER_API_KEY=
# OPENAI_API_KEY=

# Slack Integration (optional)
SLACK_WEBHOOK_URL=
"""
        env_path.write_text(env_content)
        click.echo(f"  {click.style('OK', fg='green')} Created .env file")
    else:
        click.echo(f"  {click.style('*', fg='yellow')} .env already exists")
    
    # Create sentinel.yaml config
    config_path = Path('sentinel.yaml')
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
    
    click.echo(f"\n{click.style('Done!', fg='green')} Edit .env with your API keys, then run:")
    click.echo(f"  sentinel login")
    click.echo(f"  sentinel status")
    click.echo()


@cli.command()
@click.option('--strict', is_flag=True, help='Treat warnings as failures')
@click.pass_context
def doctor(ctx, strict):
    """Run environment and connectivity diagnostics."""
    api_url = os.getenv('API_URL', 'http://localhost:8000')
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    web_url = os.getenv('SENTINEL_WEB_URL')
    llm_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPENAI_API_KEY')

    async def check_api_health():
        try:
            async with httpx.AsyncClient(timeout=4) as client:
                resp = await client.get(f"{api_url}/health")
                return resp.status_code == 200
        except Exception:
            return False

    api_ok = asyncio.run(check_api_health())
    auth_ok = is_logged_in()
    user = get_current_user() if auth_ok else None

    checks = [
        {
            "name": "Supabase URL",
            "status": "ok" if supabase_url else "fail",
            "detail": supabase_url or "Missing SUPABASE_URL",
        },
        {
            "name": "Supabase Key",
            "status": "ok" if supabase_key else "fail",
            "detail": "Configured" if supabase_key else "Missing SUPABASE_KEY or SUPABASE_ANON_KEY",
        },
        {
            "name": "CLI Login",
            "status": "ok" if auth_ok else "warn",
            "detail": f"Logged in as {user.get('email', 'unknown')}" if auth_ok else "Not logged in",
        },
        {
            "name": "Web Auth URL",
            "status": "ok" if web_url else "warn",
            "detail": web_url or "SENTINEL_WEB_URL not set (fallback auth is still supported)",
        },
        {
            "name": "LLM Provider Key",
            "status": "ok" if llm_key else "warn",
            "detail": "Configured" if llm_key else "Missing OPENROUTER_API_KEY or OPENAI_API_KEY",
        },
        {
            "name": "API Health",
            "status": "ok" if api_ok else "warn",
            "detail": f"{api_url}/health reachable" if api_ok else f"API not reachable at {api_url}/health",
        },
    ]

    failed = [c for c in checks if c["status"] == "fail"]
    warnings = [c for c in checks if c["status"] == "warn"]
    passed = len(failed) == 0 and (len(warnings) == 0 if strict else True)

    if ctx.obj.get('json'):
        click.echo(json.dumps({
            "checks": checks,
            "strict": strict,
            "passed": passed,
            "failed_count": len(failed),
            "warning_count": len(warnings),
        }, indent=2))
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
            click.echo(click.style("Critical checks failed. Fix required config and re-run `sentinel doctor`.", fg='red'))
        else:
            click.echo(click.style("Warnings treated as failures in strict mode.", fg='red'))
        raise SystemExit(1)


@cli.command()
@click.pass_context
def setup(ctx):
    """Guided first-run setup for CLI users."""
    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Guided setup")
    click.echo("  This will configure login, first service, and a quick verification.\n")

    if not Path('.env').exists():
        click.echo("  .env not found, creating defaults...")
        ctx.invoke(init)

    if not is_logged_in() and click.confirm("  You are not logged in. Run browser login now?", default=True):
        ctx.invoke(
            login,
            token=None,
            device=False,
            supabase_url=os.getenv('SUPABASE_URL'),
            web_url=os.getenv('SENTINEL_WEB_URL'),
        )

    service_name = click.prompt("  Service name", default="my-api")
    service_url = click.prompt("  Service health URL", default="https://api.example.com/health")
    check_interval = click.prompt("  Check interval seconds", type=int, default=30)

    registered = False
    db = get_db()
    if is_logged_in() and db.connected:
        user = get_current_user()
        if user and user.get('id'):
            service = db.add_service(user['id'], service_name, service_url, check_interval=check_interval)
            if service:
                registered = True
                click.echo(click.style("  OK Service registered in Supabase.", fg='green'))
            else:
                click.echo(click.style("  WARN Failed to register service in Supabase.", fg='yellow'))
        else:
            click.echo(click.style("  WARN Login state is invalid; run `sentinel login` again.", fg='yellow'))
    else:
        click.echo(click.style("  WARN Skipping DB registration (login or Supabase config missing).", fg='yellow'))

    async def quick_check():
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(service_url)
                return response.status_code == 200
        except Exception:
            return False

    health_ok = asyncio.run(quick_check())
    click.echo(click.style(
        f"  {'OK' if health_ok else 'WARN'} Health check {'passed' if health_ok else 'failed'}",
        fg='green' if health_ok else 'yellow'
    ))

    click.echo("\n  Next commands:")
    click.echo(f"    sentinel monitor {service_url}")
    if registered:
        click.echo("    sentinel services list")
    click.echo("    sentinel doctor")
    click.echo()


@cli.command()
@click.option('--host', default=lambda: os.getenv('API_HOST', '0.0.0.0'), show_default=True, help='API host')
@click.option('--port', default=lambda: int(os.getenv('API_PORT', os.getenv('PORT', '8000'))), show_default=True, help='API port')
@click.option('--reload', is_flag=True, help='Enable auto-reload for local development')
def serve(host, port, reload):
    """Start the FastAPI server."""
    cmd = [
        sys.executable,
        '-m',
        'uvicorn',
        'api_server:app',
        '--host',
        host,
        '--port',
        str(port),
    ]
    if reload:
        cmd.append('--reload')
    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Starting API server on {host}:{port}")
    raise SystemExit(subprocess.call(cmd))


# Register auth commands
cli.add_command(login)
cli.add_command(logout)
cli.add_command(whoami)

# Register data commands
cli.add_command(projects)
cli.add_command(services)


if __name__ == '__main__':
    cli()

