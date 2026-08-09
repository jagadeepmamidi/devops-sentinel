# DevOps Sentinel MVP Recovery SOP

## Purpose

This document captures the monitoring MVP recovery work implemented in this repo, how the system is supposed to operate now, how to verify it later, and what still remains as follow-up work.

For future phases, cleanup policy, and planned interface additions, use `FUTURE_ROADMAP_AND_CLEANUP.md` alongside this SOP.

## What Changed

### 1. Canonical backend

- The app now has one canonical FastAPI entrypoint: `sentinel/api/app.py`
- `api_server.py` and `server.py` are thin runners that import the canonical app
- The backend now serves both API routes and the built frontend from `web/dist`

### 2. Package rename

- The runtime package moved from `src` to `sentinel`
- CLI entrypoint now resolves to `sentinel.cli.main:cli`
- Tests and imports were updated to use `sentinel.*`

### 3. Canonical monitoring API contract

Implemented routes:

- `GET /health`
- `GET /api/status`
- `GET /api/services`
- `POST /api/services`
- `DELETE /api/services/{service_id}`
- `GET /api/incidents`
- `GET /api/incidents/{incident_id}`
- `GET /api/incidents/{incident_id}/events`
- `POST /api/postmortems/generate`
- `GET /api/quick-check`
- `POST /api/quick-check/batch`
- `POST /api/auth/*`
- `GET /api/auth/me`
- `GET /api/setup/supabase/*`
- `GET /api/setup/ai/*`

### 4. Shared Supabase data layer

- CLI and API now share the same Supabase access layer in `sentinel/cli/db.py`
- Services, incidents, health checks, and postmortems now use one consistent contract
- Incident writes include `user_id`
- Postmortems are stored in the incident row via the `postmortem` field
- Incident events are stored in `incident_events` for timelines and audits

### 5. Monitoring flow simplified

The core path is now:

1. health check runs
2. service status is updated
3. health check is logged
4. failure and recovery streaks are evaluated
5. incident is created only after the configured failure threshold is reached
6. incident is resolved only after the configured recovery threshold is reached
7. incident events are stored for detect, resolve, and postmortem generation
8. postmortem can be generated later

CrewAI is no longer in the critical incident path.

### 6. Web operator console

Added lightweight operator pages:

- `/operator/services`
- `/operator/incidents`
- `/operator/incidents/:incidentId`

These pages call the canonical API and let you:

- inspect registered services
- inspect incidents
- generate a postmortem for an incident

Current auth model for the operator UI:

- paste a bearer token into the operator console
- token is stored in browser local storage
- API calls use that token

This is intentionally simple for MVP stabilization.

### 7. Test harness stabilization

- `pytest.ini` no longer hard-fails when coverage plugins are unavailable
- local async test execution works without depending on `pytest-asyncio`
- new tests were added for:
  - shared DB contract
  - canonical API routes
  - fallback postmortem generation
  - CLI monitoring incident classification

## Current Source of Truth

### Backend

- Canonical app: `sentinel/api/app.py`
- Canonical monitoring routes: `sentinel/api/mvp_routes.py`
- Shared DB layer: `sentinel/cli/db.py`
- Auth: `sentinel/auth/auth_service.py`

### Frontend

- Router: `web/src/App.jsx`
- Operator services page: `web/src/pages/OperatorServices.jsx`
- Operator incidents page: `web/src/pages/OperatorIncidents.jsx`
- Operator incident detail page: `web/src/pages/OperatorIncidentDetail.jsx`

### Schema

- Base schema: `supabase/schema.sql`
- Alignment migration: `migrations/008_mvp_contract_alignment.sql`

## Expected Schema Contract

### `profiles`

Important fields:

- `id`
- `email`
- `display_name`
- `subscription_tier`

### `services`

Important fields:

- `id`
- `user_id`
- `project_id`
- `name`
- `url`
- `check_interval`
- `is_active`
- `last_status`
- `last_response_time_ms`
- `last_checked_at`

### `incidents`

Important fields:

