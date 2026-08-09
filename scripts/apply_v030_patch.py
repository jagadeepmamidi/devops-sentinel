"""Patch script for v0.3.0."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def patch_main_py():
    path = ROOT / "sentinel/cli/main.py"
    text = path.read_text(encoding="utf-8")
    start = text.find("@cli.command()\n@click.option('--strict', is_flag=True, help='Treat warnings as failures')")
    end = text.find("@cli.command()\n@click.pass_context\ndef setup", start)
    new_block = """@cli.command()\n@click.option('--strict', is_flag=True, help='Treat warnings as failures')\n@click.pass_context\ndef doctor(ctx, strict):\n    \"\"\"Run environment and connectivity diagnostics.\"\"\"\n    from ..core.doctor import run_doctor\n\n    result = run_doctor(strict=strict)\n    checks = result[\"checks\"]\n    passed = result[\"passed\"]\n    failed = [c for c in checks if c[\"status\"] == \"fail\"]\n    warnings = [c for c in checks if c[\"status\"] == \"warn\"]\n\n    if ctx.obj.get('json'):\n        click.echo(json.dumps(result, indent=2))\n        raise SystemExit(1 if not passed else 0)\n\n    icons = {\"ok\": \"OK\", \"warn\": \"WARN\", \"fail\": \"FAIL\"}\n    colors = {\"ok\": \"green\", \"warn\": \"yellow\", \"fail\": \"red\"}\n\n    click.echo(f\"\\n{click.style('Sentinel Doctor', bold=True)}\")\n    click.echo(\"-\" * 40)\n    for item in checks:\n        marker = click.style(icons[item[\"status\"]], fg=colors[item[\"status\"]], bold=True)\n        click.echo(f\"  {marker:<6} {item['name']}: {item['detail']}\")\n    click.echo()\n\n    if not passed:\n        if failed:\n            click.echo(click.style(\"Critical checks failed. Fix required config and re-run `sentinel doctor`.\", fg='red'))\n        else:\n            click.echo(click.style(\"Warnings treated as failures in strict mode.\", fg='red'))\n        raise SystemExit(1)\n\n\n@cli.command('mcp')\ndef mcp_server():\n    \"\"\"Start the MCP server for Cursor / Claude Desktop.\"\"\"\n    from sentinel.mcp.server import main\n\n    main()\n\n\n"""
    path.write_text(text[:start] + new_block + text[end:], encoding="utf-8")

def patch_pyproject():
    path = ROOT / "pyproject.toml"
    text = path.read_text(encoding="utf-8")
    text = text.replace("version = \"0.2.0\"", "version = \"0.3.0\"")
    if "mcp = [" not in text:
        text = text.replace("ai = [\n    \"openai>=1.0\",\n    \"anthropic>=0.18\",\n]\nall = [\n    \"devops-sentinel[dev,ai]\",\n]", "ai = [\n    \"openai>=1.0\",\n    \"anthropic>=0.18\",\n]\nmcp = [\n    \"mcp>=1.2\",\n]\nall = [\n    \"devops-sentinel[dev,ai,mcp]\",\n]")
    if "devops-sentinel-mcp" not in text:
        text = text.replace("sentinel = \"sentinel.cli.main:cli\"", "sentinel = \"sentinel.cli.main:cli\"\ndevops-sentinel-mcp = \"sentinel.mcp.server:main\"")
    if "sentinel.mcp" not in text:
        text = text.replace("\"sentinel.ml\", \"sentinel.notifications\"", "\"sentinel.ml\", \"sentinel.mcp\", \"sentinel.notifications\"")
    path.write_text(text, encoding="utf-8")

def patch_versions():
    (ROOT / "sentinel/__init__.py").write_text('"""DevOps Sentinel - Autonomous SRE Agents"""\n\n__version__ = "0.3.0"\n', encoding="utf-8")
    app = ROOT / "sentinel/api/app.py"
    app.write_text(app.read_text(encoding="utf-8").replace("APP_VERSION = \"0.2.0\"", "APP_VERSION = \"0.3.0\""), encoding="utf-8")

if __name__ == "__main__":
    patch_main_py(); patch_pyproject(); patch_versions(); print("ok")
