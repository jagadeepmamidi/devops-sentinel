"""Health expectations: status codes, body, JSON path, and TLS expiry."""

from __future__ import annotations

import json
import socket
import ssl
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse


@dataclass
class HealthExpect:
    status_codes: tuple[int, ...] | None = None
    body_contains: str | None = None
    json_path: str | None = None
    json_equals: str | None = None
    ssl_min_days: int | None = None

    @classmethod
    def from_mapping(cls, raw: dict[str, Any] | None) -> "HealthExpect":
        if not raw:
            return cls()
        status = raw.get("status") or raw.get("status_codes")
        codes: tuple[int, ...] | None = None
        if status is not None:
            if isinstance(status, (list, tuple)):
                codes = tuple(int(item) for item in status)
            else:
                codes = tuple(int(part.strip()) for part in str(status).split(",") if part.strip())
        equals = raw.get("json_equals")
        if equals is not None and not isinstance(equals, str):
            equals = json.dumps(equals)
        ssl_min = raw.get("ssl_min_days")
        return cls(
            status_codes=codes,
            body_contains=(str(raw["body"]) if raw.get("body") is not None else None),
            json_path=raw.get("json_path") or raw.get("json"),
            json_equals=equals,
            ssl_min_days=int(ssl_min) if ssl_min is not None else None,
        )


@dataclass
class ExpectEvaluation:
    healthy: bool
    reasons: list[str] = field(default_factory=list)
    json_value: Any = None
    ssl_days: int | None = None


def json_at(data: Any, path: str) -> Any:
    current = data
    cleaned = path.strip().lstrip("$")
    if cleaned.startswith("."):
        cleaned = cleaned[1:]
    cleaned = cleaned.replace("[", ".").replace("]", "")
    for part in cleaned.split("."):
        if not part:
            continue
        if isinstance(current, list) and part.isdigit():
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            raise KeyError(path)
    return current


def _json_equals(actual: Any, expected: str) -> bool:
    if str(actual) == expected:
        return True
    lowered = expected.strip().lower()
    if isinstance(actual, bool):
        return lowered in ({"true", "1"} if actual else {"false", "0"})
    try:
        return json.loads(expected) == actual
    except (json.JSONDecodeError, TypeError, ValueError):
        return False


def check_tls_days(url: str, timeout: float = 5) -> int | None:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        return None
    host = parsed.hostname
    if not host:
        return None
    port = parsed.port or 443
    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with context.wrap_socket(sock, server_hostname=host) as wrapped:
            cert = wrapped.getpeercert()
    not_after = cert.get("notAfter") if cert else None
    if not not_after:
        return None
    expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    return (expiry - datetime.now(timezone.utc)).days


def evaluate_expect(
    *,
    status_code: int | None,
    body: str,
    url: str,
    expect: HealthExpect,
    default_status_healthy: bool,
) -> ExpectEvaluation:
    reasons: list[str] = []
    json_value = None
    ssl_days = None

    if expect.status_codes:
        if status_code not in expect.status_codes:
            reasons.append(
                f"status {status_code} not in {','.join(str(code) for code in expect.status_codes)}"
            )
    elif not default_status_healthy:
        reasons.append(f"status {status_code or 'none'} is not 2xx/3xx")

    if expect.body_contains and expect.body_contains not in (body or ""):
        reasons.append(f"body missing {expect.body_contains!r}")

    if expect.json_path:
        try:
            json_value = json_at(json.loads(body or ""), expect.json_path)
            if expect.json_equals is not None and not _json_equals(json_value, expect.json_equals):
                reasons.append(
                    f"{expect.json_path}={json_value!r} expected {expect.json_equals!r}"
                )
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as error:
            reasons.append(f"json path {expect.json_path}: {error}")

    if str(url).startswith("https://"):
        try:
            ssl_days = check_tls_days(url)
        except (OSError, ssl.SSLError, socket.timeout, ValueError) as error:
            if expect.ssl_min_days is not None:
                reasons.append(f"TLS check failed: {error}")
        if expect.ssl_min_days is not None:
            if ssl_days is None:
                reasons.append("TLS certificate could not be read")
            elif ssl_days < expect.ssl_min_days:
                reasons.append(f"TLS expires in {ssl_days}d (min {expect.ssl_min_days}d)")

    return ExpectEvaluation(
        healthy=not reasons, reasons=reasons, json_value=json_value, ssl_days=ssl_days
    )
