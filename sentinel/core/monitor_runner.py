"""Reusable asynchronous monitoring primitives for CLI and dashboard adapters."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from .monitoring_policy import (
    MonitoringState,
    MonitoringThresholds,
    advance_monitoring_state,
    seed_monitoring_state,
    should_open_incident,
    should_resolve_incident,
)

HEALTHY_STATUS_CODES = range(200, 400)


def is_healthy_status(status_code: int) -> bool:
    """Return whether HTTP status belongs to healthy 2xx/3xx range."""
    return status_code in HEALTHY_STATUS_CODES


@dataclass
class HealthCheckResult:
    url: str
    healthy: bool
    status_code: int | None = None
    latency_ms: float | None = None
    error: str | None = None
    timestamp: str = ""

    def as_dict(self) -> dict:
        result = {
            "url": self.url,
            "healthy": self.healthy,
            "status_code": self.status_code,
            "latency_ms": round(self.latency_ms, 2) if self.latency_ms is not None else None,
            "timestamp": self.timestamp,
        }
        if self.error:
            result["error"] = self.error
        return result


async def check_url_once(
    url: str, timeout: float = 10, client: httpx.AsyncClient | None = None
) -> HealthCheckResult:
    """Perform one HTTP check without persistence or presentation side effects."""
    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=timeout)
    started = datetime.now(timezone.utc)
    try:
        response = await client.get(url)
        elapsed = (datetime.now(timezone.utc) - started).total_seconds() * 1000
        return HealthCheckResult(
            url=url,
            healthy=is_healthy_status(response.status_code),
            status_code=response.status_code,
            latency_ms=elapsed,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except (httpx.HTTPError, RuntimeError, ValueError, TypeError, OSError) as error:
        elapsed = (datetime.now(timezone.utc) - started).total_seconds() * 1000
        return HealthCheckResult(
            url=url,
            healthy=False,
            latency_ms=elapsed,
            error=str(error),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    finally:
        if owns_client:
            await client.aclose()


def classify_incident(response_code: int | None, error: str = "") -> tuple[str, str]:
    """Map an observed failure into severity and incident summary."""
    if response_code is None or response_code == 0:
        return "critical", error or "Service unreachable"
    if response_code >= 500:
        return "high", f"Service returned HTTP {response_code}"
    if response_code >= 400:
        return "medium", f"Service returned HTTP {response_code}"
    return "low", error or "Degraded service response"


class MonitorRunner:
    """Run repeated checks and persist service state when service is registered."""

    def __init__(
        self,
        url: str,
        interval: float = 30,
        timeout: float = 10,
        db=None,
        user_id: str | None = None,
        service: dict | None = None,
        failure_threshold: int = 3,
        recovery_threshold: int = 2,
    ):
        self.url = url
        self.interval = interval
        self.timeout = timeout
        self.db = db
        self.user_id = user_id
        self.service = service
        self.thresholds = MonitoringThresholds(failure_threshold, recovery_threshold)
        self.state = MonitoringState()
        self.active_incident_id: str | None = None
        self.check_count = 0
        if service and db and user_id and db.connected:
            active = db.get_active_incident_for_service(user_id, service["id"])
            self.active_incident_id = active["id"] if active else None
            recent = db.get_latest_health_checks(
                service["id"], limit=max(failure_threshold, recovery_threshold)
            )
            self.state = seed_monitoring_state(recent)

    async def check(self, client: httpx.AsyncClient) -> dict:
        self.check_count += 1
        result = await check_url_once(self.url, self.timeout, client)
        self.state = advance_monitoring_state(self.state, result.healthy)
        opened = False
        resolved = False
        service_id = self.service["id"] if self.service else None
        if service_id and self.db and self.db.connected:
            self.db.log_health_check(
                service_id,
                result.status_code or 0,
                int(result.latency_ms or 0),
                result.healthy,
                result.error or "",
            )
            self.db.update_service_status(
                service_id,
                "healthy" if result.healthy else ("degraded" if result.status_code else "down"),
                int(result.latency_ms or 0),
            )
            if (
                result.healthy
                and self.active_incident_id
                and should_resolve_incident(self.state, self.thresholds, has_active_incident=True)
            ):
                resolved = self.db.resolve_incident(self.active_incident_id)
                self.active_incident_id = None if resolved else self.active_incident_id
            elif (
                not result.healthy
                and self.user_id
                and should_open_incident(
                    self.state, self.thresholds, has_active_incident=bool(self.active_incident_id)
                )
            ):
                severity, detail = classify_incident(result.status_code, result.error or "")
                incident = self.db.create_incident(
                    self.user_id,
                    service_id,
                    severity,
                    detail,
                    error_code=result.status_code,
                    status="alerting",
                )
                self.active_incident_id = incident["id"] if incident else None
                opened = self.active_incident_id is not None
        payload = result.as_dict()
        payload.update(
            {
                "check": self.check_count,
                "failure_streak": self.state.consecutive_failures,
                "healthy_streak": self.state.consecutive_healthy,
                "failure_threshold": self.thresholds.failure_threshold,
                "recovery_threshold": self.thresholds.recovery_threshold,
                "incident_opened": opened,
                "incident_resolved": resolved,
            }
        )
        return payload

    async def run_forever(self, on_result: Callable[[dict], Awaitable[None] | None]) -> None:
        """Check forever until cancelled, invoking callback after every result."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            while True:
                result = await self.check(client)
                callback_result = on_result(result)
                if asyncio.iscoroutine(callback_result):
                    await callback_result
                await asyncio.sleep(self.interval)
