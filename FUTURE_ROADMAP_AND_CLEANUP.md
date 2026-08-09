# DevOps Sentinel Future Roadmap and Cleanup

## Purpose

This document is the persistent source for future plans after the MVP recovery work. It complements, and does not replace, the current-state docs:

- `MVP_RECOVERY_SOP.md` for implemented behavior and operating instructions
- `SYSTEM_FLOW_MAP.md` for the compact architecture and process map

## Current Product Position

DevOps Sentinel is currently positioned as:

- a CLI-first monitoring MVP
- backed by one canonical FastAPI backend
- using Supabase for auth and persistence
- exposing a lightweight operator console
- keeping AI optional and only after incident creation

## Future Roadmap

### Phase 1: Production Hardening

- add a dedicated background monitoring worker so checks do not depend on a foreground terminal loop
- implement explicit thresholded failure detection for incident open and resolve decisions
- add structured logging with request IDs, service IDs, and incident IDs
- validate startup configuration for Supabase, notifications, and optional AI providers
- separate process health from dependency readiness in health endpoints
- add retry and backoff handling for transient network failures

### Phase 2: Operator Maturity

- replace pasted bearer-token auth with proper browser session auth
- add create, edit, activate, deactivate, and delete actions for services in the UI
- add a service detail page with recent health checks and incident context
- add incident filters, search, and pagination
- add a real incident timeline section in the operator UI

### Phase 3: Incident Operations

- extend `incident_events` beyond detect/resolve/postmortem into acknowledgement, assignment, and note history
- support incident acknowledgement and assignment
- add notification routing abstractions for Slack, email, and PagerDuty
- add maintenance windows and alert suppression support
- expose metrics APIs for MTTR, incident counts, and unhealthy services

### Phase 4: AI and Knowledge Layer

- add a provider abstraction for optional AI-backed postmortems and summaries
- generate AI summaries only after incident creation succeeds
- add similarity search against past incidents
- extract action items from postmortems once incident events are first-class data

### Phase 5: Team and Platform Expansion

- add team membership and role-based access control
- add multi-project dashboards
- correlate incidents with deployments and change events
- integrate with public or internal status pages
- treat on-call rotation and auto-remediation as later platform work, not MVP work

## Near-Term Priorities

- background monitoring worker mode
- browser session auth for the operator console
- service CRUD in the operator UI
- threshold-based incident open and recovery logic
- structured logging and metrics-ready instrumentation

## Mid-Term Roadmap

- notification routing across Slack, email, and PagerDuty
- incident acknowledgements and assignments
- metrics and reporting endpoints
- service detail pages with health-check history
- incident search, filtering, and pagination

## Long-Term Expansion Ideas

- similarity search and incident memory workflows
- action-item extraction and ownership tracking
- deployment correlation and change feeds
- team dashboards and role-based access
- status page publishing and later auto-remediation hooks

## Next API and CLI Additions

### Planned API additions

- `PATCH /api/services/{id}`
- `GET /api/services/{id}`
- `GET /api/services/{id}/health-checks`
- `GET /api/incidents/{id}/events`
- `POST /api/incidents/{id}/acknowledge`
- `POST /api/incidents/{id}/assign`
- `GET /api/metrics/summary`

### Planned CLI additions

- `sentinel services update`
- `sentinel services history`
- `sentinel incidents show <id>`
- `sentinel incidents acknowledge <id>`
- `sentinel worker run`

## Cleanup Policy

Default cleanup policy: conservative cleanup only.

This means cleanup should remove generated artifacts and temporary outputs, but should not delete legacy code, assistant-related folders, or compatibility files without a separate audit and approval.

## Safe Cleanup List

- `.pytest_cache/`
- `__pycache__/`
- `dist/`
- `devops_sentinel.egg-info/`
- local virtualenv folders such as `venv/` and `.venv-release/`
- generated `*.pyc`, `*.tmp`, and `*.temp` files

## Deferred Cleanup List

Keep these for now:

- `src/`
- `.agent/`
- `.gemini/`
- `api_server.py`
- `server.py`
- `migrations/`
- recovery docs such as `MVP_RECOVERY_SOP.md` and `SYSTEM_FLOW_MAP.md`

Rule: legacy or assistant-related directories are not removed unless there is a separate audit and explicit approval.

## Process Maps

### Service Registration Flow

```text
User
  -> `sentinel services add <name> <url>`
  -> auth state loaded
  -> shared DB layer inserts `services` row
  -> service appears in API and operator UI
```

### Scheduled / Background Monitoring Flow

```text
Worker scheduler
  -> selects active services
  -> runs health checks on interval
  -> normalizes result
  -> writes `health_checks` row
  -> updates latest service status
  -> passes result into threshold evaluation
```

### Threshold Evaluation Flow

```text
Latest check result
  -> compare against consecutive failure / recovery rules
  -> if failure threshold reached and no active incident:
       create incident
  -> if recovery threshold reached and active incident exists:
       resolve incident
  -> otherwise keep current state
```

### Incident Lifecycle Flow

```text
Threshold breach
  -> create incident with user/service ownership
  -> set severity and status
  -> store incident_events entry
  -> optionally emit notifications
  -> expose incident through CLI, API, and operator UI
```

### Recovery Flow

```text
Healthy checks resume
  -> active incident is located
  -> incident marked resolved
  -> resolved_at and MTTR fields updated
  -> store incident_events entry
  -> optional recovery note recorded
```

### Postmortem Flow

```text
User or UI requests postmortem
  -> load incident
  -> load incident_events timeline
  -> generate fallback or AI-assisted markdown
  -> store output on incident record
  -> store incident_events entry
  -> render result in CLI or operator UI
```

### Operator Auth Flow

```text
Current state:
  user pastes bearer token
  -> token stored locally
  -> UI calls authenticated API routes

Target state:
  browser session auth via Supabase
  -> session managed by web app
  -> API requests use managed session credentials
```

### Notification Flow

```text
Incident state change
  -> notification router evaluates configured providers
  -> sends Slack/email/PagerDuty notifications
  -> delivery result is logged for audit and troubleshooting
```

## Release and Verification Checklist

Run these after future work or cleanup:

```bash
pytest -q -o addopts=""
cd web && npm run build
python -c "from sentinel.api.app import create_app; from fastapi.testclient import TestClient; client=TestClient(create_app()); assert client.get('/health').status_code == 200"
```

## Decision Rules

Future features should be prioritized only if they improve at least one of these:

- monitoring reliability
- incident visibility
- operational correctness
- testable behavior

If a proposed feature does not improve one of those areas, it should be deprioritized until after operator maturity and incident operations are complete.
