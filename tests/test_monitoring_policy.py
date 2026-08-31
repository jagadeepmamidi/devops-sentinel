from sentinel.core.monitoring_policy import (
    MonitoringState,
    MonitoringThresholds,
    advance_monitoring_state,
    seed_monitoring_state,
    should_open_incident,
    should_resolve_incident,
)


def test_advance_monitoring_state_tracks_failure_streak():
    state = advance_monitoring_state(MonitoringState(), False)
    state = advance_monitoring_state(state, False)

    assert state.consecutive_failures == 2
    assert state.consecutive_healthy == 0


def test_advance_monitoring_state_resets_failures_after_healthy_check():
    state = MonitoringState(consecutive_failures=3)
    state = advance_monitoring_state(state, True)

    assert state.consecutive_failures == 0
    assert state.consecutive_healthy == 1


def test_seed_monitoring_state_uses_latest_streak():
    state = seed_monitoring_state(
        [
            {"is_healthy": False},
            {"is_healthy": False},
            {"is_healthy": True},
        ]
    )

    assert state.consecutive_failures == 2
    assert state.consecutive_healthy == 0


def test_should_open_incident_only_after_threshold():
    thresholds = MonitoringThresholds(failure_threshold=3, recovery_threshold=2)

    assert not should_open_incident(MonitoringState(consecutive_failures=2), thresholds, has_active_incident=False)
    assert should_open_incident(MonitoringState(consecutive_failures=3), thresholds, has_active_incident=False)
    assert not should_open_incident(
        MonitoringState(consecutive_failures=5), thresholds, has_active_incident=True
    )


def test_should_resolve_incident_only_after_recovery_threshold():
    thresholds = MonitoringThresholds(failure_threshold=3, recovery_threshold=2)

    assert not should_resolve_incident(MonitoringState(consecutive_healthy=1), thresholds, has_active_incident=True)
    assert should_resolve_incident(MonitoringState(consecutive_healthy=2), thresholds, has_active_incident=True)
    assert not should_resolve_incident(
        MonitoringState(consecutive_healthy=5), thresholds, has_active_incident=False
    )


def test_seed_monitoring_state_empty_and_healthy_streak():
    assert seed_monitoring_state([]) == MonitoringState()
    state = seed_monitoring_state([{"is_healthy": True}, {"is_healthy": True}, {"is_healthy": False}])
    assert state.consecutive_healthy == 2
    assert state.consecutive_failures == 0
