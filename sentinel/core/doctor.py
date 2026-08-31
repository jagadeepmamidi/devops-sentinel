"""Environment and connectivity diagnostics."""

from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx

from sentinel.cli.auth import get_current_user, get_storage_mode, is_logged_in
from sentinel.cli.db import get_db
from sentinel.core.postmortem_generator import PostmortemGenerator


async def _check_api_health(api_url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            response = await client.get(f"{api_url}/health")
            return response.status_code in range(200, 400)
    except httpx.HTTPError:
        return False


def _check_postmortem_runtime() -> tuple[str, str]:
    """Confirm the postmortem generator imports; LLM keys remain optional."""
    try:
        PostmortemGenerator()
    except (ImportError, RuntimeError, TypeError, ValueError) as error:
        return "fail", f"Postmortem generator unavailable: {error}"
    llm_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if llm_key:
        return "ok", "Template generator ready; LLM key present"
    return "ok", "Template generator ready; LLM optional (fallback is labeled)"


def run_doctor(strict: bool = False) -> dict[str, Any]:
    """Run diagnostics with mode-aware storage checks."""
    api_url = os.getenv("API_URL", "http://localhost:8000")
    mode = get_storage_mode()
    web_url = os.getenv("SENTINEL_WEB_URL")
    llm_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    api_ok = asyncio.run(_check_api_health(api_url))
    auth_ok = is_logged_in()
    user = get_current_user() if auth_ok else None
    user_email = user.get("email", "unknown") if isinstance(user, dict) else "unknown"

    if mode == "none":
        storage_checks = [
            {
                "name": "Initialized",
                "status": "fail",
                "detail": "Run `sentinel init` for local SQLite (or `--mode supabase` for your project)",
            }
        ]
    elif mode == "local":
        local_db = get_db()
        storage_checks = [
            {
                "name": "Storage (SQLite)",
                "status": "ok" if local_db.connected else "fail",
                "detail": str(local_db.path)
                if local_db.connected
                else "SQLite could not be opened",
            },
            {
                "name": "CLI Identity",
                "status": "ok" if auth_ok else "fail",
                "detail": "Local identity active" if auth_ok else "Local identity unavailable",
            },
        ]
    else:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        storage_checks = [
            {
                "name": "Supabase URL",
                "status": "ok" if supabase_url else "fail",
                "detail": supabase_url or "Missing SUPABASE_URL",
            },
            {
                "name": "Supabase Key",
                "status": "ok" if supabase_key else "fail",
                "detail": "Configured"
                if supabase_key
                else "Missing SUPABASE_KEY or SUPABASE_ANON_KEY",
            },
            {
                "name": "CLI Login",
                "status": "ok" if auth_ok else "warn",
                "detail": f"Logged in as {user_email}" if auth_ok else "Not logged in",
            },
        ]

    checks = storage_checks + [
        {
            "name": "Web Auth URL",
            "status": "ok" if web_url else "warn",
            "detail": web_url or "Not required for local mode",
        },
        {
            "name": "LLM Provider Key",
            "status": "ok" if llm_key else "warn",
            "detail": "Configured" if llm_key else "Optional; postmortems use a labeled template fallback",
        },
        {
            "name": "API Health",
            "status": "ok" if api_ok else "warn",
            "detail": f"{api_url}/health reachable"
            if api_ok
            else f"API not reachable at {api_url}/health (only needed for `sentinel serve`)",
        },
    ]

    postmortem_status, postmortem_detail = _check_postmortem_runtime()
    checks.append(
        {"name": "Postmortem Runtime", "status": postmortem_status, "detail": postmortem_detail}
    )

    failed = [check for check in checks if check["status"] == "fail"]
    warnings = [check for check in checks if check["status"] == "warn"]
    passed = not failed and (not warnings if strict else True)
    return {
        "mode": mode,
        "checks": checks,
        "strict": strict,
        "passed": passed,
        "failed_count": len(failed),
        "warning_count": len(warnings),
    }
