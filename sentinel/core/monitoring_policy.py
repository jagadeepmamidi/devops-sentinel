"""
Monitoring threshold policy helpers shared by CLI and future workers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True)
class MonitoringThresholds:
    failure_threshold: int = 3
    recovery_threshold: int = 2


@dataclass(frozen=True)
class MonitoringState:
    consecutive_failures: int = 0
    consecutive_healthy: int = 0


def advance_monitoring_state(state: MonitoringState, is_healthy: bool) -> MonitoringState:
    """Advance the in-memory health streaks with a new observation."""
    if is_healthy:
        return MonitoringState(
            consecutive_failures=0,
            consecutive_healthy=state.consecutive_healthy + 1,
        )
    return MonitoringState(
        consecutive_failures=state.consecutive_failures + 1,
        consecutive_healthy=0,
    )


def seed_monitoring_state(checks: Iterable[Mapping[str, object]]) -> MonitoringState:
    """
    Rebuild the current streak from the latest stored health checks.

    The input is expected newest-first, matching the current DB query order.
    """
    checks = list(checks)
    if not checks:
        return MonitoringState()

    first_is_healthy = bool(checks[0].get("is_healthy"))
    streak = 0
    for check in checks:
        if bool(check.get("is_healthy")) != first_is_healthy:
            break
        streak += 1

    if first_is_healthy:
        return MonitoringState(consecutive_healthy=streak)
    return MonitoringState(consecutive_failures=streak)


def should_open_incident(
    state: MonitoringState,
    thresholds: MonitoringThresholds,
    has_active_incident: bool,
) -> bool:
    return not has_active_incident and state.consecutive_failures >= thresholds.failure_threshold


def should_resolve_incident(
    state: MonitoringState,
    thresholds: MonitoringThresholds,
    has_active_incident: bool,
) -> bool:
    return has_active_incident and state.consecutive_healthy >= thresholds.recovery_threshold
