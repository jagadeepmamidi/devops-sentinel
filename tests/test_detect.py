from pathlib import Path

from sentinel.core.detect import (
    DIAG_HTTP_5XX,
    DIAG_LATENCY,
    DIAG_UNKNOWN,
    DIAG_UNREACHABLE,
    MODEL_BASELINE,
    MODEL_IFOREST,
    MODEL_WARMUP,
    WARMUP_N,
    detect_check,
    diagnose_http,
    format_detect_fields,
    latency_zscore,
)


def _row(latency, status=200, healthy=True):
    return {
        "response_time_ms": latency,
        "status_code": status,
        "is_healthy": healthy,
    }


def test_diagnose_http_closed_set():
    assert diagnose_http(False, None, "timeout") == DIAG_UNREACHABLE
    assert diagnose_http(False, 503, "") == DIAG_HTTP_5XX
    assert diagnose_http(False, 404, "") == "http_4xx"
    assert diagnose_http(False, 200, "", ["body missing 'ok'"]) == "expect_mismatch"
    assert diagnose_http(False, 200, "", ["TLS expires in 3d (min 14d)"]) == "tls"
    assert diagnose_http(True, 200, "") == DIAG_UNKNOWN
    assert diagnose_http(False, 503, "status 503 is not 2xx/3xx") == DIAG_HTTP_5XX


def test_warmup_does_not_watch(tmp_path):
    history = [_row(40) for _ in range(5)]
    detection = detect_check(
        history,
        healthy=True,
        status_code=200,
        latency_ms=900,
        service_id="svc-1",
        model_dir=tmp_path,
    )
    assert detection.model_id == MODEL_WARMUP
    assert detection.diag == DIAG_UNKNOWN
    assert detection.watch is False


def test_http_failure_diagnoses_without_watch(tmp_path):
    history = [_row(40) for _ in range(WARMUP_N)]
    detection = detect_check(
        history,
        healthy=False,
        status_code=503,
        latency_ms=40,
        service_id="svc-1",
        model_dir=tmp_path,
    )
    assert detection.diag == DIAG_HTTP_5XX
    assert detection.watch is False


def test_baseline_watch_on_latency_when_sklearn_forced_off(tmp_path, monkeypatch):
    import sentinel.core.detect as detect

    monkeypatch.setattr(detect, "SKLEARN_AVAILABLE", False)
    history = [_row(50) for _ in range(WARMUP_N)]
    detection = detect_check(
        history,
        healthy=True,
        status_code=200,
        latency_ms=400,
        service_id="svc-1",
        model_dir=tmp_path,
    )
    assert detection.model_id == MODEL_BASELINE
    assert detection.watch is True
    assert detection.diag == DIAG_LATENCY
    assert detection.anomaly_score is not None
    zscore = latency_zscore(400, history)
    assert zscore is not None
    assert abs(zscore) >= 3


def test_iforest_watch_on_latency_outlier(tmp_path: Path):
    history = [_row(50 + (i % 5)) for i in range(WARMUP_N)]
    detection = detect_check(
        history,
        healthy=True,
        status_code=200,
        latency_ms=8000,
        service_id="svc-forest",
        model_dir=tmp_path,
    )
    assert detection.model_id == MODEL_IFOREST
    assert detection.watch is True
    assert detection.diag == DIAG_LATENCY
    assert (tmp_path / "svc-forest.pkl").exists()


def test_iforest_inlier_does_not_watch(tmp_path: Path):
    history = [_row(50 + (i % 5)) for i in range(WARMUP_N)]
    detection = detect_check(
        history,
        healthy=True,
        status_code=200,
        latency_ms=52,
        service_id="svc-forest-ok",
        model_dir=tmp_path,
    )
    assert detection.model_id == MODEL_IFOREST
    assert detection.watch is False
    assert detection.diag == DIAG_UNKNOWN


def test_unregistered_url_stays_warmup():
    history = [_row(50) for _ in range(WARMUP_N)]
    detection = detect_check(
        history,
        healthy=True,
        status_code=200,
        latency_ms=8000,
        service_id=None,
        model_dir=None,
    )
    assert detection.model_id == MODEL_WARMUP
    assert detection.watch is False


def test_format_detect_fields():
    text = format_detect_fields({"diag": "http_5xx", "model_id": "iforest", "anomaly_score": 1.234})
    assert text == "diag=http_5xx | model=iforest | anomaly=1.23"
