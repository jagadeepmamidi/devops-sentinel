"""Diagnose a bring-your-own Supabase project without storing any data."""

from __future__ import annotations

import os

import httpx

REQUIRED_TABLES = (
    "profiles",
    "projects",
    "services",
    "incidents",
    "incident_events",
    "health_checks",
)


def _headers(anon_key: str) -> dict[str, str]:
    return {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "Accept": "application/json",
    }


def run_supabase_doctor(
    url: str | None = None, anon_key: str | None = None, timeout: float = 8
) -> dict:
    project_url = (url or os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = anon_key or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY") or ""
    checks: list[dict] = []

    def add(name: str, status: str, detail: str) -> None:
        checks.append({"name": name, "status": status, "detail": detail})

    if not project_url:
        add("Supabase URL", "fail", "Set SUPABASE_URL or pass --url")
    else:
        add("Supabase URL", "ok", project_url)
    if not key:
        add("Anon key", "fail", "Set SUPABASE_ANON_KEY or pass --anon-key")
    else:
        add("Anon key", "ok", "Configured")

    if project_url and key:
        rest = f"{project_url}/rest/v1/"
        try:
            response = httpx.get(rest, headers=_headers(key), timeout=timeout)
            if response.status_code in range(200, 400):
                add("REST API", "ok", f"HTTP {response.status_code}")
            elif response.status_code in {401, 403}:
                add("REST API", "fail", f"HTTP {response.status_code} — check the anon key")
            else:
                add("REST API", "fail", f"HTTP {response.status_code}")
        except httpx.HTTPError as error:
            add("REST API", "fail", str(error))

        missing = []
        present = []
        rls_locked = []
        for table in REQUIRED_TABLES:
            try:
                table_response = httpx.get(
                    f"{project_url}/rest/v1/{table}",
                    headers=_headers(key),
                    params={"select": "id", "limit": 1},
                    timeout=timeout,
                )
            except httpx.HTTPError as error:
                missing.append(f"{table} ({error})")
                continue
            if table_response.status_code in range(200, 400):
                present.append(table)
            elif table_response.status_code in {401, 403}:
                rls_locked.append(table)
            elif table_response.status_code == 404:
                missing.append(table)
            else:
                missing.append(f"{table} HTTP {table_response.status_code}")

        if missing:
            add(
                "Schema tables",
                "fail",
                "Missing: " + ", ".join(missing) + ". Run `sentinel schema --print`.",
            )
        else:
            add("Schema tables", "ok", ", ".join(present))

        if rls_locked:
            add(
                "RLS",
                "warn",
                "Anon key cannot read: "
                + ", ".join(rls_locked)
                + ". Expected until `sentinel login` uses a user JWT.",
            )
        elif present:
            add("RLS", "ok", "Tables reachable with the configured key")

    failed = [item for item in checks if item["status"] == "fail"]
    warnings = [item for item in checks if item["status"] == "warn"]
    return {
        "checks": checks,
        "passed": not failed,
        "failed_count": len(failed),
        "warning_count": len(warnings),
    }
