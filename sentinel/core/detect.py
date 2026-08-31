"""Local detect + diagnose for HTTP health checks.

Incident open/resolve stays on HTTP thresholds. This module only labels a check
and may mark WATCH when the probe is still healthy.
"""

from __future__ import annotations

import json
import math
import os
import pickle
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

WARMUP_N = 20
Z_THRESHOLD = 3.0
RETRAIN_EVERY = 10
CONTAMINATION = 0.1
HISTORY_LIMIT = 200

DIAG_HTTP_5XX = "http_5xx"
DIAG_HTTP_4XX = "http_4xx"
DIAG_UNREACHABLE = "unreachable"
DIAG_LATENCY = "latency"
DIAG_EXPECT = "expect_mismatch"
DIAG_TLS = "tls"
DIAG_UNKNOWN = "unknown"

MODEL_WARMUP = "warmup"
MODEL_BASELINE = "baseline"
MODEL_IFOREST = "iforest"

try:
    from sklearn.ensemble import IsolationForest

    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    IsolationForest = None  # type: ignore[misc, assignment]
    SKLEARN_AVAILABLE = False


@dataclass(frozen=True)
class Detection:
    diag: str
    model_id: str
    anomaly_score: float | None
    watch: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "diag": self.diag,
            "model_id": self.model_id,
            "anomaly_score": self.anomaly_score,
            "watch": self.watch,
        }


def format_detect_fields(payload: dict[str, Any]) -> str:
    """Compact CLI suffix: diag=… | model=… | anomaly=…"""
    diag = payload.get("diag") or DIAG_UNKNOWN
    model = payload.get("model_id") or MODEL_WARMUP
    score = payload.get("anomaly_score")
    if isinstance(score, (int, float)) and math.isfinite(score):
        score_s = f"{score:.2f}"
    else:
        score_s = "n/a"
    return f"diag={diag} | model={model} | anomaly={score_s}"


def default_model_dir(db: Any | None = None) -> Path:
    if db is not None and getattr(db, "path", None):
        return Path(db.path).expanduser().parent / "models"
    data_dir = os.getenv("SENTINEL_DATA_DIR")
    if data_dir:
        return Path(data_dir).expanduser() / "models"
    return Path.cwd() / ".sentinel" / "models"


def status_class(status_code: int | None, healthy: bool) -> int:
    if not healthy and (status_code is None or status_code == 0):
        return 0
    if status_code is None:
        return 0
    if 200 <= status_code < 400:
        return 2
    if 400 <= status_code < 500:
        return 1
    if status_code >= 500:
        return 3
    return 0


def diagnose_http(
    healthy: bool,
    status_code: int | None,
    error: str = "",
    expect_reasons: list[str] | None = None,
) -> str:
    """Rule-based label from probe evidence. Does not use the local model."""
    if healthy:
        return DIAG_UNKNOWN
    blob = " ".join(expect_reasons or [])
    if error:
        blob = f"{blob} {error}".strip()
    lowered = blob.lower()
    if status_code is None or status_code == 0:
        return DIAG_UNREACHABLE
    if "tls" in lowered or "certificate" in lowered:
        return DIAG_TLS
    if any(
        token in lowered
        for token in ("body missing", "json path", "expected", "not in", "not 2xx")
    ):
        return DIAG_EXPECT
    if status_code >= 500:
        return DIAG_HTTP_5XX
    if status_code >= 400:
        return DIAG_HTTP_4XX
    return DIAG_UNKNOWN


def _latencies(rows: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for row in rows:
        raw = row.get("response_time_ms")
        if raw is None:
            raw = row.get("latency_ms")
        try:
            values.append(float(raw))
        except (TypeError, ValueError):
            continue
    return values


def latency_zscore(current_ms: float | None, history: list[dict[str, Any]]) -> float | None:
    if current_ms is None:
        return None
    samples = _latencies(history)
    if len(samples) < 2:
        return None
    mean = statistics.mean(samples)
    stdev = statistics.pstdev(samples)
    delta = float(current_ms) - mean
    if stdev == 0:
        if abs(delta) < 1e-9:
            return 0.0
        return float("inf") if delta > 0 else float("-inf")
    return delta / stdev


def feature_row(latency_ms: float | None, status_code: int | None, healthy: bool) -> list[float]:
    return [
        float(latency_ms or 0),
        float(status_class(status_code, healthy)),
        float(1 if healthy else 0),
    ]


def _history_features(history: list[dict[str, Any]]) -> list[list[float]]:
    rows = []
    for item in history:
        healthy = bool(item.get("is_healthy") if "is_healthy" in item else item.get("healthy"))
        latency = item.get("response_time_ms")
        if latency is None:
            latency = item.get("latency_ms")
        rows.append(feature_row(latency, item.get("status_code"), healthy))
    return rows


def _model_paths(model_dir: Path, service_id: str) -> tuple[Path, Path]:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in service_id)[:80]
    return model_dir / f"{safe}.pkl", model_dir / f"{safe}.meta.json"


