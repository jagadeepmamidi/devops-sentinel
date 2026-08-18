"""
DevOps Sentinel - Core Intelligence Module
==========================================

Core modules for intelligent incident management:
- Failure classification with confidence scoring
- Baseline monitoring for degraded state detection
- Incident memory with vector similarity search
- Dependency graph analysis
- Runbook matching engine
"""

from .baseline_monitor import BaselineMonitor, DegradationAlert
from .classifier import FailureClassifier, FailureType
from .dependency_analyzer import DependencyAnalyzer, DependencyType
from .incident_memory import IncidentMemory
from .runbook_matcher import RunbookMatcher

__all__ = [
    'BaselineMonitor',
    'DegradationAlert',
    'DependencyAnalyzer',
    'DependencyType',
    'FailureClassifier',
    'FailureType',
    'IncidentMemory',
    'RunbookMatcher',
]

__version__ = '1.0.0-phase1'
