# DevOps Sentinel

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Local-first SRE CLI for HTTP health checks, thresholded incidents, and postmortems.**

This is a command-line tool you install with pip. The website is documentation plus a live 503 demo for that CLI — not a hosted control plane. Sentinel does not store your data.

Source: [github.com/jagadeepmamidi/devops-sentinel](https://github.com/jagadeepmamidi/devops-sentinel) · Package: [devops-sentinel-next on PyPI](https://pypi.org/project/devops-sentinel-next/) · Site: [devops-sentinel-seven.vercel.app](https://devops-sentinel-seven.vercel.app/)

## What it is today

| Shipped | Optional | Not shipped |
| --- | --- | --- |
| `sentinel init` / local SQLite | Bring-your-own Supabase | Hosted SaaS / account wall |
| HTTP health checks (`health`, `monitor`, `up`) | Slack webhook on incident open | CrewAI / live multi-agent runtime |
| Failure and recovery thresholds | LLM postmortem when you set a key | Autonomous remediation that mutates infra |
| Incident open/resolve + event timeline | MCP (`pip install "...[mcp]"`) | Production-grade ML anomaly engine |
| Labeled template postmortems | `sentinel serve` operator API (localhost) | Transactional outbox / Kafka / FAISS |

The website (`web/`) is a Vite SPA: docs, a live failing-endpoint demo, a BYO-Supabase auth helper, and an optional operator UI that talks to **your** `sentinel serve` process.

## Quick start

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

- Data: `.sentinel/sentinel.db` in the initialized project
- Identity: `local@localhost`
- Login: not required
- API server: not required for CLI monitoring
- AI and Slack: optional

```bash
sentinel whoami
sentinel config
sentinel doctor
sentinel demo
sentinel up --once
sentinel monitor https://api.example.com/health --failure-threshold 3
sentinel health https://api.example.com/health --expect 200 --json-path status --ssl-min-days 14
sentinel postmortem generate <incident-id> --output postmortem.md
```

Commit `sentinel.yaml` (written by `sentinel init`) and run `sentinel up` to register those services. Example: `examples/sentinel.yaml`.

Optional richer checks on `health` and `monitor`: `--expect` status codes, `--body` substring, `--json-path` / `--json-equals`, `--ssl-min-days`. When a monitor opens an incident it prints a card with `incidents show`, `ack`, and `postmortem generate`.

Run `sentinel init --mode supabase` only when using **your** Supabase project. Sentinel does not host customer data.

```bash
sentinel init --mode supabase --url https://YOUR-PROJECT.supabase.co
sentinel schema --print   # paste into your SQL editor
sentinel login            # authenticates against YOUR project
sentinel supabase doctor  # URL, anon key, REST, tables, RLS
```

## Configuration

`.env` is loaded from the current project directory. Provider keys can also be stored in a user-level file:

```bash
sentinel config set openrouter_api_key
sentinel config set openai_api_key
sentinel config list
sentinel config remove openrouter_api_key
```

`config set` prompts with hidden input and stores values in `~/.sentinel/config.json` with restrictive permissions. Process variables and project `.env` values take precedence. `sentinel config` always masks secrets. Local mode needs no login.

`sentinel postmortem generate` calls OpenRouter (or OpenAI) when a key is present. Default model is `openai/gpt-4o-mini` with `SENTINEL_LLM_MAX_TOKENS=1024`. If the model call fails, the CLI writes the local template and **says so** (yellow stderr plus a footer in the markdown). The HTTP generate endpoint returns `source` and `fallback_reason` so a template report is never presented as AI-authored.

`sentinel monitor https://…` auto-registers the URL so failure thresholds persist incidents. `--notify` posts `SLACK_WEBHOOK_URL` when an incident opens.

`sentinel serve` binds **127.0.0.1** by default. In local mode `/api/services` and `/api/incidents` do not require a bearer token — that is intentional for localhost. Binding `0.0.0.0` (Docker/Render, or `--host 0.0.0.0`) prints a warning; do not expose that API to the public internet without auth.

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

Configuration precedence: process environment, project `.env`, user config, defaults. Secrets are redacted by `sentinel config`.

Service commands:

```bash
sentinel services add production-api https://api.example.com/health
sentinel services list
sentinel services check <service-id>
```

HTTP 2xx and 3xx responses count as reachable. Redirects still appear with their response code.

MCP is optional:

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
CLI (canonical)
  → health check → SQLite (or your Supabase)
  → open/resolve incidents using failure/recovery thresholds
  → template postmortem, or LLM if a key is set (fallback is labeled)

Website (this repo's web/)
  → docs + live 503 demo for the CLI
  → optional operator UI → your local `sentinel serve`
```

Storage is behind `SentinelDB`. SQLite uses the same project, service, health-check, incident, event, and postmortem method contracts as the Supabase adapter.

## Monitoring and incident lifecycle

1. Register a service.
2. Run a single check or continuous monitor.
3. Persist health-check evidence.
4. Open incidents after failure-threshold evaluation.
5. Record detection and recovery events.
6. Resolve after recovery-threshold evaluation.
7. Generate a **labeled** template postmortem, or an LLM draft when a key works.

Failure and recovery thresholds prevent one transient request from opening or resolving an incident. MTTD is left unset when there is not enough evidence to compute it.

## Incident-response stages

The CLI pipeline is:

```text
Health check
    ↓
Detect              Failure, latency, or SSL
    ↓
Open / notify       Incident row + optional Slack
    ↓
Plan                Template or optional LLM postmortem
    ↓
Human               Destructive remediation is not auto-executed
```

`sentinel agents` prints this map. It is **not** a CrewAI crew and does not run a separate agent process.

MCP hosts can query read-only operational context: `health_check`, `health_check_batch`, `doctor`, `list_incidents`, `get_incident`, `get_incident_events`, `analyze_anomaly`, `generate_postmortem`.

Do not expose remote MCP to the public internet without authentication.

GitHub Action for a one-shot health probe: `.github/actions/sentinel-health`. Copy `examples/github-health.yml` into a consuming repo.

## Website

The marketing site is a client-rendered SPA. Static HTML includes the GitHub and PyPI links so a crawler that cannot execute JavaScript can still find the repo.

```bash
cd web
npm install
npm run dev
```

Operator routes talk to a FastAPI process you run (`sentinel serve`), not a hosted backend:

- `/operator/services`
- `/operator/incidents`
- `/operator/incidents/:incidentId`

## npm client

`packages/client` calls the HTTP API. It does not duplicate Python monitoring logic.

## Development

Dependencies live in `pyproject.toml` only (`pip install -e ".[dev]"`). There is no `requirements.txt`.

```bash
python -m pip install -e ".[dev]"
pytest -q -o addopts="" --cov=sentinel.core --cov-report=term-missing
python -m ruff check sentinel tests
cd web
npm run lint
npm run build
```

Docker and Render bind `0.0.0.0` on purpose (containers must listen on all interfaces). The CLI default remains localhost.

## License

MIT License.
