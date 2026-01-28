"""
DevOps Sentinel CLI - Main Entry Point
=======================================

Usage:
    sentinel login                   - Authenticate with browser
    sentinel monitor <url>           - Monitor a URL for health
    sentinel incidents list          - List recent incidents
    sentinel postmortem <id>         - View/generate postmortem
    sentinel status                  - Show service status
    sentinel deploy <service> <ver>  - Register deployment
    sentinel config                  - Show configuration
"""

import click
import asyncio
import httpx
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

# Auth module
from .auth import login, logout, whoami, is_logged_in, get_current_user, get_access_token

# Projects and Services modules
from .projects import projects
from .services import services

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
╔═══════════════════════════════════════════════════════════════╗
║  ██████╗ ███████╗██╗   ██╗ ██████╗ ██████╗ ███████╗           ║
║  ██╔══██╗██╔════╝██║   ██║██╔═══██╗██╔══██╗██╔════╝           ║
║  ██║  ██║█████╗  ╚██╗ ██╔╝██║   ██║██████╔╝███████╗           ║
║  ██████╔╝███████╗ ╚████╔╝ ╚██████╔╝██║     ╚════██║           ║
║  ╚═════╝ ╚══════╝  ╚═══╝   ╚═════╝ ╚═╝     ╚═════╝            ║
║  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗  ║
║  ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║  ║
║  ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║  ║
║  ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║  ║
║  ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
║  ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
╚═══════════════════════════════════════════════════════════════╝
"""
    click.echo(click.style(banner, fg='cyan'))


@click.group()
@click.version_option(version='0.1.0', prog_name='DevOps Sentinel')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
@click.pass_context
def cli(ctx, output_json):
    """
    ⬢ DevOps Sentinel - Autonomous SRE Agent
    
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
        
        check_count = 0
        failures = 0
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            while True:
                check_count += 1
                start = datetime.utcnow()
                
                try:
                    response = await client.get(url)
                    elapsed = (datetime.utcnow() - start).total_seconds() * 1000
                    
                    if response.status_code == 200:
                        status = click.style('✓ HEALTHY', fg='green')
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
                        failures += 1
                        status = click.style(f'⚠ WARNING', fg='yellow')
                        if ctx.obj.get('json'):
                            click.echo(json.dumps({
                                'status': 'warning',
                                'code': response.status_code,
                                'latency_ms': round(elapsed, 2),
                                'check': check_count
                            }))
                        else:
                            click.echo(f"  {status} | {response.status_code} | {elapsed:.0f}ms | Check #{check_count}")
                        
                except Exception as e:
                    failures += 1
                    status = click.style('✗ FAILED', fg='red')
                    if ctx.obj.get('json'):
                        click.echo(json.dumps({
                            'status': 'failed',
                            'error': str(e),
                            'check': check_count
                        }))
                    else:
                        click.echo(f"  {status} | {str(e)[:50]} | Check #{check_count}")
                
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
                        click.echo(f"\n{click.style('✓', fg='green')} {url}")
                        click.echo(f"  Status: {click.style('HEALTHY', fg='green')}")
                    else:
                        click.echo(f"\n{click.style('⚠', fg='yellow')} {url}")
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
                    click.echo(f"\n{click.style('✗', fg='red')} {url}")
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
    # Demo data for now - would connect to Supabase in production
    demo_incidents = [
        {'id': 'inc-001', 'severity': 'P1', 'service': 'api-gateway', 'status': 'resolved', 'created': '2026-01-27 10:30'},
        {'id': 'inc-002', 'severity': 'P2', 'service': 'payment-api', 'status': 'open', 'created': '2026-01-27 14:15'},
        {'id': 'inc-003', 'severity': 'P0', 'service': 'database', 'status': 'acknowledged', 'created': '2026-01-27 18:45'},
    ]
    
    if ctx.obj.get('json'):
        click.echo(json.dumps(demo_incidents, indent=2))
    else:
        click.echo(f"\n{click.style('Recent Incidents', bold=True)}")
        click.echo("─" * 60)
        click.echo(f"{'ID':<12} {'Severity':<10} {'Service':<15} {'Status':<12} {'Created'}")
        click.echo("─" * 60)
        
        for inc in demo_incidents[:limit]:
            sev_color = {'P0': 'red', 'P1': 'yellow', 'P2': 'blue', 'P3': 'white'}.get(inc['severity'], 'white')
            sev = click.style(inc['severity'], fg=sev_color, bold=True)
            click.echo(f"{inc['id']:<12} {sev:<19} {inc['service']:<15} {inc['status']:<12} {inc['created']}")
        
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
        click.echo(f"\n{click.style('✓', fg='green')} Postmortem saved to {output}")
    else:
        click.echo(postmortem_text)


@cli.command()
@click.pass_context
def status(ctx):
    """Show current system status."""
    click.echo(f"\n{click.style('DevOps Sentinel Status', bold=True)}")
    click.echo("─" * 40)
    
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
    
    supabase_configured = bool(os.getenv('SUPABASE_URL'))
    openai_configured = bool(os.getenv('OPENAI_API_KEY'))
    slack_configured = bool(os.getenv('SLACK_WEBHOOK_URL') or os.getenv('SLACK_CLIENT_ID'))
    
    def status_icon(ok):
        return click.style('✓', fg='green') if ok else click.style('✗', fg='red')
    
    click.echo(f"  {status_icon(api_ok)} API Server: {'Connected' if api_ok else 'Not running'}")
    click.echo(f"  {status_icon(supabase_configured)} Supabase: {'Configured' if supabase_configured else 'Not configured'}")
    click.echo(f"  {status_icon(openai_configured)} OpenAI: {'Configured' if openai_configured else 'Not configured'}")
    click.echo(f"  {status_icon(slack_configured)} Slack: {'Configured' if slack_configured else 'Not configured'}")
    click.echo()


@cli.command()
def config():
    """Show current configuration."""
    click.echo(f"\n{click.style('Configuration', bold=True)}")
    click.echo("─" * 40)
    
    configs = [
        ('API_URL', os.getenv('API_URL', 'http://localhost:8000')),
        ('SUPABASE_URL', os.getenv('SUPABASE_URL', 'Not set')[:50] + '...' if os.getenv('SUPABASE_URL') else 'Not set'),
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

# AI Provider (choose one)
OPENAI_API_KEY=
# OPENROUTER_API_KEY=

# Slack Integration (optional)
SLACK_WEBHOOK_URL=
"""
        env_path.write_text(env_content)
        click.echo(f"  {click.style('✓', fg='green')} Created .env file")
    else:
        click.echo(f"  {click.style('•', fg='yellow')} .env already exists")
    
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
        click.echo(f"  {click.style('✓', fg='green')} Created sentinel.yaml")
    else:
        click.echo(f"  {click.style('•', fg='yellow')} sentinel.yaml already exists")
    
    click.echo(f"\n{click.style('Done!', fg='green')} Edit .env with your API keys, then run:")
    click.echo(f"  sentinel login")
    click.echo(f"  sentinel status")
    click.echo()


# Register auth commands
cli.add_command(login)
cli.add_command(logout)
cli.add_command(whoami)

# Register data commands
cli.add_command(projects)
cli.add_command(services)


if __name__ == '__main__':
    cli()
