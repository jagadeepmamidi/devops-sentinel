"""
Enhanced Incident Memory - Protected Similarity Search
=======================================================

Find similar past incidents with confidence thresholds
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio


class IncidentMemory:
    """
    Enhanced Incident Memory with protection
    
    Features:
    - Confidence threshold filtering
    - Explanation generation
    - Dismissal tracking (user feedback)
    - Protected from bad suggestions
    """
    
    # Only suggest incidents above this similarity threshold
    CONFIDENCE_THRESHOLD = 0.82
    
    # Minimum threshold to even consider
    MINIMUM_THRESHOLD = 0.60
    
    def __init__(self, supabase_client, embedding_client=None):
        self.supabase = supabase_client
        self.embedding_client = embedding_client
    
    async def find_similar_incidents(
        self,
        incident: Dict,
        limit: int = 5,
        include_low_confidence: bool = False
    ) -> Dict:
        """
        Find similar past incidents with confidence protection
        
        Args:
            incident: Current incident to find matches for
            limit: Max number of similar incidents to return
            include_low_confidence: Include medium-confidence matches
        
        Returns:
            Dict with suggestion, explanation, and confidence info
        """
        # Get embedding for current incident
        embedding = incident.get('embedding')
        
        if not embedding:
            # Generate embedding if not present
            embedding = await self._generate_embedding(incident)
        
        if not embedding:
            return {
                'suggestion': None,
                'reason': 'Unable to generate embedding for comparison',
                'confidence': 0
            }
        
        # Search for similar incidents using pgvector
        similar = await self._vector_similarity_search(
            embedding=embedding,
            service_id=incident.get('service_id'),
            exclude_id=incident.get('id'),
            limit=limit * 2  # Get extra to filter
        )
        
        if not similar:
            return {
                'suggestion': None,
                'reason': 'No similar past incidents found',
                'confidence': 0
            }
        
        # Filter by confidence threshold
        threshold = self.MINIMUM_THRESHOLD if include_low_confidence else self.CONFIDENCE_THRESHOLD
        
        high_confidence = [
            s for s in similar 
            if s.get('similarity_score', 0) >= threshold
        ]
        
        if not high_confidence:
            return {
                'suggestion': None,
                'reason': 'No confident matches found (threshold: {:.0%})'.format(threshold),
                'confidence': max(s.get('similarity_score', 0) for s in similar) if similar else 0,
                'below_threshold': True
            }
        
        # Get the best match
        best_match = high_confidence[0]
        confidence = best_match.get('similarity_score', 0)
        
        # Generate explanation
        explanation = self._generate_explanation(incident, best_match)
        
        return {
            'suggestion': {
                'incident_id': best_match.get('id'),
                'title': best_match.get('title'),
                'service_name': best_match.get('service_name'),
                'failure_type': best_match.get('failure_type'),
                'resolution': best_match.get('resolution_notes'),
                'time_to_resolve': best_match.get('time_to_resolve_minutes'),
                'occurred_at': best_match.get('detected_at')
            },
            'confidence': confidence,
            'confidence_level': self._get_confidence_level(confidence),
            'explanation': explanation,
            'disclaimer': 'This might be related - here\'s why:',
            'dismissible': True,
            'feedback_prompt': 'Was this suggestion helpful?',
            'similar_count': len(high_confidence),
            'all_matches': [
                {
                    'id': s.get('id'),
                    'confidence': s.get('similarity_score'),
                    'title': s.get('title')
                }
                for s in high_confidence[:limit]
            ]
        }
    
    def _generate_explanation(self, current: Dict, past: Dict) -> str:
        """Generate plain-English explanation for why incidents matched"""
        reasons = []
        
        # Same service
        if current.get('service_id') == past.get('service_id'):
            reasons.append(f"Same service ({current.get('service_name', 'unknown')})")
        
        # Same failure type
        if current.get('failure_type') == past.get('failure_type'):
            reasons.append(f"Same failure type ({current.get('failure_type')})")
        
        # Similar error signature
        current_error = current.get('error_message', '')
        past_error = past.get('error_message', '')
        if current_error and past_error:
            if self._similar_error_signature(current_error, past_error):
                reasons.append("Similar error message pattern")
        
        # Similar time of day (might indicate scheduled jobs)
        current_time = current.get('detected_at')
        past_time = past.get('detected_at')
        if current_time and past_time:
            try:
                curr_hour = datetime.fromisoformat(current_time.replace('Z', '+00:00')).hour
                past_hour = datetime.fromisoformat(past_time.replace('Z', '+00:00')).hour
                if abs(curr_hour - past_hour) <= 1:
                    reasons.append("Occurred at similar time of day")
            except:
                pass
        
        # Vector similarity is high
        similarity = past.get('similarity_score', 0)
        if similarity >= 0.90:
            reasons.append(f"Very high semantic similarity ({similarity:.0%})")
        elif similarity >= 0.85:
            reasons.append(f"High semantic similarity ({similarity:.0%})")
        
        if not reasons:
            reasons.append(f"Pattern similarity ({past.get('similarity_score', 0):.0%})")
        
        return " + ".join(reasons)
    
    def _similar_error_signature(self, error1: str, error2: str) -> bool:
        """Check if two error messages have similar signatures"""
        # Simple heuristic: check for common patterns
        if not error1 or not error2:
            return False
        
        # Normalize
        e1 = error1.lower()[:100]
        e2 = error2.lower()[:100]
        
        # Check for common error types
        common_patterns = [
            'connection refused',
            'timeout',
            'out of memory',
            'disk full',
            'permission denied',
            'not found',
            '500 internal',
            '503 service unavailable',
            'database connection'
        ]
        
        for pattern in common_patterns:
            if pattern in e1 and pattern in e2:
                return True
        
        # Check word overlap
        words1 = set(e1.split())
        words2 = set(e2.split())
        overlap = len(words1 & words2) / max(len(words1), len(words2), 1)
        
        return overlap > 0.5
    
    def _get_confidence_level(self, score: float) -> str:
        """Convert numeric confidence to human-readable level"""
        if score >= 0.95:
            return 'very_high'
        elif score >= 0.90:
            return 'high'
        elif score >= 0.85:
            return 'medium_high'
        elif score >= 0.82:
            return 'medium'
        else:
            return 'low'
    
    async def record_feedback(
        self,
        incident_id: str,
        suggested_incident_id: str,
        helpful: bool,
        user_id: str
    ):
        """
        Record user feedback on suggestion quality
        
        This helps improve future suggestions
        """
        await self.supabase.table('suggestion_feedback').upsert({
            'incident_id': incident_id,
            'suggested_incident_id': suggested_incident_id,
            'helpful': helpful,
            'user_id': user_id,
            'recorded_at': datetime.utcnow().isoformat()
        }).execute()
        
        # If not helpful, lower the effective similarity for future
        if not helpful:
            # Could implement learning here
            pass
    
    async def _vector_similarity_search(
        self,
        embedding: List[float],
        service_id: Optional[str] = None,
        exclude_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Perform vector similarity search using pgvector
        
        Uses cosine similarity for matching
        """
        # Build query
        query = """
            SELECT 
                id,
                title,
                service_id,
                failure_type,
                error_message,
                resolution_notes,
                time_to_resolve_minutes,
                detected_at,
                resolved_at,
                1 - (embedding <=> $1) as similarity_score
            FROM incidents
            WHERE status = 'resolved'
            AND embedding IS NOT NULL
        """
        
        params = [embedding]
        
        if service_id:
            query += " AND service_id = $2"
            params.append(service_id)
        
        if exclude_id:
            idx = len(params) + 1
            query += f" AND id != ${idx}"
            params.append(exclude_id)
        
        query += f"""
            ORDER BY embedding <=> $1
            LIMIT {limit}
        """
        
        # Execute via Supabase RPC or direct query
        # This is a simplified version - actual implementation depends on Supabase setup
        try:
            result = await self.supabase.rpc(
                'search_similar_incidents',
                {
                    'query_embedding': embedding,
                    'match_count': limit,
                    'service_filter': service_id,
                    'exclude_incident': exclude_id
                }
            ).execute()
            
            return result.data or []
        except Exception as e:
            print(f"Vector search error: {e}")
            return []
    
    async def _generate_embedding(self, incident: Dict) -> Optional[List[float]]:
        """Generate embedding for incident using OpenAI/other API"""
        if not self.embedding_client:
            return None
        
        # Build text to embed
        text = self._build_embedding_text(incident)
        
        try:
            # Call embedding API
            response = await self.embedding_client.create_embedding(text)
            return response.embedding
        except Exception as e:
            print(f"Embedding generation error: {e}")
            return None
    
    def _build_embedding_text(self, incident: Dict) -> str:
        """Build text representation for embedding"""
        parts = []
        
        if incident.get('title'):
            parts.append(f"Title: {incident['title']}")
        
        if incident.get('failure_type'):
            parts.append(f"Failure: {incident['failure_type']}")
        
        if incident.get('error_message'):
            # Truncate long error messages
            error = incident['error_message'][:500]
            parts.append(f"Error: {error}")
        
        if incident.get('description'):
            parts.append(f"Description: {incident['description'][:500]}")
        
        return "\n".join(parts)


