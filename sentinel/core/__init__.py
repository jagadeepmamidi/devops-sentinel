"""Core helpers used by the CLI: health checks, thresholds, incidents, postmortems."""

from .baseline_monitor import BaselineMonitor, DegradationAlert
from .classifier import FailureClassifier, FailureType
from .incident_memory import IncidentMemory
from .runbook_matcher import RunbookMatcher

__all__ = [
    "BaselineMonitor",
    "DegradationAlert",
    "DependencyAnalyzer",
    "DependencyType",
    "FailureClassifier",
    "FailureType",
    "IncidentMemory",
    "RunbookMatcher",
]


def __getattr__(name):
    if name in {"DependencyAnalyzer", "DependencyType"}:
        from .dependency_analyzer import DependencyAnalyzer, DependencyType

        return DependencyAnalyzer if name == "DependencyAnalyzer" else DependencyType
    raise AttributeError(name)