def _load_meta(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_iforest(model_dir: Path, service_id: str, model: Any, n_trained: int) -> None:
    model_dir.mkdir(parents=True, exist_ok=True)
    pkl_path, meta_path = _model_paths(model_dir, service_id)
    pkl_path.write_bytes(pickle.dumps(model, protocol=4))
    meta_path.write_text(json.dumps({"n_trained": n_trained}), encoding="utf-8")


def _load_iforest(model_dir: Path, service_id: str) -> tuple[Any | None, int]:
    pkl_path, meta_path = _model_paths(model_dir, service_id)
    meta = _load_meta(meta_path)
    n_trained = int(meta.get("n_trained") or 0)
    if not pkl_path.exists():
        return None, n_trained
    try:
        return pickle.loads(pkl_path.read_bytes()), n_trained  # noqa: S301 — local model file
    except (OSError, pickle.PickleError, TypeError, ValueError):
        return None, 0


def _fit_iforest(features: list[list[float]]) -> Any | None:
    if not SKLEARN_AVAILABLE or IsolationForest is None or len(features) < WARMUP_N:
        return None
    try:
        model = IsolationForest(
            contamination=CONTAMINATION,
            n_estimators=50,
            random_state=0,
        )
        model.fit(features)
        return model
    except (ValueError, TypeError):
        return None


def _score_iforest(model: Any, row: list[float]) -> tuple[bool, float]:
    pred = int(model.predict([row])[0])
    raw = float(model.score_samples([row])[0])
    return pred == -1, round(-raw, 4)


def detect_check(
    history: list[dict[str, Any]],
    *,
    healthy: bool,
    status_code: int | None,
    latency_ms: float | None,
    error: str = "",
    expect_reasons: list[str] | None = None,
    service_id: str | None = None,
    model_dir: Path | None = None,
) -> Detection:
    """Label one probe. WATCH only when HTTP is healthy and the local model fires."""
    http_diag = diagnose_http(healthy, status_code, error, expect_reasons)
    n = len(history)
    if n < WARMUP_N or not service_id:
        return Detection(
            diag=http_diag,
            model_id=MODEL_WARMUP,
            anomaly_score=None,
            watch=False,
        )

    directory = model_dir or default_model_dir()
    current = feature_row(latency_ms, status_code, healthy)

    if SKLEARN_AVAILABLE:
        model, n_trained = _load_iforest(directory, service_id)
        should_train = model is None or (n - n_trained) >= RETRAIN_EVERY
        if should_train:
            fitted = _fit_iforest(_history_features(history))
            if fitted is not None:
                _save_iforest(directory, service_id, fitted, n)
                model = fitted
                n_trained = n
        if model is not None:
            is_outlier, score = _score_iforest(model, current)
            zscore = latency_zscore(latency_ms, history)
            far_latency = zscore is not None and abs(zscore) >= Z_THRESHOLD
            # IsolationForest path length saturates for values far outside the
            # training min/max, so |z|>=3 still marks WATCH on this path.
            watch = bool(healthy and (is_outlier or far_latency))
            diag = DIAG_LATENCY if watch else http_diag
            return Detection(
                diag=diag,
                model_id=MODEL_IFOREST,
                anomaly_score=score,
                watch=watch,
            )

    zscore = latency_zscore(latency_ms, history)
    watch = bool(healthy and zscore is not None and abs(zscore) >= Z_THRESHOLD)
    if zscore is None:
        score: float | None = None
    elif not math.isfinite(zscore):
        score = 99.0
    else:
        score = round(abs(zscore), 4)
    return Detection(
        diag=DIAG_LATENCY if watch else http_diag,
        model_id=MODEL_BASELINE,
        anomaly_score=score,
        watch=watch,
    )
