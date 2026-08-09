# DevOps Sentinel System Flow Map

## Goal

This document gives a compact process map for the current monitoring MVP, plus a future roadmap for what should come next.

For the persistent future-phase backlog, cleanup policy, and planned API/CLI additions, use `FUTURE_ROADMAP_AND_CLEANUP.md` together with this flow map.

## Current System Map

### High-level architecture

```text
User / Operator
    |
    | uses
    v
CLI (`sentinel`) ----------------------------+
    |                                        |
    | direct Supabase writes                 | authenticated REST
    v                                        v
Shared DB Layer (`sentinel/cli/db.py`)   Canonical API (`sentinel/api/app.py`)
    |                                        |
    +--------------------+-------------------+
                         |
                         v
                  Supabase Tables
profiles / projects / services / incidents / incident_events / health_checks
                         |
                         v
                  Web Operator Console
        /operator/services /operator/incidents /operator/incidents/:id
```

## Current Monitoring Flow

### 1. Service registration flow

```text
User
  -> `sentinel services add <name> <url>`
  -> CLI auth state loaded
  -> Shared DB layer inserts row into `services`
  -> Service appears in API and operator UI
```

### 2. Continuous monitoring flow

```text
User
  -> `sentinel monitor <url>`
  -> HTTP check runs on interval
  -> Result classified as healthy / degraded / down
  -> health_checks row inserted
  -> services row updated with latest status + latency
  -> failure/recovery thresholds evaluated
  -> if failure threshold reached and no active incident:
       create incident
  -> if recovery threshold reached and active incident exists:
       resolve incident
```

### 3. Incident lifecycle flow

```text
Failure threshold reached
  -> classify severity
  -> create `incidents` row with:
       user_id
       service_id
       severity
       status=alerting
       error_code / error_message
  -> create `incident_events` row:
       event_type=detected
  -> operator UI can list it
  -> CLI can list it
```

### 4. Recovery flow

```text
Later healthy checks reach recovery threshold
  -> find active incident for service
  -> update incident:
       status=resolved
       resolved_at=now
       mttr_seconds=calculated
       action_plan="Recovered automatically after healthy checks passed."
  -> create `incident_events` row:
       event_type=resolved
```

### 5. Postmortem flow

```text
CLI or Operator UI
  -> request postmortem generation
  -> canonical API / CLI loads incident
  -> incident_events timeline is loaded when available
  -> fallback postmortem generator builds markdown
  -> markdown stored on incident.postmortem
  -> incident_events row added with event_type=postmortem_generated
  -> operator UI displays stored postmortem
```

## API Process Map

### Authenticated service read

```text
Browser / script
  -> GET /api/services
  -> bearer token validated
  -> request-scoped DB client created
  -> rows fetched from `services`
  -> normalized response returned
```

### Authenticated incident read

```text
Browser / script
  -> GET /api/incidents
  -> bearer token validated
  -> rows fetched from `incidents` joined with `services`
  -> normalized response returned
```

### Authenticated postmortem generation

```text
Browser / script
  -> POST /api/postmortems/generate
  -> bearer token validated
  -> incident ownership checked
  -> markdown generated
  -> incident.postmortem updated
  -> markdown returned
```

## Operator Console Flow

### Services page

```text
User opens /operator/services
  -> paste bearer token
  -> token stored in localStorage
  -> page calls GET /api/services
  -> list renders service state
```

### Incidents page

```text
User opens /operator/incidents
  -> token loaded from localStorage
  -> page calls GET /api/incidents
  -> list renders current + historical incidents
```

### Incident detail page

```text
User opens /operator/incidents/:id
  -> token loaded
  -> page calls GET /api/incidents/:id
  -> incident renders
  -> user can submit resolution notes
  -> page calls POST /api/postmortems/generate
  -> postmortem section updates
```

## Current Strengths

- one backend app instead of split API surfaces
- one shared persistence layer for CLI and API
- stable service/incident/postmortem contract
- tests and frontend build are passing
- operator UI now reflects real backend state

## Current Gaps

- web auth is still bearer-token paste, not full browser session auth
- CLI monitoring is still process-local; no background worker or scheduler service
- service creation from the operator UI is still missing
- old `src/` tree still exists in the repo as legacy code
- incidents do not yet support acknowledgement or assignment workflows

## Recommended Future Plan

## Phase 1: Production hardening

- remove legacy `src/` once external imports are confirmed clean
- add structured logging and request IDs
- add background monitoring worker mode instead of only terminal loop
- add CI badges and stricter workflow checks
- add API contract tests for auth failures and ownership boundaries

## Phase 2: Operator maturity

- add browser session auth using Supabase web auth
- add create/edit/delete service forms in the operator UI
- add incident filters, search, and pagination
- add service detail page with recent health-check history
- add incident event timeline table

## Phase 3: Real SRE workflows

- extend incident events with acknowledgement, assignment, and notes
- add alert routing abstraction for Slack / email / PagerDuty
- add acknowledgements and assignments
- add MTTR / incident frequency dashboard
- add runbook links on incident detail

## Phase 4: AI-assisted workflows

- optional AI summary on incident creation
- configurable postmortem generation providers
- similarity search against prior incidents
- action item extraction and ownership tracking
- runbook recommendation based on incident pattern

## Phase 5: Team and platform expansion

- team membership and role-based access
- multi-project dashboards
- scheduled reports
- status page integration
- deployment correlation and change feed

## Feature Backlog Ideas

### Good next features

- service detail with last 20 health checks
- retry and threshold-based alerting
- alert suppression / maintenance window
- webhook notifications
- incident export as markdown
- dashboard cards for open incidents and unhealthy services

### Later features

- anomaly detection on latency
- dependency map
- auto-remediation hooks
- on-call rotation
- GitHub deployment correlation
- incident memory / vector search

## Practical Decision Rule

When deciding whether to build something next:

1. Does it improve service monitoring reliability?
2. Does it improve incident visibility?
3. Does it reduce false assumptions in the system?
4. Can it be verified with tests and a clear API contract?

If the answer is no, it probably belongs after Phase 2.
