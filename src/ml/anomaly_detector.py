"""
ML Anomaly Detector - Isolation Forest for Proactive Detection
==============================================================

Uses scikit-learn's Isolation Forest to detect anomalies in:
- Response times
- Error rates
- Traffic patterns

Enables "predict before it fails" capability.
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import pickle
import os

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not installed. Run: pip install scikit-learn")


class AnomalyDetector:
    """
    ML-based anomaly detection using Isolation Forest
    
    Features:
    - Unsupervised learning (no labeled data needed)
    - Detects outliers in multivariate data
    - Auto-trains on healthy service metrics
    - Persists models to disk
    
    Metrics Analyzed:
    - Response time (ms)
    - Error rate (%)
    - Request rate (req/s)
    """
    
    def __init__(
        self,
        contamination: float = 0.1,
        model_dir: str = "models"
    ):
        """
        Initialize anomaly detector
        
        Args:
            contamination: Expected proportion of anomalies (0.0-0.5)
            model_dir: Directory to save/load models
        """
        self.contamination = contamination
        self.model_dir = model_dir
        self.models = {}  # service_id -> {"model": IsolationForest, "scaler": StandardScaler}
        
        if not SKLEARN_AVAILABLE:
            print("Anomaly detection disabled - scikit-learn not available")
        
        # Create model directory
        os.makedirs(model_dir, exist_ok=True)
    
    def train(
        self,
        service_id: str,
        historical_data: List[Dict],
        force_retrain: bool = False
    ) -> bool:
        """
        Train anomaly detection model for a service
        
        Args:
            service_id: Service UUID
            historical_data: List of health check dicts with:
                - response_time_ms
                - error_rate (0-1)
                - request_rate
            force_retrain: Force retraining even if model exists
        
        Returns:
            True if training succeeded
        """
        if not SKLEARN_AVAILABLE:
            return False
        
        # Check if model already exists
        if service_id in self.models and not force_retrain:
            print(f"Model already trained for {service_id}")
            return True
        
        # Try loading from disk
        if not force_retrain and self._load_model(service_id):
            return True
        
        # Need at least 100 data points for good training
        if len(historical_data) < 100:
            print(f"Insufficient data for {service_id}: {len(historical_data)} samples (need 100+)")
            return False
        
        # Extract features
        features = self._extract_features(historical_data)
        
        if len(features) == 0:
            return False
        
        # Normalize features
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Train Isolation Forest
        model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100
        )
        model.fit(features_scaled)
        
        # Store model and scaler
        self.models[service_id] = {
            "model": model,
            "scaler": scaler,
            "trained_at": datetime.utcnow(),
            "sample_count": len(features)
        }
        
        # Persist to disk
        self._save_model(service_id)
        
        print(f"Trained anomaly detector for {service_id} with {len(features)} samples")
        return True
    
    def detect(
        self,
        service_id: str,
        current_metrics: Dict
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Detect if current metrics are anomalous
        
        Args:
            current_metrics: Dict with response_time_ms, error_rate, request_rate
        
        Returns:
            Tuple of (is_anomaly, anomaly_score, anomaly_type)
            - is_anomaly: True if anomalous
            - anomaly_score: -1 to 1 (lower = more anomalous)
            - anomaly_type: 'response_time', 'error_rate', 'traffic', or 'mixed'
        """
        if not SKLEARN_AVAILABLE:
            return False, 0.0, None
        
        # Load model if not in memory
        if service_id not in self.models:
            if not self._load_model(service_id):
                return False, 0.0, None
        
        model_data = self.models[service_id]
        model = model_data["model"]
        scaler = model_data["scaler"]
        
        # Extract features
        features = self._extract_features([current_metrics])
        if len(features) == 0:
            return False, 0.0, None
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Predict
        prediction = model.predict(features_scaled)[0]  # 1 = normal, -1 = anomaly
        anomaly_score = model.score_samples(features_scaled)[0]  # Lower = more anomalous
        
        is_anomaly = (prediction == -1)
        
        # Determine anomaly type
        anomaly_type = None
        if is_anomaly:
            anomaly_type = self._identify_anomaly_type(current_metrics, anomaly_score)
        
        return is_anomaly, float(anomaly_score), anomaly_type
    
    def should_alert(
        self,
        service_id: str,
        current_metrics: Dict,
        sensitivity: float = 0.8
    ) -> Tuple[bool, str]:
        """
        Determine if anomaly warrants an alert
        
        Args:
            service_id: Service UUID
            current_metrics: Current metrics
            sensitivity: Alert threshold (0-1, higher = more sensitive)
        
        Returns:
            Tuple of (should_alert, reason)
        """
        is_anomaly, score, anomaly_type = self.detect(service_id, current_metrics)
        
        if not is_anomaly:
            return False, "No anomaly detected"
        
        # More negative score = more anomalous
        # Typical range: -0.5 to 0.5
        # Alert if score < -0.2 (configurable via sensitivity)
        alert_threshold = -0.5 + (sensitivity * 0.3)  # -0.5 to -0.2
        
        if score < alert_threshold:
            reason = f"Anomalous {anomaly_type} detected (score: {score:.3f})"
            return True, reason
        
        return False, f"Anomaly not severe enough (score: {score:.3f})"
    
    def _extract_features(self, data: List[Dict]) -> np.ndarray:
        """Extract feature matrix from health check data"""
        features = []
        
        for point in data:
            # Skip if missing required fields
            if not all(k in point for k in ['response_time_ms', 'error_rate', 'request_rate']):
                continue
            
            features.append([
                float(point['response_time_ms']),
                float(point['error_rate']),
                float(point.get('request_rate', 0))
            ])
        
        return np.array(features)
    
    def _identify_anomaly_type(self, metrics: Dict, score: float) -> str:
        """Identify which metric is causing the anomaly"""
        response_time = metrics.get('response_time_ms', 0)
        error_rate = metrics.get('error_rate', 0)
        request_rate = metrics.get('request_rate', 0)
        
        # Simple heuristic: identify dominant outlier
        issues = []
        
        if response_time > 1000:  # > 1 second
            issues.append('response_time')
        
        if error_rate > 0.05:  # > 5% error rate
            issues.append('error_rate')
        
        if request_rate < 1:  # Very low traffic
            issues.append('traffic')
        
        if len(issues) == 0:
            return 'mixed'
        elif len(issues) == 1:
            return issues[0]
        else:
            return 'mixed'
    
    def _save_model(self, service_id: str):
        """Persist model to disk"""
        if service_id not in self.models:
            return
        
        model_path = os.path.join(self.model_dir, f"{service_id}.pkl")
        
        with open(model_path, 'wb') as f:
            pickle.dump(self.models[service_id], f)
    
    def _load_model(self, service_id: str) -> bool:
        """Load model from disk"""
        model_path = os.path.join(self.model_dir, f"{service_id}.pkl")
        
        if not os.path.exists(model_path):
            return False
        
        try:
            with open(model_path, 'rb') as f:
                self.models[service_id] = pickle.load(f)
            
            print(f"Loaded trained model for {service_id}")
            return True
        except Exception as e:
            print(f"Failed to load model for {service_id}: {e}")
            return False
    
    def get_model_info(self, service_id: str) -> Optional[Dict]:
        """Get information about trained model"""
        if service_id not in self.models:
            if not self._load_model(service_id):
                return None
        
        model_data = self.models[service_id]
        return {
            'service_id': service_id,
            'trained_at': model_data['trained_at'].isoformat(),
            'sample_count': model_data['sample_count'],
            'contamination': self.contamination
        }


