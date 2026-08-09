"""
DevOps Sentinel CLI - Projects Command
=======================================

Manage projects from the terminal.
"""

import json

import click

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
def projects():
    """Manage projects."""
    pass


@projects.command('list')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def projects_list(output_json):
    """List all projects."""
    user = _require_user()
    if not user:
        return

    db = get_db()
    if not db.connected:
        click.echo(click.style('Error: Database not configured. Check SUPABASE_URL and SUPABASE_KEY.', fg='red'))
        return

    projects_data = db.list_projects(user['id'])

    if output_json:
        click.echo(json.dumps(projects_data, indent=2, default=str))
        return

    if not projects_data:
        click.echo(f"\n{click.style('[SENTINEL]', fg='cyan')} No projects found.")
        click.echo("  Create one with: sentinel projects create <name>")
        return

    click.echo(f"\n{click.style('Projects', bold=True)}")
    click.echo("-" * 60)
    click.echo(f"{'Name':<25} {'Services':<10} {'Created'}")
    click.echo("-" * 60)

    for proj in projects_data:
        name = proj.get('name', 'Unnamed')[:24]
        created = str(proj.get('created_at', ''))[:10]
        click.echo(f"{name:<25} {'--':<10} {created}")

    click.echo()


@projects.command('create')
@click.argument('name')
@click.option('--description', '-d', default='', help='Project description')
@click.option('--json', 'output_json', is_flag=True, help='Output as JSON')
def projects_create(name, description, output_json):
    """Create a new project."""
    user = _require_user()
    if not user:
        return

    db = get_db()
    if not db.connected:
        click.echo(click.style('Error: Database not configured.', fg='red'))
        return

    project = db.create_project(user['id'], name, description)

    if output_json:
        click.echo(json.dumps(project, indent=2, default=str))
        return

    if project:
        click.echo(f"\n{click.style('OK', fg='green')} Created project: {name}")
        click.echo(f"  ID: {project.get('id', 'unknown')[:8]}...")
    else:
        click.echo(click.style('Error: Failed to create project.', fg='red'))


@projects.command('delete')
@click.argument('project_id')
@click.option('--force', '-f', is_flag=True, help='Skip confirmation')
def projects_delete(project_id, force):
    """Delete a project."""
    user = _require_user()
    if not user:
        return

    if not force and not click.confirm(f'Delete project {project_id[:8]}...?'):
        return

    db = get_db()
    if db.delete_project(project_id):
        click.echo(f"{click.style('OK', fg='green')} Project deleted.")
    else:
        click.echo(click.style('Error: Failed to delete project.', fg='red'))
