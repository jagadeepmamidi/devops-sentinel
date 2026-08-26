"""Manage monitored services from terminal."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone

import click
import httpx
from rich.console import Console
from rich.table import Table

from .auth import get_current_user, is_logged_in
from .db import get_db


def _json(ctx):
    return bool(ctx.find_root().obj.get("json"))


def _require_user():
    if not is_logged_in():
        raise click.ClickException(
            "No active identity. Run `sentinel init --mode local` or `sentinel login`."
        )
    user = get_current_user()
    if not user or not user.get("id"):
        raise click.ClickException("Identity state invalid. Run `sentinel login` again.")
    return user


def _db_or_fail():
    db = get_db()
    if not db.connected:
        raise click.ClickException("Database not configured.")
    return db


@click.group()
def services():
    """Manage monitored services."""


@services.command("list")
@click.option("--project", "-p", help="Filter by project ID")
@click.pass_context
def services_list(ctx, project):
    """List all monitored services."""
    data = _db_or_fail().list_services(_require_user()["id"], project)
    if _json(ctx):
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        table = Table(title="Monitored Services")
        table.add_column("Name", style="bold")
        table.add_column("URL")
        table.add_column("Status")
        table.add_column("Latency")
        for item in data:
            table.add_row(
                str(item.get("name", "Unnamed")),
                str(item.get("url", "")),
                str(item.get("last_status", "unknown")),
                f"{item.get('last_response_time_ms') or 0}ms",
            )
        Console().print(table)


@services.command("add")
@click.argument("name")
@click.argument("url")
@click.option("--project", "-p")
@click.option("--interval", "-i", default=30, type=click.IntRange(1, 3600), show_default=True)
@click.pass_context
def services_add(ctx, name, url, project, interval):
    """Add monitored service."""
    service = _db_or_fail().add_service(_require_user()["id"], name, url, project, interval)
    if not service:
        raise click.ClickException("Failed to add service.")
    if _json(ctx):
        click.echo(json.dumps(service, indent=2, default=str))
    else:
        click.echo(f"Added service: {name} ({url}), interval {interval}s")


@services.command("update")
@click.argument("service_id")
@click.option("--name")
@click.option("--url")
@click.option("--interval", type=click.IntRange(1, 3600))
@click.option("--enable/--disable", default=None)
@click.pass_context
def services_update(ctx, service_id, name, url, interval, enable):
    """Update registered service fields."""
    user = _require_user()
    db = _db_or_fail()
    service = db.get_service(service_id)
    if not service or service.get("user_id") != user["id"]:
        raise click.ClickException("Service not found.")
    updates = {
        k: v
        for k, v in {
            "name": name,
            "url": url,
            "check_interval": interval,
            "is_active": enable,
        }.items()
        if v is not None
    }
    if not updates or not db.update_service(service_id, updates):
        raise click.ClickException("No valid updates supplied.")
    updated = {**service, **updates}
    click.echo(json.dumps(updated, default=str) if _json(ctx) else f"Updated service: {service_id}")


@services.command("delete")
@click.argument("service_id")
@click.option("--force", "-f", is_flag=True)
def services_delete(service_id, force):
    """Delete monitored service."""
    _require_user()
    db = _db_or_fail()
    if not force and not click.confirm(f"Delete service {service_id[:8]}...?"):
        return
    if not db.delete_service(service_id):
        raise click.ClickException("Failed to delete service.")
    click.echo("Service deleted.")


@services.command("check")
@click.argument("service_id")
@click.option("--timeout", "-t", default=10, show_default=True)
@click.pass_context
def services_check(ctx, service_id, timeout):
    """Check service. Exit 1 when unhealthy or unreachable."""
    user = _require_user()
    db = _db_or_fail()
    service = db.get_service(service_id)
    if not service or service.get("user_id") != user["id"]:
        raise click.ClickException("Service not found.")
    url = service.get("url")
    if not isinstance(url, str) or not url:
        raise click.ClickException("Service URL is missing.")

    async def run():
        start = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url)
            elapsed = (datetime.now(timezone.utc) - start).total_seconds() * 1000
            healthy = response.status_code in range(200, 400)
            db.log_health_check(service_id, response.status_code, int(elapsed), healthy)
            db.update_service_status(service_id, "healthy" if healthy else "degraded", int(elapsed))
            return {
                "service_id": service_id,
                "url": url,
                "status_code": response.status_code,
                "latency_ms": round(elapsed, 2),
                "healthy": healthy,
            }
        except (httpx.HTTPError, RuntimeError, ValueError, TypeError, OSError) as error:
            db.log_health_check(service_id, 0, 0, False, str(error))
            db.update_service_status(service_id, "down", 0)
            return {"service_id": service_id, "url": url, "healthy": False, "error": str(error)}

    result = asyncio.run(run())
    click.echo(
        json.dumps(result, indent=2)
        if _json(ctx)
        else (
            f"HEALTHY {result.get('status_code')} | {result.get('latency_ms', 0)}ms"
            if result["healthy"]
            else f"DOWN | {result.get('error') or result.get('status_code')}"
        )
    )
    if not result["healthy"]:
        raise click.exceptions.Exit(1)
