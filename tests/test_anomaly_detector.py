"""
Tests for Anomaly Detector
==========================

Tests statistical anomaly detection
"""

import pytest
import math
from src.core.anomaly_detector import AnomalyDetector, StreamingAnomalyDetector


class TestAnomalyDetector:
    """Tests for AnomalyDetector class"""
    
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()
    
    @pytest.fixture
    def normal_history(self):
        """Normal distribution around 100"""
        return [100, 102, 98, 105, 97, 103, 99, 101, 104, 96]
    
    def test_init(self, detector):
        """Should initialize correctly"""
        assert detector is not None
        assert detector.THRESHOLDS is not None
    
    def test_thresholds_defined(self, detector):
        """Should have thresholds for common metrics"""
        assert 'response_time' in detector.THRESHOLDS
        assert 'error_rate' in detector.THRESHOLDS
        assert 'cpu' in detector.THRESHOLDS
    
    def test_detect_normal_value(self, detector, normal_history):
        """Should not flag normal values"""
        result = detector.detect('response_time', 105, normal_history)
        
        assert result['is_anomaly'] is False
    
    def test_detect_anomalous_high_value(self, detector, normal_history):
        """Should flag extremely high values"""
        result = detector.detect('response_time', 200, normal_history)
        
        assert result['is_anomaly'] is True
        assert result['direction'] == 'high'
    
    def test_detect_anomalous_low_value(self, detector, normal_history):
        """Should flag extremely low values"""
        result = detector.detect('response_time', 10, normal_history)
        
        assert result['is_anomaly'] is True
        assert result['direction'] == 'low'
    
    def test_detect_empty_history(self, detector):
        """Should handle empty history gracefully"""
        result = detector.detect('response_time', 100, [])
        
        assert result['is_anomaly'] is False
        assert 'No baseline' in result.get('reason', '')
    
    def test_detect_insufficient_samples(self, detector):
        """Should require minimum samples"""
        result = detector.detect('response_time', 100, [100, 101])
        
        assert result['is_anomaly'] is False
        assert 'samples' in result.get('reason', '').lower() or 'Not enough' in result.get('reason', '')
    
    def test_zscore_calculation(self, detector, normal_history):
        """Should calculate z-score correctly"""
        result = detector.detect('response_time', 100, normal_history)
        
        assert 'z_score' in result
        assert 'mean' in result
        assert 'stdev' in result
        
        # Z-score for value at mean should be ~0
        assert abs(result['z_score']) < 1
    
    def test_iqr_method(self, detector, normal_history):
        """Should support IQR method"""
        result = detector.detect(
            'response_time', 200, normal_history, method='iqr'
        )
        
        assert result['is_anomaly'] is True
        assert 'lower_bound' in result
        assert 'upper_bound' in result
        assert 'iqr' in result
    
    def test_confidence_score(self, detector, normal_history):
        """Should return confidence score for anomalies"""
        result = detector.detect('response_time', 200, normal_history)
        
        assert 'confidence' in result
        assert 0 <= result['confidence'] <= 1
    
    def test_deviation_percent(self, detector, normal_history):
        """Should calculate deviation percentage"""
        result = detector.detect('response_time', 150, normal_history)
        
        assert 'deviation_percent' in result
        assert result['deviation_percent'] > 0
    
    def test_explain_anomaly(self, detector, normal_history):
        """Should generate human-readable explanation"""
        detection = detector.detect('response_time', 200, normal_history)
        explanation = detector.explain_anomaly(detection, 'response_time')
        
        assert 'response' in explanation.lower() or 'Response' in explanation
        assert '%' in explanation
    
    def test_explain_no_anomaly(self, detector):
        """Should explain non-anomaly"""
        detection = {'is_anomaly': False}
        explanation = detector.explain_anomaly(detection, 'response_time')
        
        assert 'no anomaly' in explanation.lower() or 'No anomaly' in explanation
    
    def test_uniform_data(self, detector):
        """Should handle uniform data (zero variance)"""
        uniform_history = [100] * 20
        result = detector.detect('response_time', 100, uniform_history)
        
        # Should not crash and should indicate no variance
        assert result is not None
        assert result['is_anomaly'] is False


class TestStreamingAnomalyDetector:
    """Tests for streaming detector"""
    
    @pytest.fixture
    def streaming(self):
        return StreamingAnomalyDetector(alpha=0.1)
    
    def test_init(self, streaming):
        """Should initialize with alpha"""
        assert streaming.alpha == 0.1
        assert streaming.ema == {}
        assert streaming.emv == {}
    
    def test_first_update_initializes(self, streaming):
        """Should initialize on first value"""
        result = streaming.update('metric', 100)
        
        assert result['is_anomaly'] is False
        assert 'Initializing' in result.get('reason', '')
        assert streaming.ema['metric'] == 100
    
    def test_normal_updates(self, streaming):
        """Should not flag normal updates"""
        # Initialize
        streaming.update('metric', 100)
        
        # Normal values
        for _ in range(10):
            result = streaming.update('metric', 100)
        
        result = streaming.update('metric', 102)
        assert result['is_anomaly'] is False
    
    def test_anomaly_detection(self, streaming):
        """Should detect sudden spike"""
        # Build baseline
        for v in [100, 102, 98, 100, 101, 99, 100, 101]:
            streaming.update('metric', v)
        
        # Sudden spike
        result = streaming.update('metric', 200)
        
        assert result['is_anomaly'] is True
        assert result['direction'] == 'high'
    
    def test_ema_adapts(self, streaming):
        """EMA should adapt to new values"""
        streaming.update('metric', 100)
        initial_ema = streaming.ema['metric']
        
        streaming.update('metric', 120)
        new_ema = streaming.ema['metric']
        
        # EMA should have moved toward 120
        assert new_ema > initial_ema
        assert new_ema < 120  # But not all the way
    
    def test_get_state(self, streaming):
        """Should return current state"""
        streaming.update('metric1', 100)
        streaming.update('metric2', 200)
        
        state = streaming.get_state()
        
        assert 'ema' in state
        assert 'emv' in state
        assert 'metric1' in state['ema']
        assert 'metric2' in state['ema']
    
    def test_load_state(self, streaming):
        """Should restore state"""
        state = {
            'ema': {'metric': 100},
            'emv': {'metric': 25}
        }
        
        streaming.load_state(state)
        
        assert streaming.ema['metric'] == 100
        assert streaming.emv['metric'] == 25
    
    def test_multiple_metrics(self, streaming):
        """Should track multiple metrics independently"""
        streaming.update('cpu', 50)
        streaming.update('memory', 70)
        
        assert streaming.ema['cpu'] == 50
        assert streaming.ema['memory'] == 70


class TestEdgeCases:
    """Edge case tests"""
    
    def test_negative_values(self):
        """Should handle negative values"""
        detector = AnomalyDetector()
        history = [-10, -12, -8, -11, -9, -10, -11, -9, -10, -10]
        
        result = detector.detect('response_time', -50, history)
        
        assert result['is_anomaly'] is True
    
    def test_very_large_values(self):
        """Should handle very large values"""
        detector = AnomalyDetector()
        history = [1e9, 1.1e9, 0.9e9, 1e9, 1.05e9] * 4
        
        result = detector.detect('response_time', 1e9, history)
        
        assert result is not None
    
    def test_very_small_values(self):
        """Should handle very small values"""
        detector = AnomalyDetector()
        history = [0.001, 0.0011, 0.0009, 0.001, 0.0012] * 4
        
        result = detector.detect('response_time', 0.001, history)
        
        assert result is not None
