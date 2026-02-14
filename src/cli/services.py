"""
DevOps Sentinel CLI - Services Command
=======================================

Manage monitored services from the terminal.
"""

import asyncio
import json
from datetime import datetime

import click
import httpx

from .auth import get_current_user, is_logged_in
from .db import get_db


def _require_user():
    """Return current user when login state is valid."""
    if not is_logged_in():
        click.echo(click.style('Error: Not logged in. Run `sentinel login` first.', fg='red'))
        return None

    user = get_current_user()
    if not user or not user.get('id'):
        click.echo(click.style('Error: Login state is invalid. Run `sentinel login` again.', fg='red'))
        return None
    return user


@click.group()
def services():
    """Manage monitored services."""
    pass


@services.command('list')
@click.option('--project', '-p', help='Filter by project ID')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def services_list(project, output_json):
    """List all monitored services."""
    user = _require_user()
    if not user:
        return

    db = get_db()
    if not db.connected:
        click.echo(click.style('Error: Database not configured.', fg='red'))
        return

    services_data = db.list_services(user['id'], project)

    if output_json:
        click.echo(json.dumps(services_data, indent=2, default=str))
        return

    if not services_data:
        click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} No services found.")
        click.echo("  Add one with: sentinel services add <name> <url>")
        return

    click.echo(f"\n{click.style('Monitored Services', bold=True)}")
    click.echo("-" * 70)
    click.echo(f"{'Name':<20} {'URL':<30} {'Status':<10} {'Latency'}")
    click.echo("-" * 70)

    for svc in services_data:
        name = svc.get('name', 'Unnamed')[:19]
        url = svc.get('url', '')[:29]
        status = svc.get('last_status', 'unknown')
        latency = f"{svc.get('avg_response_time', 0)}ms"

        status_color = {'healthy': 'green', 'degraded': 'yellow', 'down': 'red'}.get(status, 'white')
        status_styled = click.style(status, fg=status_color)

        click.echo(f"{name:<20} {url:<30} {status_styled:<19} {latency}")

    click.echo()


@services.command('add')
@click.argument('name')
@click.argument('url')
@click.option('--project', '-p', help='Project ID to add service to')
@click.option('--interval', '-i', default=30, help='Check interval in seconds')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def services_add(name, url, project, interval, output_json):
    """Add a new service to monitor."""
    user = _require_user()
    if not user:
        return

    db = get_db()
    if not db.connected:
        click.echo(click.style('Error: Database not configured.', fg='red'))
        return

    service = db.add_service(user['id'], name, url, project, interval)

    if output_json:
        click.echo(json.dumps(service, indent=2, default=str))
        return

    if service:
        click.echo(f"\n{click.style('OK', fg='green')} Added service: {name}")
        click.echo(f"  URL: {url}")
        click.echo(f"  Check interval: {interval}s")
        click.echo(f"\n  Start monitoring with: sentinel monitor {url}")
    else:
        click.echo(click.style('Error: Failed to add service.', fg='red'))


@services.command('delete')
@click.argument('service_id')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation')
def services_delete(service_id, force):
    """Delete a monitored service."""
    user = _require_user()
    if not user:
        return

    if not force and not click.confirm(f'Delete service {service_id[:8]}...?'):
        return

    db = get_db()
    if db.delete_service(service_id):
        click.echo(f"{click.style('OK', fg='green')} Service deleted.")
    else:
        click.echo(click.style('Error: Failed to delete service.', fg='red'))


@services.command('check')
@click.argument('service_id')
def services_check(service_id):
    """Run a health check on a specific service."""
    user = _require_user()
    if not user:
        return

    db = get_db()
    if not db.connected:
        click.echo(click.style('Error: Database not configured.', fg='red'))
        return

    services_data = db.list_services(user['id'])
    service = next((s for s in services_data if s['id'] == service_id), None)

    if not service:
        click.echo(click.style('Error: Service not found.', fg='red'))
        return

    url = service.get('url')
    click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} Checking {service.get('name')}...")

    async def _check():
        async with httpx.AsyncClient(timeout=10) as client:
            start = datetime.utcnow()
            try:
                response = await client.get(url)
                elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
                is_healthy = response.status_code == 200

                db.log_health_check(service_id, response.status_code, elapsed, is_healthy)
                db.update_service_status(service_id, 'healthy' if is_healthy else 'degraded', elapsed)

                status = click.style('OK HEALTHY', fg='green') if is_healthy else click.style('WARN DEGRADED', fg='yellow')
                click.echo(f"  {status} | {response.status_code} | {elapsed}ms")

            except Exception as e:
                db.log_health_check(service_id, 0, 0, False, str(e))
                db.update_service_status(service_id, 'down', 0)
                click.echo(f"  {click.style('X DOWN', fg='red')} | {str(e)[:50]}")

    asyncio.run(_check())
