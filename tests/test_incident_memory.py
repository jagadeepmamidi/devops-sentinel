"""
Tests for Incident Memory
=========================

Tests similar incident search and confidence thresholds
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from src.core.incident_memory import IncidentMemory


class TestIncidentMemory:
    """Tests for IncidentMemory class"""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create mock Supabase client"""
        mock = MagicMock()
        mock.table.return_value = mock
        mock.select.return_value = mock
        mock.insert.return_value = mock
        mock.upsert.return_value = mock
        mock.update.return_value = mock
        mock.eq.return_value = mock
        mock.gte.return_value = mock
        mock.order.return_value = mock
        mock.limit.return_value = mock
        
        # Mock RPC for vector search
        mock_rpc_result = MagicMock()
        mock_rpc_result.execute = AsyncMock(return_value=MagicMock(data=[]))
        mock.rpc.return_value = mock_rpc_result
        
        mock.execute = AsyncMock(return_value=MagicMock(data=[]))
        return mock
    
    @pytest.fixture
    def memory(self, mock_supabase):
        return IncidentMemory(mock_supabase)
    
    def test_init(self, memory):
        """Should initialize with Supabase client"""
        assert memory.supabase is not None
    
    def test_confidence_threshold(self, memory):
        """Should have 82% confidence threshold"""
        assert memory.CONFIDENCE_THRESHOLD >= 0.82
    
    def test_minimum_threshold(self, memory):
        """Should have minimum threshold"""
        assert memory.MINIMUM_THRESHOLD > 0
        assert memory.MINIMUM_THRESHOLD < memory.CONFIDENCE_THRESHOLD
    
    @pytest.mark.asyncio
    async def test_find_similar_no_embedding(self, memory):
        """Should handle missing embedding gracefully"""
        result = await memory.find_similar_incidents(
            incident={'id': 'inc-1', 'title': 'Test'}
            # No embedding and no embedding_client
        )
        
        # Should return no suggestion when can't generate embedding
        assert result['suggestion'] is None
        assert 'embedding' in result.get('reason', '').lower() or result['confidence'] == 0
    
    @pytest.mark.asyncio
    async def test_find_similar_with_embedding_no_results(self, memory, mock_supabase):
        """Should handle no similar incidents found"""
        # RPC returns no data
        mock_rpc_result = MagicMock()
        mock_rpc_result.execute = AsyncMock(return_value=MagicMock(data=[]))
        mock_supabase.rpc.return_value = mock_rpc_result
        
        result = await memory.find_similar_incidents(
            incident={
                'id': 'inc-1',
                'title': 'Test',
                'embedding': [0.1] * 1536  # Provide embedding
            }
        )
        
        assert result['suggestion'] is None
        assert 'No similar' in result.get('reason', '') or result['confidence'] == 0
    
    @pytest.mark.asyncio
    async def test_find_similar_filters_low_confidence(self, memory, mock_supabase):
        """Should filter out low confidence matches"""
        # Return a low-confidence match
        mock_rpc_result = MagicMock()
        mock_rpc_result.execute = AsyncMock(return_value=MagicMock(data=[
            {
                'id': 'inc-old',
                'title': 'Old incident',
                'similarity_score': 0.50  # Below threshold
            }
        ]))
        mock_supabase.rpc.return_value = mock_rpc_result
        
        result = await memory.find_similar_incidents(
            incident={
                'id': 'inc-1',
                'title': 'Test',
                'embedding': [0.1] * 1536
            }
        )
        
        # Should not suggest low-confidence match
        assert result['suggestion'] is None
        assert result.get('below_threshold') is True or 'threshold' in result.get('reason', '').lower()
    
    @pytest.mark.asyncio
    async def test_find_similar_returns_high_confidence_match(self, memory, mock_supabase):
        """Should return high-confidence matches"""
        # Return a high-confidence match
        mock_rpc_result = MagicMock()
        mock_rpc_result.execute = AsyncMock(return_value=MagicMock(data=[
            {
                'id': 'inc-old',
                'title': 'Database timeout',
                'service_id': 'svc-1',
                'failure_type': 'timeout',
                'resolution_notes': 'Restarted connection pool',
                'similarity_score': 0.92
            }
        ]))
        mock_supabase.rpc.return_value = mock_rpc_result
        
        result = await memory.find_similar_incidents(
            incident={
                'id': 'inc-1',
                'title': 'Database connection error',
                'embedding': [0.1] * 1536
            }
        )
        
        assert result['suggestion'] is not None
        assert result['confidence'] >= 0.82
    
    @pytest.mark.asyncio
    async def test_record_feedback(self, memory, mock_supabase):
        """Should record user feedback"""
        mock_supabase.execute = AsyncMock(return_value=MagicMock(data=[]))
        
        await memory.record_feedback(
            incident_id='inc-1',
            suggested_incident_id='inc-old',
            helpful=True,
            user_id='user-1'
        )
        
        # Verify upsert was called
        mock_supabase.table.assert_called_with('suggestion_feedback')
        mock_supabase.upsert.assert_called()


