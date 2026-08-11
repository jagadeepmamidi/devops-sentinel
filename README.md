# DevOps Sentinel Next

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Agent-accessible SRE operations platform** for health checks, incident operations, evidence-backed response plans, and postmortems.

[Install `devops-sentinel-next` from PyPI](https://pypi.org/project/devops-sentinel-next/) · [GitHub](https://github.com/jagadeepmamidi/devops-sentinel)

This distribution keeps Python as canonical runtime while adding a secure MCP interface and a typed npm client.

## Why use it?

- **Fast signal:** check one or many endpoints with latency, status, SSL, and suggestions.
- **Incident memory:** preserve incidents, event timelines, response plans, and postmortems.
- **Agent-ready:** expose operational context to Claude, Cursor, and other MCP hosts.
- **API-first:** CLI, web console, MCP, and npm client use shared contracts.
- **Safe by default:** remediation is not exposed as an unapproved shell; destructive runbook steps require approval.
- **Self-hostable:** Supabase persistence, optional AI, no telemetry, MIT licensed.

## Architecture

```text
CLI / FastAPI / MCP / npm client
            ↓
     Sentinel application
            ↓
   Supabase + optional AI
```

## Install

```bash
pip install devops-sentinel-next
# Optional MCP server
pip install "devops-sentinel-next[mcp]"
```

The CLI command remains `sentinel`:

```bash
sentinel doctor
sentinel health https://api.example.com/health
sentinel services list
```

## MCP

Run local stdio server:

```bash
devops-sentinel-mcp
```

Read-only tools include `health_check`, `health_check_batch`, `doctor`, `list_incidents`, `get_incident`, `get_incident_events`, `analyze_anomaly`, and `generate_postmortem`. Account-scoped tools require CLI authentication and Supabase configuration. Remote MCP deployment needs an authentication and audit layer; do not expose it directly to the public internet.

## npm client

A separate package lives in `packages/client`:

```bash
cd packages/client
npm install
npm run build
```

Publish target: `@devops-sentinel/client`. It calls the HTTP API; it does not duplicate Python monitoring logic.

## How it works

1. Register service endpoint.
2. Run health checks on schedule or on demand.
3. Store health-check evidence and latest service state.
4. Open incidents after failure policy evaluation.
5. Record detection, investigation, resolution, and postmortem events.
6. Generate fallback or optional AI-assisted postmortems.
7. Let humans approve any destructive remediation.

## Configuration

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_key
SENTINEL_WEB_URL=https://your-console.example.com
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key
```

Run `sentinel doctor` before operating.

## Security and privacy

- No telemetry or external data collection.
- Data stays in your Supabase project.
- Credentials are stored under `~/.sentinel`.
- Destructive runbook actions require approval.
- Arbitrary commands and script checks are disabled unless explicitly enabled.
- Review SSRF, authentication, and authorization controls before public deployment.

## Published package

Install latest release directly from [PyPI](https://pypi.org/project/devops-sentinel-next/):

```bash
python -m pip install --upgrade devops-sentinel-next
```

Import path and CLI remain compatible with earlier DevOps Sentinel releases. For contributor release automation, use PyPI trusted publishing through GitHub Actions.

## Development

```bash
python -m pip install -e ".[dev,mcp]"  # local development
pytest -q -o addopts=""
python -m ruff check sentinel tests
```

MIT License.
