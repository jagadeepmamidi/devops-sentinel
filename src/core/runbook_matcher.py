"""
Runbook Matcher - Smart Playbook Matching Engine
================================================

Automatically matches incidents to relevant runbooks/playbooks based on:
- Error message patterns (regex matching)
- Tags and keywords
- Service type
- Historical effectiveness

Tracks runbook usage and success rates for continuous improvement.
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class RunbookMatcher:
    """
    Matches incidents to relevant runbooks and tracks effectiveness
    
    Features:
    - Pattern-based matching (regex on error messages)
    - Tag-based categorization
    - Service-specific runbooks
    - Effectiveness tracking (success rate)
    - Auto-suggest best runbook based on past success
    """
    
    def __init__(self, db_client=None):
        """
        Initialize runbook matcher
        
        Args:
            db_client: Database client for fetching/storing runbooks
        """
        self.db = db_client
        self.runbooks_cache = []  # Cache for performance
    
    async def find_matching_runbooks(
        self,
        service_id: str,
        error_message: str,
        error_code: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Find runbooks that match the incident
        
        Args:
            service_id: Service UUID
            error_message: Error message text
            error_code: HTTP status code or error code
            tags: Additional tags (e.g., ['database', 'timeout'])
        
        Returns:
            List of matching runbooks, sorted by relevance and success rate
        """
        # Fetch runbooks for this service (and global runbooks)
        runbooks = await self._fetch_runbooks(service_id)
        
        if not runbooks:
            return []
        
        matches = []
        
        for runbook in runbooks:
            # Calculate match score
            score = self._calculate_match_score(
                runbook,
                error_message,
                error_code,
                tags or []
            )
            
            if score > 0:
                matches.append({
                    **runbook,
                    'match_score': score,
                    'confidence': self._get_confidence(runbook, score)
                })
        
        # Sort by (success_rate * match_score) descending
        matches.sort(
            key=lambda x: x.get('success_rate', 0.5) * x['match_score'],
            reverse=True
        )
        
        return matches
    
    async def get_best_runbook(
        self,
        service_id: str,
        error_message: str,
        error_code: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """
        Get the single best runbook for this incident
        
        Args:
            service_id: Service UUID
            error_message: Error message
            error_code: Error code
            tags: Additional tags
        
        Returns:
            Best matching runbook or None
        """
        matches = await self.find_matching_runbooks(
            service_id,
            error_message,
            error_code,
            tags
        )
        
        if not matches:
            return None
        
        # Return highest scoring runbook
        return matches[0]
    
    async def record_runbook_usage(
        self,
        runbook_id: str,
        success: bool,
        incident_id: Optional[str] = None
    ):
        """
        Record runbook usage and update effectiveness metrics
        
        Args:
            runbook_id: Runbook UUID
            success: Whether runbook led to successful resolution
            incident_id: Related incident ID (optional)
        """
        if not self.db:
            return
        
        # TODO: Implement database update
        # UPDATE runbooks 
        # SET times_used = times_used + 1,
        #     success_count = success_count + (1 if success else 0)
        # WHERE id = runbook_id
        
        print(f"Recorded runbook {runbook_id} usage: {'success' if success else 'failure'}")
    
    async def create_runbook(
        self,
        service_id: str,
        title: str,
        description: str,
        steps: List[Dict],
        error_pattern: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Create a new runbook
        
        Args:
            service_id: Service UUID (or 'global' for all services)
            title: Runbook title
            description: Detailed description
            steps: List of steps [{'title': ..., 'command': ..., 'description': ...}]
            error_pattern: Regex pattern to match error messages
            tags: Tags for categorization
        
        Returns:
            Runbook ID
        """
        runbook = {
            'service_id': service_id,
            'title': title,
            'description': description,
            'steps': steps,
            'error_pattern': error_pattern,
            'tags': tags or [],
            'times_used': 0,
            'success_count': 0,
            'created_at': datetime.utcnow()
        }
        
        if self.db:
            # TODO: Insert into database
            runbook_id = "new-runbook-id"
        else:
            runbook_id = f"runbook-{len(self.runbooks_cache)}"
            self.runbooks_cache.append(runbook)
        
        return runbook_id
    
    def _calculate_match_score(
        self,
        runbook: Dict,
        error_message: str,
        error_code: Optional[int],
        tags: List[str]
    ) -> float:
        """
        Calculate how well runbook matches the incident
        
        Scoring:
        - Error pattern match: +0.6
        - Tag match: +0.2 per tag (max 0.4)
        - Service-specific: +0.2
        
        Returns:
            Match score (0.0-1.0)
        """
        score = 0.0
        
        # 1. Error pattern matching (most important)
        if runbook.get('error_pattern'):
            try:
                pattern = re.compile(runbook['error_pattern'], re.IGNORECASE)
                if pattern.search(error_message):
                    score += 0.6
            except re.error:
                # Invalid regex pattern
                pass
        
        # 2. Tag matching
        runbook_tags = set(runbook.get('tags', []))
        incident_tags = set(tags)
        matching_tags = runbook_tags.intersection(incident_tags)
        
        if matching_tags:
            # Up to 0.4 for tag matches
            tag_score = min(len(matching_tags) * 0.2, 0.4)
            score += tag_score
        
        # 3. Service-specific bonus
        if runbook.get('service_id') != 'global':
            score += 0.2
        
        return min(score, 1.0)
    
    def _get_confidence(self, runbook: Dict, match_score: float) -> str:
        """
        Get confidence level for runbook match
        
        Args:
            runbook: Runbook dict
            match_score: Match score (0-1)
        
        Returns:
            Confidence level: 'high', 'medium', or 'low'
        """
        success_rate = runbook.get('success_rate', 0.5)
        
        # Combined score
        combined = (match_score * 0.6) + (success_rate * 0.4)
        
        if combined >= 0.8:
            return "high"
        elif combined >= 0.5:
            return "medium"
        else:
            return "low"
    
    async def _fetch_runbooks(self, service_id: str) -> List[Dict]:
        """
        Fetch runbooks from database
        
        Fetches:
        - Service-specific runbooks
        - Global runbooks (service_id = 'global')
        """
        if not self.db:
            # Return cache for testing
            return self.runbooks_cache
        
        # TODO: Implement database query
        # SELECT * FROM runbooks 
        # WHERE service_id = $1 OR service_id = 'global'
        # ORDER BY success_rate DESC
        
        return []
    
    async def suggest_new_runbook(
        self,
        incident: Dict,
        resolution_steps: str
    ) -> Dict:
        """
        Suggest creating a new runbook based on incident resolution
        
        Args:
            incident: Incident details
            resolution_steps: Steps taken to resolve
        
        Returns:
            Suggested runbook structure
        """
        # Extract common error patterns
        error_pattern = self._extract_error_pattern(incident.get('error_message', ''))
        
        # Suggest tags based on error message
        suggested_tags = self._suggest_tags(incident)
        
        # Parse resolution steps into structured format
        steps = self._parse_resolution_steps(resolution_steps)
        
        return {
            'title': f"Runbook for {incident.get('service_name', 'Unknown')} - {error_pattern}",
            'description': f"Auto-generated from incident {incident.get('id', 'unknown')}",
            'service_id': incident.get('service_id', 'global'),
            'error_pattern': error_pattern,
            'tags': suggested_tags,
            'steps': steps
        }
    
    def _extract_error_pattern(self, error_message: str) -> str:
        """Extract regex pattern from error message"""
        # Remove specific IDs, timestamps, etc.
        pattern = re.sub(r'\d{4}-\d{2}-\d{2}', r'\\d{4}-\\d{2}-\\d{2}', error_message)
        pattern = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', 
                        r'[0-9a-f-]{36}', pattern)
        return pattern[:200]  # Limit length
    
    def _suggest_tags(self, incident: Dict) -> List[str]:
        """Suggest tags based on incident details"""
        tags = []
        error_msg = incident.get('error_message', '').lower()
        
        # Common patterns
        if 'database' in error_msg or 'sql' in error_msg:
            tags.append('database')
        if 'timeout' in error_msg:
            tags.append('timeout')
        if 'connection' in error_msg:
            tags.append('connection')
        if 'memory' in error_msg or 'oom' in error_msg:
            tags.append('memory')
        if 'permission' in error_msg or 'unauthorized' in error_msg:
            tags.append('auth')
        
        # Add status code
        if incident.get('error_code'):
            tags.append(f"status_{incident['error_code']}")
        
        return tags
    
    def _parse_resolution_steps(self, resolution_text: str) -> List[Dict]:
        """Parse resolution text into structured steps"""
        # Split by numbered list or newlines
        lines = resolution_text.split('\n')
        steps = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Extract command if present (anything in backticks or starting with $)
                command_match = re.search(r'`([^`]+)`|\$\s*(.+)', line)
                command = command_match.group(1) or command_match.group(2) if command_match else None
                
                steps.append({
                    'title': line[:100],  # First 100 chars as title
                    'command': command,
                    'description': line
                })
        
        return steps


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_runbook_matcher():
        matcher = RunbookMatcher()
        
        # Create test runbook
        runbook_id = await matcher.create_runbook(
            service_id="auth-api",
            title="Database Connection Pool Exhausted",
            description="Steps to resolve database connection pool issues",
            steps=[
                {
                    'title': "Check current connections",
                    'command': "SELECT count(*) FROM pg_stat_activity;",
                    'description': "Count active database connections"
                },
                {
                    'title': "Kill idle connections",
                    'command': "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';",
                    'description': "Terminate idle connections to free up pool"
                },
                {
                    'title': "Restart application",
                    'command': "kubectl rollout restart deployment auth-api",
                    'description': "Restart the application to reset connection pool"
                }
            ],
            error_pattern=r"connection pool.*exhausted|too many connections",
            tags=['database', 'connection', 'postgres']
        )
        
        print(f"Created runbook: {runbook_id}")
        
        # Test matching
        matches = await matcher.find_matching_runbooks(
            service_id="auth-api",
            error_message="Database connection pool exhausted - max 100 connections reached",
            error_code=500,
            tags=['database']
        )
        
        if matches:
            best = matches[0]
            print(f"\nBest match: {best['title']}")
            print(f"Match score: {best['match_score']:.2f}")
            print(f"Confidence: {best['confidence']}")
    
    asyncio.run(test_runbook_matcher())
