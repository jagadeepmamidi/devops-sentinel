"""Environment and connectivity diagnostics."""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List

import httpx

from sentinel.cli.auth import get_current_user, is_logged_in


async def _check_api_health(api_url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            resp = await client.get(f"{api_url}/health")
            return resp.status_code == 200
    except Exception:
        return False


def run_doctor(strict: bool = False) -> Dict[str, Any]:
    """Run environment and connectivity diagnostics."""
    api_url = os.getenv("API_URL", "http://localhost:8000")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    web_url = os.getenv("SENTINEL_WEB_URL")
    llm_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")

    api_ok = asyncio.run(_check_api_health(api_url))
    auth_ok = is_logged_in()
    user = get_current_user() if auth_ok else None

    checks: List[Dict[str, str]] = [
        {
            "name": "Supabase URL",
            "status": "ok" if supabase_url else "fail",
            "detail": supabase_url or "Missing SUPABASE_URL",
        },
        {
            "name": "Supabase Key",
            "status": "ok" if supabase_key else "fail",
            "detail": "Configured" if supabase_key else "Missing SUPABASE_KEY or SUPABASE_ANON_KEY",
        },
        {
            "name": "CLI Login",
            "status": "ok" if auth_ok else "warn",
            "detail": f"Logged in as {user.get('email', 'unknown')}" if auth_ok else "Not logged in",
        },
        {
            "name": "Web Auth URL",
            "status": "ok" if web_url else "warn",
            "detail": web_url or "SENTINEL_WEB_URL not set (fallback auth is still supported)",
        },
        {
            "name": "LLM Provider Key",
            "status": "ok" if llm_key else "warn",
            "detail": "Configured" if llm_key else "Missing OPENROUTER_API_KEY or OPENAI_API_KEY",
        },
        {
            "name": "API Health",
            "status": "ok" if api_ok else "warn",
            "detail": f"{api_url}/health reachable" if api_ok else f"API not reachable at {api_url}/health",
        },
    ]

    failed = [c for c in checks if c["status"] == "fail"]
    warnings = [c for c in checks if c["status"] == "warn"]
    passed = len(failed) == 0 and (len(warnings) == 0 if strict else True)

    return {
        "checks": checks,
        "strict": strict,
        "passed": passed,
        "failed_count": len(failed),
        "warning_count": len(warnings),
    }
