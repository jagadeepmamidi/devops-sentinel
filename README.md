# DevOps Sentinel Next

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Terminal-first SRE operations for health checks, incidents, evidence-backed response plans, and postmortems.**

DevOps Sentinel works locally without Supabase, an account, or an API server. Team deployments can keep using Supabase compatibility mode. Python remains canonical runtime; FastAPI, MCP, web console, and npm client use shared contracts.

## Why Sentinel?

- **Local-first:** SQLite persistence and local identity work offline.
- **Fast signal:** HTTP health checks with latency, status, SSL, retries, and suggestions.
- **Incident memory:** Store health evidence, incident timelines, response plans, and postmortems.
- **Agent-ready:** Expose safe operational context to Claude, Cursor, and other MCP hosts.
- **Multi-agent response:** Watcher, First Responder, Investigator, and Strategist roles coordinate response.
- **Safe by default:** Agents recommend remediation; destructive actions require explicit approval.
- **Scriptable:** Consistent CLI commands, JSON output, and CI-friendly API tokens.
- **Self-hostable:** Local SQLite by default, optional Supabase compatibility, no telemetry.

## Quick start — no Supabase

```bash
pip install devops-sentinel-next
sentinel init
sentinel demo
sentinel health https://api.example.com/health
sentinel services add production-api https://api.example.com/health
sentinel services list
sentinel incidents list
```

`sentinel init` defaults to local mode:

- Data: `.sentinel/sentinel.db` in initialized project
- Identity: `local@localhost`
- Login: not required
- API server: not required for CLI monitoring
- AI and Slack: optional

Useful local commands:

```bash
sentinel whoami
sentinel config
sentinel doctor
sentinel agents
sentinel demo
sentinel up --once
sentinel monitor https://api.example.com/health --failure-threshold 3
sentinel health https://api.example.com/health --expect 200 --json-path status --ssl-min-days 14
sentinel postmortem generate <incident-id> --output postmortem.md
```

Commit `sentinel.yaml` (written by `sentinel init`) and run `sentinel up` to register those services and monitor them. Example: `examples/sentinel.yaml`.

Optional richer checks on `health` and `monitor`: `--expect` status codes, `--body` substring, `--json-path` / `--json-equals`, `--ssl-min-days`. When a monitor opens an incident it prints a card with `incidents show`, `ack`, and `postmortem generate`.

Run `sentinel init --mode supabase` only when using **your** Supabase project for auth and persistence. Sentinel does not host customer data.

```bash
sentinel init --mode supabase --url https://YOUR-PROJECT.supabase.co
sentinel schema --print   # paste into your SQL editor
sentinel login            # authenticates against YOUR project
sentinel supabase doctor  # URL, anon key, REST, tables, RLS
```

## Configuration

`.env` is loaded from the current project directory. Provider keys can also be stored in a user-level file, similar to CLI auth stores:

```bash
sentinel config set openrouter_api_key
sentinel config set openai_api_key
sentinel config list
sentinel config remove openrouter_api_key
```

`config set` prompts with hidden input and stores values in `~/.sentinel/config.json` with restrictive permissions. Existing process variables and project `.env` values take precedence. `sentinel config` always masks secrets. Local mode needs no login; `sentinel login` is only for Supabase compatibility mode.

Local-first example:

```env
SENTINEL_MODE=local
SENTINEL_DATA_DIR=.sentinel
OPENROUTER_API_KEY=
SLACK_WEBHOOK_URL=
```

Optional compatibility mode:

```env
SENTINEL_MODE=supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-key
```

Configuration precedence: process environment, project `.env`, user config, defaults.
Secrets are redacted by `sentinel config`.

Service commands use the `services` namespace:

```bash
sentinel services add production-api https://api.example.com/health
sentinel services list
sentinel services check <service-id>
```

HTTP 2xx and 3xx responses count as reachable/healthy. Redirects still appear with their response code.

MCP support is optional:

```bash
pip install "devops-sentinel-next[mcp]"
sentinel mcp
```

Cursor `mcp.json` (also in `examples/mcp.json`):

```json
{
  "mcpServers": {
    "devops-sentinel": {
      "command": "sentinel",
      "args": ["mcp"]
    }
  }
}
```

## Architecture

```text
CLI / FastAPI / MCP / npm client / web console
                         ↓
                 Sentinel application
                         ↓
          Storage adapter + auth adapter
                 ↓                ↓
        SQLite local mode   Supabase compatibility
                         ↓
                  Optional AI / Slack
```

Storage is behind `SentinelDB`. SQLite uses the same project, service, health-check, incident, event, and postmortem method contracts as the Supabase adapter. Supabase remains optional so local installs do not need the Supabase Python package.

## Monitoring and incident lifecycle

1. Register a service.
2. Run a single check or continuous monitor.
3. Persist health-check evidence.
4. Open incidents after failure-threshold evaluation.
5. Record detection, alerting, investigation, and recovery events.
6. Resolve after recovery-threshold evaluation.
7. Generate fallback or optional AI-assisted postmortems.
8. Require human approval before destructive remediation.

Failure and recovery thresholds prevent one transient request from opening or resolving an incident.

## Multi-agent workflow

Sentinel uses a staged workflow. Each role has narrow responsibility and evidence context:

```text
Health check
    ↓
Watcher             Detect failure, latency, or anomaly
    ↓
First Responder     Create incident context and notify responders
    ↓
Investigator        Correlate checks, events, deployments, and dependencies
    ↓
Strategist          Produce action plan, runbook suggestion, and postmortem
    ↓
Human approval      Approve any remediation with operational side effects
```

Agent definitions live in `agents.py`; orchestration lives in `orchestrator.py`. The workflow is intentionally non-destructive. Agents can explain and propose; they cannot run arbitrary shell commands or change infrastructure without an approval boundary.

MCP hosts can query read-only operational context:

- `health_check`
- `health_check_batch`
- `doctor`
- `list_incidents`
- `get_incident`
- `get_incident_events`
- `analyze_anomaly`
- `generate_postmortem`

Start local MCP stdio mode:

```bash
sentinel mcp
```

GitHub Action for a one-shot health probe lives at `.github/actions/sentinel-health`. Copy `examples/github-health.yml` into a consuming repo. Do not add a public-URL health job as a required check on this repository.

Do not expose remote MCP directly to the public internet without authentication, authorization, rate limiting, and audit logging.

## Web console

Web console uses the same terminal language as the CLI:

- charcoal CRT background (`#242526`) and JetBrains Mono
- phosphor green for healthy status, orange-red for live/warn
- sharp corners, HUD chrome, invert-on-hover links
- keyboard-visible focus states
- working routes for docs, CLI auth (BYO Supabase), and optional operator UI

Run it during development:

```bash
cd web
npm install
npm run dev
```

Operator routes:

- `/operator/services`
- `/operator/incidents`
- `/operator/incidents/:incidentId`

## npm client

`packages/client` calls the HTTP API. It does not duplicate Python monitoring logic.

```bash
cd packages/client
npm install
npm run build
```

Publish target: `@devops-sentinel/client`.

## Development and verification

```bash
python -m pip install -e ".[dev]"
pytest -q -o addopts=""
python -m ruff check sentinel tests
cd web
npm run lint
npm run build
```


MIT License.
