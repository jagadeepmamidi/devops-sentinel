"""Manage projects from terminal."""

from __future__ import annotations

import json

import click
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
        raise click.ClickException("Storage not configured. Run `sentinel init --mode local`.")
    return db


@click.group()
def projects():
    """Manage projects."""


@projects.command("list")
@click.pass_context
def projects_list(ctx):
    """List projects."""
    data = _db_or_fail().list_projects(_require_user()["id"])
    if _json(ctx):
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        table = Table(title="Projects")
        table.add_column("Name", style="bold")
        table.add_column("Description")
        table.add_column("Created")
        for item in data:
            table.add_row(
                str(item.get("name", "Unnamed")),
                str(item.get("description", "")),
                str(item.get("created_at", ""))[:10],
            )
        Console().print(table)


@projects.command("create")
@click.argument("name")
@click.option("--description", "-d", default="")
@click.pass_context
def projects_create(ctx, name, description):
    """Create project."""
    project = _db_or_fail().create_project(_require_user()["id"], name, description)
    if not project:
        raise click.ClickException("Failed to create project.")
    click.echo(json.dumps(project, default=str) if _json(ctx) else f"Created project: {name}")


@projects.command("delete")
@click.argument("project_id")
@click.option("--force", "-f", is_flag=True)
def projects_delete(project_id, force):
    """Delete project."""
    _require_user()
    db = _db_or_fail()
    if not force and not click.confirm(f"Delete project {project_id[:8]}...?"):
        return
    if not db.delete_project(project_id):
        raise click.ClickException("Failed to delete project.")
    click.echo("Project deleted.")
