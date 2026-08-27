"""Commands for managing monitored services."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import click
import httpx

from .auth import get_active_user
from .db import get_db
from .render import (
    emit_error,
    emit_json,
    marker,
    presentation_from_context,
    render_health,
    render_services,
)


def _require_user() -> dict[str, Any]:
    user = get_active_user()
    if not user or not user.get("id"):
        emit_error("no active identity is available", "run `sentinel setup`")
    return user


def _require_db():
    db = get_db()
    if not db.connected:
        emit_error("service storage is not configured", "run `sentinel init --mode local` or configure Supabase")
    return db


@click.group()
def services() -> None:
    """Manage monitored services."""


@services.command("list")
@click.option("--project", "-p", help="Filter by project ID.")
@click.option("--json", "output_json", is_flag=True, help="Emit JSON (global --json also works).")
@click.pass_context
def services_list(ctx: click.Context, project: str | None, output_json: bool) -> None:
    """List registered services."""
    user = _require_user()
    db = _require_db()
    items = db.list_services(user["id"], project)
    root_obj = ctx.find_root().obj or {}
    ctx.obj = {**(ctx.obj or {}), "json": output_json or bool(root_obj.get("json"))}
    render_services(items, presentation_from_context(ctx))


@services.command("add")
@click.argument("name")
@click.argument("url")
@click.option("--project", "-p", help="Project ID to add the service to.")
@click.option("--interval", "-i", default=30, type=click.IntRange(min=1), show_default=True, help="Check interval in seconds.")
@click.option("--json", "output_json", is_flag=True, help="Emit JSON (global --json also works).")
@click.pass_context
def services_add(ctx: click.Context, name: str, url: str, project: str | None, interval: int, output_json: bool) -> None:
    """Register a service for monitoring."""
    user = _require_user()
    db = _require_db()
    service = db.add_service(user["id"], name, url, project, interval)
    if not service:
        emit_error("failed to add service", "check database connectivity and try again")
    root_obj = ctx.find_root().obj or {}
    ctx.obj = {**(ctx.obj or {}), "json": output_json or bool(root_obj.get("json"))}
    p = presentation_from_context(ctx)
    if p.json:
        emit_json(service)
    else:
        click.echo(f"{marker('ready', p)} Added service: {name}")
        click.echo(f"  Endpoint: {url}")
        click.echo(f"  Interval: {interval} s")
        click.echo(f"Next: sentinel monitor {url}")


@services.command("delete")
@click.argument("service_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation.")
@click.pass_context
def services_delete(ctx: click.Context, service_id: str, force: bool) -> None:
    """Delete a monitored service."""
    user = _require_user()
    db = _require_db()
    service = next((item for item in db.list_services(user["id"]) if item.get("id") == service_id), None)
    if not force:
        name = service.get("name", service_id) if service else service_id
        endpoint = service.get("url") if service else "endpoint unavailable"
        if not click.confirm(f"Delete service '{name}' ({endpoint})?"):
            return
    if not db.delete_service(service_id):
        emit_error("failed to delete service", "verify the service ID and try again")
    p = presentation_from_context(ctx)
    if p.json:
        emit_json({"deleted": service_id})
    else:
        click.echo(f"{marker('ready', p)} Deleted service {service_id}")


@services.command("check")
@click.argument("service_id")
@click.pass_context
def services_check(ctx: click.Context, service_id: str) -> None:
    """Run and record one check for a registered service."""
    user = _require_user()
    db = _require_db()
    service = next((item for item in db.list_services(user["id"]) if item.get("id") == service_id), None)
    if not service:
        emit_error(f"service {service_id} was not found", "run `sentinel services list`")
    url = service.get("url")

    async def check() -> dict[str, Any]:
        started = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url)
            elapsed = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
            healthy = response.status_code == 200
            db.log_health_check(service_id, response.status_code, elapsed, healthy)
            db.update_service_status(service_id, "healthy" if healthy else "degraded", elapsed)
            return {"url": url, "status": "healthy" if healthy else "degraded", "status_code": response.status_code, "latency_ms": elapsed, "healthy": healthy, "timestamp": datetime.now(timezone.utc).isoformat()}
        except Exception as exc:  # noqa: BLE001 - network clients expose varied transport errors
            db.log_health_check(service_id, 0, 0, False, str(exc))
            db.update_service_status(service_id, "down", 0)
            return {"url": url, "status": "down", "healthy": False, "error": str(exc), "timestamp": datetime.now(timezone.utc).isoformat()}

    result = asyncio.run(check())
    p = presentation_from_context(ctx)
    if p.json:
        emit_json({"service_id": service_id, **result})
    else:
        click.echo(f"Checking {service.get('name', service_id)}")
        render_health(result, p)
    if not result["healthy"]:
        raise click.exceptions.Exit(1)