class TestExplanationGeneration:
    """Tests for explanation generation"""
    
    @pytest.fixture
    def memory(self):
        return IncidentMemory(MagicMock())
    
    def test_generate_explanation_same_service(self, memory):
        """Should explain same-service match"""
        current = {'service_id': 'svc-1', 'service_name': 'API'}
        past = {'service_id': 'svc-1', 'similarity_score': 0.88}
        
        explanation = memory._generate_explanation(current, past)
        
        assert len(explanation) > 0
        assert 'service' in explanation.lower() or 'API' in explanation
    
    def test_generate_explanation_same_failure_type(self, memory):
        """Should explain same-failure-type match"""
        current = {'failure_type': 'timeout'}
        past = {'failure_type': 'timeout', 'similarity_score': 0.85}
        
        explanation = memory._generate_explanation(current, past)
        
        assert 'timeout' in explanation.lower() or 'failure' in explanation.lower()
    
    def test_generate_explanation_high_similarity(self, memory):
        """Should indicate high similarity"""
        current = {'failure_type': 'other'}
        past = {'failure_type': 'different', 'similarity_score': 0.95}
        
        explanation = memory._generate_explanation(current, past)
        
        assert '95%' in explanation or 'high' in explanation.lower()


class TestConfidenceLevels:
    """Tests for confidence level conversion"""
    
    @pytest.fixture
    def memory(self):
        return IncidentMemory(MagicMock())
    
    def test_very_high_confidence(self, memory):
        """Should return very_high for >= 0.95"""
        level = memory._get_confidence_level(0.96)
        assert level == 'very_high'
    
    def test_high_confidence(self, memory):
        """Should return high for >= 0.90"""
        level = memory._get_confidence_level(0.92)
        assert level == 'high'
    
    def test_medium_high_confidence(self, memory):
        """Should return medium_high for >= 0.85"""
        level = memory._get_confidence_level(0.87)
        assert level == 'medium_high'
    
    def test_medium_confidence(self, memory):
        """Should return medium for >= 0.82"""
        level = memory._get_confidence_level(0.83)
        assert level == 'medium'
    
    def test_low_confidence(self, memory):
        """Should return low for < 0.82"""
        level = memory._get_confidence_level(0.70)
        assert level == 'low'


class TestErrorSignatureMatching:
    """Tests for error signature comparison"""
    
    @pytest.fixture
    def memory(self):
        return IncidentMemory(MagicMock())
    
    def test_matching_error_patterns(self, memory):
        """Should detect matching error patterns"""
        e1 = "Error: connection timeout after 30s"
        e2 = "Connection timeout occurred after 25s"
        
        result = memory._similar_error_signature(e1, e2)
        assert result is True
    
    def test_different_error_patterns(self, memory):
        """Should detect non-matching errors"""
        e1 = "Error: out of memory"
        e2 = "Connection refused by host"
        
        result = memory._similar_error_signature(e1, e2)
        assert result is False
    
    def test_empty_errors(self, memory):
        """Should handle empty error messages"""
        result = memory._similar_error_signature("", "")
        assert result is False
    
    def test_none_errors(self, memory):
        """Should handle None error messages"""
        result = memory._similar_error_signature(None, None)
        assert result is False


class TestEmbeddingText:
    """Tests for embedding text generation"""
    
    @pytest.fixture
    def memory(self):
        return IncidentMemory(MagicMock())
    
    def test_build_embedding_text(self, memory):
        """Should combine incident fields for embedding"""
        incident = {
            'title': 'Database Error',
            'failure_type': 'connection_error',
            'error_message': 'Connection refused',
            'description': 'Primary DB not responding'
        }
        
        text = memory._build_embedding_text(incident)
        
        assert 'Database Error' in text
        assert 'connection_error' in text
        assert 'Connection refused' in text
    
    def test_build_embedding_text_partial(self, memory):
        """Should handle partial incident data"""
        incident = {'title': 'Simple Error'}
        
        text = memory._build_embedding_text(incident)
        
        assert 'Simple Error' in text