# Example usage
if __name__ == "__main__":
    detector = AnomalyDetector()
    
    # Generate mock training data
    np.random.seed(42)
    training_data = []
    for _ in range(200):
        training_data.append({
            'response_time_ms': np.random.normal(100, 20),  # Mean 100ms, stddev 20ms
            'error_rate': np.random.uniform(0, 0.02),  # 0-2% error rate
            'request_rate': np.random.normal(50, 10)  # Mean 50 req/s
        })
    
    # Train
    success = detector.train('test-service', training_data)
    print(f"Training successful: {success}")
    
    # Test normal metrics
    normal_metrics = {
        'response_time_ms': 105,
        'error_rate': 0.01,
        'request_rate': 48
    }
    is_anomaly, score, anom_type = detector.detect('test-service', normal_metrics)
    print(f"Normal metrics - Anomaly: {is_anomaly}, Score: {score:.3f}")
    
    # Test anomalous metrics
    anomalous_metrics = {
        'response_time_ms': 850,  # Very high
        'error_rate': 0.15,  # 15% errors!
        'request_rate': 45
    }
    is_anomaly, score, anom_type = detector.detect('test-service', anomalous_metrics)
    print(f"Anomalous metrics - Anomaly: {is_anomaly}, Score: {score:.3f}, Type: {anom_type}")
