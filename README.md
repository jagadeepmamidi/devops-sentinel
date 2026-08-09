# DevOps Sentinel

[![PyPI version](https://img.shields.io/pypi/v/devops-sentinel.svg)](https://pypi.org/project/devops-sentinel/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**CLI-first SRE agent assistant** for service health checks, incident tracking, evidence-backed response plans, and postmortem workflows.

**[Install from PyPI](https://pypi.org/project/devops-sentinel/)** | [Documentation](https://devops-sentinel-i2ygm8zfs-jagadeeps-projects-10f14bee.vercel.app/) | [GitHub](https://github.com/jagadeepmamidi/devops-sentinel)

## Features

- **Continuous Monitoring** - Health checks at configurable intervals
- **Canonical API** - One FastAPI backend for CLI, API, and operator workflows
- **AI Postmortems** - Optional post-incident documentation with a fallback generator
- **Incident Tracking** - Services, incidents, and health checks share one schema contract
- **Incident Event History** - Detect, resolve, and postmortem events are stored for auditability
- **Operator Console** - Lightweight web UI for services and incidents
- **CLI Interface** - Terminal-first developer experience
- **Privacy-First** - No telemetry, transparent data handling

Future work and cleanup policy live in `FUTURE_ROADMAP_AND_CLEANUP.md`. Current operating details live in `MVP_RECOVERY_SOP.md`.

## Architecture

```text
+--------------------- DevOps Sentinel ----------------------+
| CLI (`sentinel`) | Canonical API | Operator Console        |
+------------------------------------------------------------+
| Shared monitoring logic | Shared Supabase data layer       |
+------------------------------------------------------------+
| Services | Incidents | Health checks | Postmortems          |
+------------------------------------------------------------+
| Supabase (auth + persistence) | Optional AI | Notifications |
+------------------------------------------------------------+
```

## Installation

```bash
# Install from PyPI (recommended)
pip install devops-sentinel
```

### For Developers

```bash
# Clone the repository
git clone https://github.com/jagadeepmamidi/devops-sentinel.git
cd devops-sentinel

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in editable mode for development
pip install -e .
```

## Quick Start

```bash
# Login to DevOps Sentinel
sentinel login

# Add a service
sentinel services add my-api https://api.example.com/health

# List services
sentinel services list

# Monitor a service continuously
sentinel monitor https://api.example.com/health

# List incidents
sentinel incidents list

# Validate environment and auth
sentinel doctor
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `sentinel login` | Authenticate the CLI |
| `sentinel monitor <url>` | Monitor a service URL |
| `sentinel services list` | List registered services |
| `sentinel services add <name> <url>` | Register a monitored service |
| `sentinel services delete <service_id>` | Delete a monitored service |
| `sentinel services check <service_id>` | Run a one-off service check |
| `sentinel incidents list` | List recent incidents |
| `sentinel postmortem generate <id>` | Generate incident postmortem |
| `sentinel serve` | Start API server |
| `sentinel doctor` | Run environment diagnostics |

## Configuration

Create a `.env` file:

```env
SENTINEL_WEB_URL=https://devops-sentinel.dev
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
DEFAULT_MODEL=google/gemini-pro
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
# SUPABASE_KEY=your_anon_key  # alias also supported
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

For direct OpenAI usage, set `LLM_PROVIDER=openai`, provide `OPENAI_API_KEY`, and use a model such as `gpt-4o-mini`.

`sentinel login` opens `${SENTINEL_WEB_URL}/cli-auth` for signup/signin, then returns to the local CLI callback.

## Install Command Note

Use this exact command:

```bash
pip install devops-sentinel
```

`pip install devops sentinel` (with a space) is invalid.

## Release Checklist (GitHub + PyPI)

```bash
# 1) Sanity checks
python -m py_compile main.py config.py api_server.py sentinel\cli\main.py sentinel\cli\auth.py sentinel\api\app.py
python main.py --help
python main.py --json doctor
pytest -q -o addopts=""
cd web && npm run build

# 2) Build package
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*

# 3) Publish (PyPI)
python -m twine upload dist/*

# 4) Verify install from PyPI
python -m venv /tmp/sentinel-smoke
# Windows: python -m venv %TEMP%\sentinel-smoke
pip install devops-sentinel
sentinel --version
```

## Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f sentinel
```

## How It Works

1. The CLI or worker runs health checks against a service endpoint
2. Results are written to Supabase health-check history
3. Services are updated with the latest status and timing data
4. Failure and recovery thresholds decide when incidents open or resolve
5. Incident events are stored for timeline and audit history
6. Postmortems are generated later through the API or CLI
7. **Watcher Agent** continuously monitors service health endpoints
8. On failure, **First Responder** sends a Slack alert
9. **Investigator** analyzes logs, deployments, and database status
10. **Strategist** creates a prioritized action plan
11. The incident remains open until a human or approved remediation flow verifies recovery
12. AI generates a structured postmortem after resolution

Detection latency is measured only when the source provides both failure-start and detection timestamps. The polling monitor does not invent an MTTD value when the original failure time is unknown.

## Safety controls

- Destructive runbook steps require explicit approval by default.
- Arbitrary shell commands are disabled unless `SENTINEL_ALLOW_ARBITRARY_COMMANDS=true` is explicitly configured in a trusted environment.
- Script-based health checks are disabled unless `SENTINEL_ALLOW_SCRIPT_CHECKS=true` is explicitly configured.
- Public URL checks validate every redirect hop to reduce SSRF risk.

## Privacy

- All data stays local or in YOUR Supabase instance
- No telemetry or external data collection
- Use `sentinel doctor` to validate configuration and connectivity
- OpenRouter calls only contain health check context (no PII)

## Supabase Schema

This README shows a simplified contract. Use `supabase/schema.sql` and `migrations/008_mvp_contract_alignment.sql` as the source of truth.

```sql
-- Run these in your Supabase SQL editor
CREATE TABLE services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    check_interval INTEGER DEFAULT 10,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID REFERENCES services(id),
    status TEXT DEFAULT 'detecting',
    detected_at TIMESTAMPTZ DEFAULT now(),
    resolved_at TIMESTAMPTZ,
    mttd_seconds FLOAT,
    postmortem TEXT
);

CREATE TABLE health_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID REFERENCES services(id),
    status_code INTEGER,
    response_time_ms FLOAT,
    is_healthy BOOLEAN,
    checked_at TIMESTAMPTZ DEFAULT now()
);
```

## License

MIT License

## Release validation

```bash
python -m pip install -e ".[dev]"
pytest
rm -rf build dist devops_sentinel.egg-info
python -m build --wheel
python -m twine check dist/*
```