- `id`
- `user_id`
- `service_id`
- `status`
- `severity`
- `error_code`
- `error_message`
- `detected_at`
- `resolved_at`
- `mttr_seconds`
- `action_plan`
- `postmortem`

### `health_checks`

Important fields:

- `id`
- `service_id`
- `status_code`
- `response_time_ms`
- `is_healthy`
- `error_message`
- `checked_at`

### `incident_events`

Important fields:

- `id`
- `user_id`
- `incident_id`
- `service_id`
- `event_type`
- `description`
- `metadata`
- `created_at`

## Supported CLI Commands

Supported and aligned to the MVP:

- `sentinel login`
- `sentinel services list`
- `sentinel services add <name> <url>`
- `sentinel services delete <service_id>`
- `sentinel services check <service_id>`
- `sentinel monitor <url>`
- `sentinel monitor <url> --failure-threshold <n> --recovery-threshold <n>`
- `sentinel incidents list`
- `sentinel postmortem generate <incident_id>`
- `sentinel doctor`
- `sentinel serve`

## Operator SOP

### Local run

1. Set env vars in `.env`
2. Build frontend:

```bash
cd web
npm run build
```

3. Start backend:

```bash
python api_server.py
```

4. Open the app root or `/operator/services`

### Service registration

Option A: CLI

```bash
sentinel services add my-api https://api.example.com/health
```

Option B: API

```bash
curl -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"my-api\",\"url\":\"https://api.example.com/health\",\"check_interval\":30}" \
  http://localhost:8000/api/services
```

### Monitoring

```bash
sentinel monitor https://api.example.com/health
```

Expected behavior:

- healthy checks update service status
- failures count toward the configured failure threshold
- incidents open only after the failure threshold is reached
- recovery resolves the active incident only after the recovery threshold is reached

### Postmortem generation

CLI:

```bash
sentinel postmortem generate <incident_id>
```

API:

```bash
curl -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"incident_id\":\"<incident_id>\",\"resolution_notes\":\"Rollback completed\"}" \
  http://localhost:8000/api/postmortems/generate
```

## Verification SOP

### Python tests

```bash
pytest -q -o addopts=""
```

Expected result at time of writing:

- all tests pass

### Frontend build

```bash
cd web
npm run build
```

Expected result at time of writing:

- build succeeds

### Smoke check

```bash
python -c "from sentinel.api.app import create_app; from fastapi.testclient import TestClient; client=TestClient(create_app()); print(client.get('/health').status_code); print(client.get('/').status_code)"
```

Expected output:

- `200`
- `200`

## Required After Pulling Later

These are the important operational steps if you revisit the repo later:

1. Run the latest Supabase schema plus `migrations/008_mvp_contract_alignment.sql`
2. Rebuild `web/dist` before serving the frontend through the backend
3. Verify `.env` still contains:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY` or `SUPABASE_KEY`
   - optional auth/provider keys
4. Run:
   - `pytest -q -o addopts=""`
   - `cd web && npm run build`

## Remaining Follow-Up Items

These are not blockers for the recovered MVP, but they are still worth doing.

The canonical future-work and cleanup plan now lives in `FUTURE_ROADMAP_AND_CLEANUP.md`.

### High-value next changes

- Remove the legacy `src/` tree completely after you confirm no external tooling still imports it
- Replace operator bearer-token paste flow with proper web session auth
- Add create/update forms in the operator UI for services and filters for incidents
- Add acknowledgement and assignment flows on top of the new incident event history
- Move experimental modules behind explicit feature flags or an `experimental/` namespace

### Nice-to-have cleanup

- Add CI workflow to run backend tests and frontend build on every push
- Add typed API client for the web app
- Add structured logging and request IDs in the backend
- Add OpenAPI examples for service and incident payloads

## Current Product Position

DevOps Sentinel is now positioned as:

- a CLI-first monitoring MVP
- backed by Supabase for auth and persistence
- with a minimal operator web console
- and optional AI/fallback postmortem generation layered after incident creation

It is no longer split across multiple competing backend surfaces.
