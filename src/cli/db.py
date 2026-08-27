"""Storage operations for Supabase and the local-first CLI mode."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from supabase import Client, create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

from .auth import CONFIG_DIR, load_credentials, load_user_config

LOCAL_DATA_FILE = CONFIG_DIR / 'data.json'


def get_supabase_client() -> Optional[Client]:
    """Get the configured authenticated Supabase client, when available."""
    if not SUPABASE_AVAILABLE:
        return None
    url = os.getenv('SUPABASE_URL')
    anon_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    if not url or not anon_key:
        return None
    client = create_client(url, anon_key)
    creds = load_credentials() or {}
    access_token = creds.get('access_token')
    refresh_token = creds.get('refresh_token')
    if access_token:
        try:
            if refresh_token:
                client.auth.set_session(access_token, refresh_token)
            else:
                client.postgrest.auth(access_token)
        except Exception:  # noqa: BLE001 - client versions expose different auth APIs
            try:
                client.postgrest.auth(access_token)
            except Exception:  # noqa: BLE001 - an anonymous client remains usable
                pass
    return client


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_local_data() -> Dict[str, list]:
    return {'projects': [], 'services': [], 'incidents': [], 'health_checks': []}


def _read_local_data() -> Dict[str, list]:
    if not LOCAL_DATA_FILE.exists():
        return _empty_local_data()
    try:
        data = json.loads(LOCAL_DATA_FILE.read_text())
        return {**_empty_local_data(), **data} if isinstance(data, dict) else _empty_local_data()
    except (json.JSONDecodeError, OSError):
        return _empty_local_data()


def _write_local_data(data: Dict[str, list]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    LOCAL_DATA_FILE.write_text(json.dumps(data, indent=2, default=str))
    if os.name != 'nt':
        LOCAL_DATA_FILE.chmod(0o600)


class SentinelDB:
    """Database facade with a JSON-backed local mode and Supabase mode."""

    def __init__(self):
        self.client = get_supabase_client()
        self.local_mode = load_user_config().get('mode', 'local') != 'supabase'

    @property
    def connected(self) -> bool:
        return self.local_mode or self.client is not None

    def list_projects(self, user_id: str) -> List[Dict]:
        if self.local_mode:
            return [item for item in _read_local_data()['projects'] if item.get('user_id') == user_id]
        if not self.client:
            return []
        result = self.client.table('projects').select('*').eq('user_id', user_id).order('created_at', desc=True).execute()
        return result.data or []

    def create_project(self, user_id: str, name: str, description: str = '') -> Optional[Dict]:
        if self.local_mode:
            data = _read_local_data()
            project = {'id': str(uuid.uuid4()), 'user_id': user_id, 'name': name, 'description': description, 'created_at': _now()}
            data['projects'].append(project)
            _write_local_data(data)
            return project
        if not self.client:
            return None
        result = self.client.table('projects').insert({'user_id': user_id, 'name': name, 'description': description}).execute()
        return result.data[0] if result.data else None

    def delete_project(self, project_id: str) -> bool:
        if self.local_mode:
            data = _read_local_data()
            before = len(data['projects'])
            data['projects'] = [item for item in data['projects'] if item.get('id') != project_id]
            _write_local_data(data)
            return len(data['projects']) < before
        if not self.client:
            return False
        self.client.table('projects').delete().eq('id', project_id).execute()
        return True

    def list_services(self, user_id: str, project_id: Optional[str] = None) -> List[Dict]:
        if self.local_mode:
            return [item for item in _read_local_data()['services'] if item.get('user_id') == user_id and (not project_id or item.get('project_id') == project_id)]
        if not self.client:
            return []
        query = self.client.table('services').select('*').eq('user_id', user_id)
        if project_id:
            query = query.eq('project_id', project_id)
        result = query.order('created_at', desc=True).execute()
        return result.data or []

    def add_service(self, user_id: str, name: str, url: str, project_id: Optional[str] = None, check_interval: int = 30) -> Optional[Dict]:
        if self.local_mode:
            data = _read_local_data()
            service = {'id': str(uuid.uuid4()), 'user_id': user_id, 'name': name, 'url': url, 'check_interval': check_interval, 'last_status': 'unknown', 'avg_response_time': 0, 'created_at': _now()}
            if project_id:
                service['project_id'] = project_id
            data['services'].append(service)
            _write_local_data(data)
            return service
        if not self.client:
            return None
        payload: Dict[str, Any] = {'user_id': user_id, 'name': name, 'url': url, 'check_interval': check_interval}
        if project_id:
            payload['project_id'] = project_id
        result = self.client.table('services').insert(payload).execute()
        return result.data[0] if result.data else None

    def delete_service(self, service_id: str) -> bool:
        if self.local_mode:
            data = _read_local_data()
            before = len(data['services'])
            data['services'] = [item for item in data['services'] if item.get('id') != service_id]
            _write_local_data(data)
            return len(data['services']) < before
        if not self.client:
            return False
        self.client.table('services').delete().eq('id', service_id).execute()
        return True

    def update_service_status(self, service_id: str, status: str, response_time: int) -> bool:
        if self.local_mode:
            data = _read_local_data()
            for item in data['services']:
                if item.get('id') == service_id:
                    item.update({'last_status': status, 'avg_response_time': response_time, 'last_checked_at': _now()})
                    _write_local_data(data)
                    return True
            return False
        if not self.client:
            return False
        self.client.table('services').update({'last_status': status, 'avg_response_time': response_time, 'last_checked_at': _now()}).eq('id', service_id).execute()
        return True

    def list_incidents(self, user_id: str, limit: int = 10, severity: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
        if self.local_mode:
            items = [item for item in _read_local_data()['incidents'] if item.get('user_id') == user_id and (not severity or item.get('severity') == severity) and (not status or item.get('status') == status)]
            return items[:limit]
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
        if self.local_mode:
            data = _read_local_data()
            incident = {'id': str(uuid.uuid4()), 'user_id': user_id, 'service_id': service_id, 'severity': severity, 'title': title, 'description': description, 'status': 'open', 'created_at': _now()}
            data['incidents'].append(incident)
            _write_local_data(data)
            return incident
        if not self.client:
            return None
        result = self.client.table('incidents').insert({'user_id': user_id, 'service_id': service_id, 'severity': severity, 'title': title, 'description': description, 'status': 'open'}).execute()
        return result.data[0] if result.data else None

    def get_incident(self, incident_id: str) -> Optional[Dict]:
        if self.local_mode:
            return next((item for item in _read_local_data()['incidents'] if item.get('id') == incident_id), None)
        if not self.client:
            return None
        result = self.client.table('incidents').select('*, services(name, url)').eq('id', incident_id).single().execute()
        return result.data

    def update_incident(self, incident_id: str, updates: Dict) -> bool:
        if self.local_mode:
            data = _read_local_data()
            for item in data['incidents']:
                if item.get('id') == incident_id:
                    item.update(updates)
                    _write_local_data(data)
                    return True
            return False
        if not self.client:
            return False
        self.client.table('incidents').update(updates).eq('id', incident_id).execute()
        return True

    def log_health_check(self, service_id: str, status_code: int, response_time_ms: int, is_healthy: bool, error: str = '') -> bool:
        if self.local_mode:
            data = _read_local_data()
            data['health_checks'].append({'id': str(uuid.uuid4()), 'service_id': service_id, 'status_code': status_code, 'response_time_ms': response_time_ms, 'is_healthy': is_healthy, 'error_message': error, 'checked_at': _now()})
            _write_local_data(data)
            return True
        if not self.client:
            return False
        self.client.table('health_checks').insert({'service_id': service_id, 'status_code': status_code, 'response_time_ms': response_time_ms, 'is_healthy': is_healthy, 'error_message': error}).execute()
        return True


_db: Optional[SentinelDB] = None


def get_db() -> SentinelDB:
    """Return the process-local storage facade."""
    global _db
    if _db is None:
        _db = SentinelDB()
    return _db
