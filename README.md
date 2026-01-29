# DevOps Sentinel

[![PyPI version](https://img.shields.io/pypi/v/devops-sentinel.svg)](https://pypi.org/project/devops-sentinel/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Autonomous SRE Agent System** - Reduce Mean Time to Detection (MTTD) from minutes to under 10 seconds.

**[Install from PyPI](https://pypi.org/project/devops-sentinel/)** | [Documentation](https://devops-sentinel-i2ygm8zfs-jagadeeps-projects-10f14bee.vercel.app/) | [GitHub](https://github.com/jagadeepmamidi/devops-sentinel)

## Features

- **Continuous Monitoring** - Health checks at configurable intervals
- **Multi-Agent Analysis** - CrewAI-powered investigation and root cause analysis
- **AI Postmortems** - Automated incident documentation
- **Incident Memory** - Learn from past incidents with similarity matching
- **Real-time Dashboard** - WebSocket-powered live updates
- **CLI Interface** - Terminal-first developer experience
- **Privacy-First** - No telemetry, transparent data handling

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      DevOps Sentinel                         │
├─────────────────────────────────────────────────────────────┤
│  CLI (Typer)  │  API (FastAPI)  │  Dashboard (WebSocket)    │
├─────────────────────────────────────────────────────────────┤
│                   Monitoring Orchestrator                    │
├─────────────────────────────────────────────────────────────┤
│  Watcher Agent  │  Triage Agent  │  Investigator  │  Strategist  │
├─────────────────────────────────────────────────────────────┤
│  Health Check  │  Slack Alert  │  Log Analysis  │  DB Health  │
├─────────────────────────────────────────────────────────────┤
│  Supabase (Persistence)  │  OpenRouter (LLM)  │  Slack       │
└─────────────────────────────────────────────────────────────┘
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

# Check a service health
sentinel health https://api.example.com

# Monitor a service continuously
sentinel monitor https://api.example.com/health

# View your projects
sentinel projects list
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `sentinel init` | Interactive configuration setup |
| `sentinel monitor <url>` | Monitor a service URL |
| `sentinel status` | Show monitored services |
| `sentinel incidents` | List recent incidents |
| `sentinel postmortem <id>` | View incident postmortem |
| `sentinel serve` | Start dashboard server |
| `sentinel lint <path>` | Run pre-deploy checks |

## Configuration

Create a `.env` file or run `sentinel init`:

```env
OPENROUTER_API_KEY=your_key_here
DEFAULT_MODEL=google/gemini-pro
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

## Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f sentinel
```

## How It Works

1. **Watcher Agent** continuously monitors service health endpoints
2. On failure, **First Responder** sends a Slack alert
3. **Investigator** analyzes logs, deployments, and database status
4. **Strategist** creates a prioritized action plan
5. AI generates a structured postmortem saved to Supabase

## Privacy

- All data stays local or in YOUR Supabase instance
- No telemetry or external data collection
- Use `--privacy` flag to see exactly what data is processed
- OpenRouter calls only contain health check context (no PII)

## Supabase Schema

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