# Database function for similarity search (add via migration)
SIMILARITY_SEARCH_FUNCTION = """
CREATE OR REPLACE FUNCTION search_similar_incidents(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    service_filter uuid DEFAULT NULL,
    exclude_incident uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    title text,
    service_id uuid,
    failure_type text,
    error_message text,
    resolution_notes text,
    time_to_resolve_minutes int,
    detected_at timestamptz,
    resolved_at timestamptz,
    similarity_score float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id,
        i.title,
        i.service_id,
        i.failure_type,
        i.error_message,
        i.resolution_notes,
        i.time_to_resolve_minutes,
        i.detected_at,
        i.resolved_at,
        1 - (i.embedding <=> query_embedding) as similarity_score
    FROM incidents i
    WHERE i.status = 'resolved'
    AND i.embedding IS NOT NULL
    AND (service_filter IS NULL OR i.service_id = service_filter)
    AND (exclude_incident IS NULL OR i.id != exclude_incident)
    ORDER BY i.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
"""


# Example usage
if __name__ == "__main__":
    async def demo():
        class MockSupabase:
            def table(self, name):
                return self
            def upsert(self, data):
                return self
            def rpc(self, name, params):
                return self
            async def execute(self):
                class R:
                    data = [{
                        'id': 'past-inc-1',
                        'title': 'Redis connection timeout',
                        'service_id': 'svc-1',
                        'failure_type': 'connection_timeout',
                        'resolution_notes': 'Restarted Redis pod, cleared connection pool',
                        'time_to_resolve_minutes': 15,
                        'detected_at': '2026-01-20T10:00:00Z',
                        'similarity_score': 0.89
                    }]
                return R()
        
        memory = IncidentMemory(MockSupabase())
        
        result = await memory.find_similar_incidents({
            'id': 'current-inc',
            'service_id': 'svc-1',
            'service_name': 'API Gateway',
            'failure_type': 'connection_timeout',
            'error_message': 'Error connecting to Redis: connection refused',
            'embedding': [0.1] * 1536  # Mock embedding
        })
        
        if result.get('suggestion'):
            print(f"Found similar incident!")
            print(f"Confidence: {result['confidence']:.0%}")
            print(f"Explanation: {result['explanation']}")
            print(f"Resolution: {result['suggestion']['resolution']}")
        else:
            print(f"No similar incidents: {result.get('reason')}")
    
    asyncio.run(demo())
