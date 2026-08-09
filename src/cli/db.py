"""
DevOps Sentinel CLI - Supabase Client Module
=============================================

Handles all Supabase database operations for the CLI.
"""

import os
import json
from typing import Optional, Dict, List
from pathlib import Path

# Try to import supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

from .auth import load_credentials


def get_supabase_client() -> Optional[Client]:
    """
    Get authenticated Supabase client.
    Uses stored access token from login.
    """
    if not SUPABASE_AVAILABLE:
        return None
    
    url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    if not url or not anon_key:
        return None
    
    client = create_client(url, anon_key)
    
    # Set auth token if logged in
    creds = load_credentials() or {}
    access_token = creds.get('access_token')
    refresh_token = creds.get('refresh_token')
    if access_token:
        try:
            if refresh_token:
                client.auth.set_session(access_token, refresh_token)
            else:
                client.postgrest.auth(access_token)
        except Exception:
            try:
                client.postgrest.auth(access_token)
            except Exception:
                pass
    
    return client


class SentinelDB:
    """Database operations for DevOps Sentinel CLI."""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    @property
    def connected(self) -> bool:
        return self.client is not None
    
    # Projects
    def list_projects(self, user_id: str) -> List[Dict]:
        """List all projects for a user."""
        if not self.client:
            return []
        
        result = self.client.table('projects').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return result.data or []
    
    def create_project(self, user_id: str, name: str, description: str = '') -> Optional[Dict]:
        """Create a new project."""
        if not self.client:
            return None
        
        result = self.client.table('projects').insert({
            'user_id': user_id,
            'name': name,
            'description': description
        }).execute()
        
        return result.data[0] if result.data else None
    
    def delete_project(self, project_id: str) -> bool:
        """Delete a project."""
        if not self.client:
            return False
        
        self.client.table('projects').delete().eq('id', project_id).execute()
        return True
    
    # Services
    def list_services(self, user_id: str, project_id: Optional[str] = None) -> List[Dict]:
        """List services, optionally filtered by project."""
        if not self.client:
            return []
        
        query = self.client.table('services').select('*').eq('user_id', user_id)
        if project_id:
            query = query.eq('project_id', project_id)
        
        result = query.order('created_at', desc=True).execute()
        return result.data or []
    
    def add_service(self, user_id: str, name: str, url: str, project_id: Optional[str] = None, check_interval: int = 30) -> Optional[Dict]:
        """Add a new service to monitor."""
        if not self.client:
            return None
        
        data = {
            'user_id': user_id,
            'name': name,
            'url': url,
            'check_interval': check_interval
        }
        if project_id:
            data['project_id'] = project_id
        
        result = self.client.table('services').insert(data).execute()
        return result.data[0] if result.data else None
    
    def delete_service(self, service_id: str) -> bool:
        """Delete a service."""
        if not self.client:
            return False
        
        self.client.table('services').delete().eq('id', service_id).execute()
        return True
    
    def update_service_status(self, service_id: str, status: str, response_time: int) -> bool:
        """Update service health status."""
        if not self.client:
            return False
        
        from datetime import datetime
        
        self.client.table('services').update({
            'last_status': status,
            'avg_response_time': response_time,
            'last_checked_at': datetime.utcnow().isoformat()
        }).eq('id', service_id).execute()
        return True
    
    # Incidents
    def list_incidents(self, user_id: str, limit: int = 10, severity: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        """List incidents with optional filters."""
        if not self.client:
            return []
        
        query = self.client.table('incidents').select('*, services(name, url)').eq('user_id', user_id)
        
        if severity:
            query = query.eq('severity', severity)
        if status:
            query = query.eq('status', status)
        
        result = query.order('created_at', desc=True).limit(limit).execute()
        return result.data or []
    
    def create_incident(self, user_id: str, service_id: str, severity: str, title: str, description: str = '') -> Optional[Dict]:
        """Create a new incident."""
        if not self.client:
            return None
        
        result = self.client.table('incidents').insert({
            'user_id': user_id,
            'service_id': service_id,
            'severity': severity,
            'title': title,
            'description': description,
            'status': 'open'
        }).execute()
        
        return result.data[0] if result.data else None
    
    def get_incident(self, incident_id: str) -> Optional[Dict]:
        """Get a single incident by ID."""
        if not self.client:
            return None
        
        result = self.client.table('incidents').select('*, services(name, url)').eq('id', incident_id).single().execute()
        return result.data
    
    def update_incident(self, incident_id: str, updates: Dict) -> bool:
        """Update an incident."""
        if not self.client:
            return False
        
        self.client.table('incidents').update(updates).eq('id', incident_id).execute()
        return True
    
    def get_incident_events(self, incident_id: str) -> List[Dict]:
        """Get timeline events for an incident."""
        if not self.client:
            return []

        try:
            result = self.client.table('incident_events').select('*').eq('incident_id', incident_id).order('timestamp').execute()
            return result.data or []
        except Exception:
            return []

    # Health checks
    def log_health_check(self, service_id: str, status_code: int, response_time_ms: int, is_healthy: bool, error: str = '') -> bool:
        """Log a health check result."""
        if not self.client:
            return False
        
        self.client.table('health_checks').insert({
            'service_id': service_id,
            'status_code': status_code,
            'response_time_ms': response_time_ms,
            'is_healthy': is_healthy,
            'error_message': error
        }).execute()
        return True


# Singleton instance
_db: Optional[SentinelDB] = None

def get_db() -> SentinelDB:
    """Get database instance."""
    global _db
    if _db is None:
        _db = SentinelDB()
    return _db
