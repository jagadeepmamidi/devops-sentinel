"""
Anomaly Detector - Statistical Anomaly Detection
=================================================

Detect anomalies in metrics without ML training
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import statistics
import math


class AnomalyDetector:
    """
    Simple statistical anomaly detection
    
    Uses Z-score and IQR methods - no ML training required
    Perfect for V1 before investing in ML infrastructure
    
    Supported metrics:
    - Response time
    - Error rate
    - Request count
    - CPU/memory usage
    """
    
    # Thresholds for different metrics
    THRESHOLDS = {
        'response_time': {'z_score': 3.0, 'min_samples': 10},
        'error_rate': {'z_score': 2.5, 'min_samples': 5},
        'request_count': {'z_score': 2.0, 'min_samples': 20},
        'cpu': {'z_score': 2.5, 'min_samples': 10},
        'memory': {'z_score': 2.5, 'min_samples': 10}
    }
    
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.cache = {}  # In-memory baseline cache
    
    def detect(
        self,
        metric_name: str,
        current_value: float,
        historical_values: List[float],
        method: str = 'z_score'
    ) -> Dict:
        """
        Detect if current value is anomalous
        
        Args:
            metric_name: Name of metric (response_time, error_rate, etc.)
            current_value: Current metric value
            historical_values: Historical baseline values
            method: Detection method ('z_score' or 'iqr')
        
        Returns:
            Anomaly detection result
        """
        if not historical_values:
            return {
                'is_anomaly': False,
                'reason': 'No baseline data',
                'confidence': 0
            }
        
        thresholds = self.THRESHOLDS.get(metric_name, self.THRESHOLDS['response_time'])
        
        if len(historical_values) < thresholds['min_samples']:
            return {
                'is_anomaly': False,
                'reason': f'Not enough samples (need {thresholds["min_samples"]})',
                'confidence': 0
            }
        
        if method == 'z_score':
            return self._detect_zscore(
                current_value, historical_values, thresholds['z_score']
            )
        elif method == 'iqr':
            return self._detect_iqr(current_value, historical_values)
        else:
            return {'is_anomaly': False, 'reason': 'Unknown method'}
    
    def _detect_zscore(
        self,
        value: float,
        history: List[float],
        threshold: float
    ) -> Dict:
        """Z-score based anomaly detection"""
        mean = statistics.mean(history)
        stdev = statistics.stdev(history) if len(history) > 1 else 0
        
        if stdev == 0:
            return {
                'is_anomaly': False,
                'reason': 'No variance in baseline',
                'z_score': 0,
                'mean': mean,
                'stdev': 0
            }
        
        z_score = (value - mean) / stdev
        is_anomaly = abs(z_score) > threshold
        
        # Calculate confidence based on how far beyond threshold
        if is_anomaly:
            confidence = min(1.0, (abs(z_score) - threshold) / threshold + 0.5)
        else:
            confidence = 0
        
        direction = 'high' if z_score > 0 else 'low'
        
        return {
            'is_anomaly': is_anomaly,
            'z_score': round(z_score, 2),
            'mean': round(mean, 2),
            'stdev': round(stdev, 2),
            'threshold': threshold,
            'confidence': round(confidence, 2),
            'direction': direction,
            'deviation_percent': round(abs(value - mean) / mean * 100, 1) if mean else 0
        }
    
    def _detect_iqr(
        self,
        value: float,
        history: List[float]
    ) -> Dict:
        """IQR (Interquartile Range) based detection"""
        sorted_history = sorted(history)
        n = len(sorted_history)
        
        q1 = sorted_history[n // 4]
        q3 = sorted_history[3 * n // 4]
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        is_anomaly = value < lower_bound or value > upper_bound
        
        if is_anomaly:
            if value < lower_bound:
                distance = lower_bound - value
                direction = 'low'
            else:
                distance = value - upper_bound
                direction = 'high'
            confidence = min(1.0, distance / iqr)
        else:
            confidence = 0
            direction = None
        
        return {
            'is_anomaly': is_anomaly,
            'lower_bound': round(lower_bound, 2),
            'upper_bound': round(upper_bound, 2),
            'iqr': round(iqr, 2),
            'q1': round(q1, 2),
            'q3': round(q3, 2),
            'confidence': round(confidence, 2),
            'direction': direction
        }
    
    async def check_service(
        self,
        service_id: str,
        current_metrics: Dict
    ) -> List[Dict]:
        """
        Check all metrics for a service
        
        Args:
            service_id: Service to check
            current_metrics: Current metric values
        
        Returns:
            List of detected anomalies
        """
        anomalies = []
        
        # Get historical data
        history = await self._get_service_history(service_id)
        
        for metric_name, current_value in current_metrics.items():
            if metric_name not in history:
                continue
            
            result = self.detect(
                metric_name=metric_name,
                current_value=current_value,
                historical_values=history[metric_name]
            )
            
            if result.get('is_anomaly'):
                anomalies.append({
                    'metric': metric_name,
                    'current_value': current_value,
                    'detection': result
                })
        
        return anomalies
    
    async def _get_service_history(
        self,
        service_id: str,
        hours: int = 24
    ) -> Dict[str, List[float]]:
        """Get historical metrics for service"""
        if not self.supabase:
            return {}
        
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        result = await self.supabase.table('health_checks').select(
            'response_time_ms, status_code, checked_at'
        ).eq('service_id', service_id).gte('checked_at', since).execute()
        
        if not result.data:
            return {}
        
        checks = result.data
        
        return {
            'response_time': [c['response_time_ms'] for c in checks if c.get('response_time_ms')],
            'error_rate': self._calculate_error_rates(checks)
        }
    
    def _calculate_error_rates(
        self,
        checks: List[Dict],
        window: int = 10
    ) -> List[float]:
        """Calculate rolling error rates"""
        if len(checks) < window:
            return []
        
        rates = []
        for i in range(len(checks) - window):
            window_checks = checks[i:i + window]
            errors = sum(1 for c in window_checks if c.get('status_code', 200) >= 400)
            rates.append(errors / window)
        
        return rates
    
    def explain_anomaly(self, detection: Dict, metric_name: str) -> str:
        """Generate human-readable explanation"""
        if not detection.get('is_anomaly'):
            return "No anomaly detected"
        
        direction = detection.get('direction', 'outside range')
        confidence = detection.get('confidence', 0)
        deviation = detection.get('deviation_percent', 0)
        
        explanations = {
            'response_time': f"Response time is {deviation}% {'higher' if direction == 'high' else 'lower'} than normal",
            'error_rate': f"Error rate is {deviation}% {'above' if direction == 'high' else 'below'} baseline",
            'request_count': f"Traffic is {deviation}% {'higher' if direction == 'high' else 'lower'} than expected",
            'cpu': f"CPU usage is {deviation}% {'above' if direction == 'high' else 'below'} normal",
            'memory': f"Memory usage is {deviation}% {'above' if direction == 'high' else 'below'} normal"
        }
        
        base = explanations.get(metric_name, f"Metric is {deviation}% {direction}")
        confidence_text = f" (confidence: {int(confidence * 100)}%)"
        
        return base + confidence_text


# Streaming detector for real-time monitoring
class StreamingAnomalyDetector:
    """
    Real-time anomaly detection using exponential moving average
    
    Suitable for streaming metrics without storing full history
    """
    
    def __init__(self, alpha: float = 0.1):
        """
        Args:
            alpha: Smoothing factor (0-1). Higher = more weight to recent values
        """
        self.alpha = alpha
        self.ema = {}  # Exponential moving average per metric
        self.emv = {}  # Exponential moving variance per metric
    
    def update(
        self,
        metric_name: str,
        value: float,
        threshold: float = 3.0
    ) -> Dict:
        """
        Update with new value and check for anomaly
        
        Args:
            metric_name: Metric identifier
            value: New metric value
            threshold: Z-score threshold for anomaly
        
        Returns:
            Detection result
        """
        if metric_name not in self.ema:
            # Initialize with first value
            self.ema[metric_name] = value
            self.emv[metric_name] = 0
            return {
                'is_anomaly': False,
                'reason': 'Initializing baseline'
            }
        
        # Get current estimates
        current_ema = self.ema[metric_name]
        current_emv = self.emv[metric_name]
        
        # Calculate deviation
        deviation = value - current_ema
        stdev = math.sqrt(current_emv) if current_emv > 0 else 1
        
        # Calculate z-score
        z_score = deviation / stdev if stdev > 0 else 0
        is_anomaly = abs(z_score) > threshold
        
        # Update EMA and EMV (do this AFTER checking for anomaly)
        self.ema[metric_name] = self.alpha * value + (1 - self.alpha) * current_ema
        self.emv[metric_name] = self.alpha * (deviation ** 2) + (1 - self.alpha) * current_emv
        
        return {
            'is_anomaly': is_anomaly,
            'z_score': round(z_score, 2),
            'ema': round(self.ema[metric_name], 2),
            'stdev': round(stdev, 2),
            'direction': 'high' if z_score > 0 else 'low'
        }
    
    def get_state(self) -> Dict:
        """Get current detector state"""
        return {
            'ema': self.ema.copy(),
            'emv': self.emv.copy()
        }
    
    def load_state(self, state: Dict):
        """Load detector state (for persistence)"""
        self.ema = state.get('ema', {})
        self.emv = state.get('emv', {})


# Example usage
if __name__ == "__main__":
    # Test basic detector
    detector = AnomalyDetector()
    
    # Normal baseline
    history = [100, 102, 98, 105, 97, 103, 99, 101, 104, 96]
    
    # Test normal value
    result = detector.detect('response_time', 105, history)
    print(f"Normal value (105): anomaly={result['is_anomaly']}")
    
    # Test anomalous value
    result = detector.detect('response_time', 200, history)
    print(f"Anomalous value (200): anomaly={result['is_anomaly']}, z={result.get('z_score')}")
    print(f"Explanation: {detector.explain_anomaly(result, 'response_time')}")
    
    # Test streaming detector
    streaming = StreamingAnomalyDetector(alpha=0.1)
    
    values = [100, 102, 98, 105, 97, 103, 99, 101, 104, 96, 200, 102]
    for v in values:
        result = streaming.update('latency', v)
        if result.get('is_anomaly'):
            print(f"ANOMALY at value {v}: z={result['z_score']}")
