"""
Failure Classifier - Confidence Scoring to Prevent Alert Spam
============================================================

Calculates confidence score for failures based on:
- Consecutive failures
- Error severity (status code)
- Service criticality
- Blast radius (affected downstream services)

Only triggers incidents if confidence >= threshold (default 0.6)
"""

from typing import Dict, Tuple
from enum import Enum


class FailureType(Enum):
    """Classification of failure types"""
    TRANSIENT = "transient"           # Temporary network issues, 502s
    DEPENDENCY = "dependency"         # Upstream service failure
    DEPLOYMENT = "deployment"         # Related to recent deployment
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # OOM, disk full, etc.
    ANOMALY = "anomaly"              # Detected by ML anomaly detector
    UNKNOWN = "unknown"              # Cannot classify


class FailureClassifier:
    """
    Intelligent failure classification with confidence scoring
    
    Score Calculation:
        confidence = (consecutive_failures * 0.4)
                   + (error_severity * 0.3)
                   + (service_criticality * 0.2)
                   + (blast_radius * 0.1)
    
    Thresholds:
        - >= 0.8: High confidence (definitely an incident)
        - 0.6-0.8: Medium confidence (likely an incident)
        - < 0.6: Low confidence (probably transient, don't alert)
    """
    
    # Status code severity mapping
    SEVERITY_MAP = {
        # 5xx - Server errors (high severity)
        500: 1.0,   # Internal Server Error
        501: 0.8,   # Not Implemented
        502: 0.7,   # Bad Gateway (often transient)
        503: 0.8,   # Service Unavailable
        504: 0.6,   # Gateway Timeout (often transient)
        505: 0.7,   # HTTP Version Not Supported
        
        # 4xx - Client errors (lower severity)
        400: 0.2,   # Bad Request
        401: 0.3,   # Unauthorized
        403: 0.4,   # Forbidden
        404: 0.3,   # Not Found
        408: 0.5,   # Request Timeout
        429: 0.6,   # Too Many Requests
        
        # 0 - Connection errors (high severity)
        0: 0.9,     # Connection refused, DNS failure, etc.
    }
    
    DEFAULT_SEVERITY = 0.5  # For unknown status codes
    
    def __init__(self, confidence_threshold: float = 0.6):
        """
        Initialize classifier
        
        Args:
            confidence_threshold: Minimum confidence to trigger incident (0.0-1.0)
        """
        self.confidence_threshold = confidence_threshold
    
    def calculate_confidence(
        self,
        consecutive_failures: int,
        status_code: int,
        service_criticality: float,
        blast_radius: int
    ) -> float:
        """
        Calculate confidence score for a failure
        
        Args:
            consecutive_failures: Number of consecutive health check failures
            status_code: HTTP status code (or 0 for connection failure)
            service_criticality: Service criticality score (0.0-1.0)
            blast_radius: Number of downstream services affected
        
        Returns:
            Confidence score (0.0-1.0)
        """
        # 1. Consecutive failures component (0.0-1.0)
        # Cap at 10 failures for normalization
        norm_failures = min(consecutive_failures, 10) / 10.0
        
        # 2. Error severity component (0.0-1.0)
        error_severity = self.SEVERITY_MAP.get(status_code, self.DEFAULT_SEVERITY)
        
        # 3. Service criticality component (0.0-1.0)
        # Already normalized
        norm_criticality = service_criticality
        
        # 4. Blast radius component (0.0-1.0)
        # Cap at 20 services for normalization
        norm_blast = min(blast_radius, 20) / 20.0
        
        # Weighted sum
        confidence = (
            norm_failures * 0.4 +      # 40% weight - most important
            error_severity * 0.3 +      # 30% weight - error type matters
            norm_criticality * 0.2 +    # 20% weight - service importance
            norm_blast * 0.1            # 10% weight - impact scope
        )
        
        return min(confidence, 1.0)
    
    def classify_failure(
        self,
        status_code: int,
        error_message: str,
        recent_deployment: bool = False
    ) -> FailureType:
        """
        Classify failure type based on error details
        
        Args:
            status_code: HTTP status code
            error_message: Error message text
            recent_deployment: Whether deployment happened in last 30 mins
        
        Returns:
            FailureType enum
        """
        error_lower = error_message.lower()
        
        # Check for deployment-related failures
        if recent_deployment:
            return FailureType.DEPLOYMENT
        
        # Check for resource exhaustion
        resource_keywords = ['out of memory', 'disk full', 'too many open files', 
                           'resource exhausted', 'quota exceeded']
        if any(keyword in error_lower for keyword in resource_keywords):
            return FailureType.RESOURCE_EXHAUSTION
        
        # Check for dependency failures
        dependency_keywords = ['connection refused', 'connection reset', 
                             'upstream', 'dependency', 'service unavailable']
        if any(keyword in error_lower for keyword in dependency_keywords):
            return FailureType.DEPENDENCY
        
        # Check for transient failures
        transient_keywords = ['timeout', 'temporary', 'try again', 'network', 
                            'dns', 'unreachable']
        if any(keyword in error_lower for keyword in transient_keywords):
            return FailureType.TRANSIENT
        
        # Transient status codes
        if status_code in [502, 504]:
            return FailureType.TRANSIENT
        
        return FailureType.UNKNOWN
    
    def should_trigger_incident(
        self,
        consecutive_failures: int,
        status_code: int,
        service_criticality: float,
        blast_radius: int,
        is_canary: bool = False
    ) -> Tuple[bool, float, str]:
        """
        Determine if incident should be triggered based on confidence
        
        Args:
            consecutive_failures: Number of consecutive failures
            status_code: HTTP status code
            service_criticality: Service criticality (0.0-1.0)
            blast_radius: Number of affected services
            is_canary: Whether this is a canary service
        
        Returns:
            Tuple of (should_trigger, confidence_score, reasoning)
        """
        confidence = self.calculate_confidence(
            consecutive_failures,
            status_code,
            service_criticality,
            blast_radius
        )
        
        # Canary services have higher threshold (0.8 vs 0.6)
        threshold = 0.8 if is_canary else self.confidence_threshold
        
        should_trigger = confidence >= threshold
        
        # Generate reasoning
        if should_trigger:
            reasoning = f"High confidence ({confidence:.2f}) incident detected"
            if is_canary:
                reasoning += " (canary service)"
        else:
            reasoning = f"Low confidence ({confidence:.2f}), likely transient"
        
        return should_trigger, confidence, reasoning
    
    def get_severity_level(
        self,
        confidence: float,
        service_criticality: float,
        blast_radius: int
    ) -> str:
        """
        Determine incident severity (P0-P3) based on confidence and impact
        
        P0 = Critical (customer-facing down, high blast radius)
        P1 = High (degraded performance, medium impact)
        P2 = Medium (non-critical issues)
        P3 = Low (informational)
        
        Args:
            confidence: Confidence score (0.0-1.0)
            service_criticality: Service criticality (0.0-1.0)
            blast_radius: Number of affected services
        
        Returns:
            Severity level: 'P0', 'P1', 'P2', or 'P3'
        """
        # P0: Critical service + high confidence + significant blast radius
        if service_criticality >= 0.8 and confidence >= 0.8 and blast_radius >= 3:
            return "P0"
        
        # P0: Critical service with total failure
        if service_criticality >= 1.0 and confidence >= 0.7:
            return "P0"
        
        # P1: High confidence or critical service
        if confidence >= 0.8 or service_criticality >= 0.8:
            return "P1"
        
        # P2: Medium confidence
        if confidence >= 0.6:
            return "P2"
        
        # P3: Low confidence (shouldn't happen if using threshold)
        return "P3"


# Example usage
if __name__ == "__main__":
    classifier = FailureClassifier()
    
    # Test case 1: Single transient 502 on standard service
    should_trigger, confidence, reason = classifier.should_trigger_incident(
        consecutive_failures=1,
        status_code=502,
        service_criticality=0.5,
        blast_radius=1
    )
    print(f"Test 1: {should_trigger} - {reason}")
    
    # Test case 2: 3 consecutive 500s on critical service
    should_trigger, confidence, reason = classifier.should_trigger_incident(
        consecutive_failures=3,
        status_code=500,
        service_criticality=1.0,
        blast_radius=5
    )
    print(f"Test 2: {should_trigger} - {reason}")
    severity = classifier.get_severity_level(confidence, 1.0, 5)
    print(f"  Severity: {severity}")
