"""Commands for managing Sentinel projects."""

from __future__ import annotations

from typing import Any

import click

from .auth import get_active_user
from .db import get_db
from .render import emit_error, emit_json, marker, presentation_from_context, render_projects


def _require_user() -> dict[str, Any]:
    user = get_active_user()
    if not user or not user.get("id"):
        emit_error("no active identity is available", "run `sentinel setup`")
    return user


def _require_db():
    db = get_db()
    if not db.connected:
        emit_error("project storage is not configured", "configure SUPABASE_URL and SUPABASE_ANON_KEY")
    return db


@click.group()
def projects() -> None:
    """Manage projects."""


@projects.command("list")
@click.option("--json", "output_json", is_flag=True, help="Emit JSON (global --json also works).")
@click.pass_context
def projects_list(ctx: click.Context, output_json: bool) -> None:
    """List projects."""
    user = _require_user()
    db = _require_db()
    items = db.list_projects(user["id"])
    root_obj = ctx.find_root().obj or {}
    ctx.obj = {**(ctx.obj or {}), "json": output_json or bool(root_obj.get("json"))}
    render_projects(items, presentation_from_context(ctx))


@projects.command("create")
@click.argument("name")
@click.option("--description", "-d", default="", help="Project description.")
@click.option("--json", "output_json", is_flag=True, help="Emit JSON (global --json also works).")
@click.pass_context
def projects_create(ctx: click.Context, name: str, description: str, output_json: bool) -> None:
    """Create a project."""
    user = _require_user()
    db = _require_db()
    project = db.create_project(user["id"], name, description)
    if not project:
        emit_error("failed to create project", "check database connectivity and try again")
    root_obj = ctx.find_root().obj or {}
    ctx.obj = {**(ctx.obj or {}), "json": output_json or bool(root_obj.get("json"))}
    p = presentation_from_context(ctx)
    if p.json:
        emit_json(project)
    else:
        click.echo(f"{marker('ready', p)} Created project: {name}")
        click.echo(f"  ID: {project.get('id', 'unknown')}")


@projects.command("delete")
@click.argument("project_id")
@click.option("--force", "-f", is_flag=True, help="Skip confirmation.")
@click.pass_context
def projects_delete(ctx: click.Context, project_id: str, force: bool) -> None:
    """Delete a project after confirmation."""
    user = _require_user()
    db = _require_db()
    project = next((item for item in db.list_projects(user["id"]) if item.get("id") == project_id), None)
    if not force:
        name = project.get("name", project_id) if project else project_id
        if not click.confirm(f"Delete project '{name}'?"):
            return
    if not db.delete_project(project_id):
        emit_error("failed to delete project", "verify the project ID and try again")
    p = presentation_from_context(ctx)
    if p.json:
        emit_json({"deleted": project_id})
    else:
        click.echo(f"{marker('ready', p)} Deleted project {project_id}")
