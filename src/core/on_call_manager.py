"""
On-Call Manager - Rotation & Escalation
========================================

Manages on-call schedules, rotations, and escalation policies
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import asyncio


class OnCallManager:
    """
    Manage on-call schedules and escalations
    
    Features:
    - Round-robin rotation
    - Time-based schedules (weekly, daily)
    - Multi-layer escalation
    - Timezone-aware scheduling
    - Override assignments
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    async def get_current_on_call(
        self,
        team_id: str,
        service_id: Optional[str] = None
    ) -> Dict:
        """
        Get who is currently on-call
        
        Args:
            team_id: Team identifier
            service_id: Optional service-specific on-call
        
        Returns:
            Current on-call person details
        """
        now = datetime.utcnow()
        
        # Check for overrides first
        override = await self._check_override(team_id, service_id, now)
        if override:
            return override
        
        # Get active schedule
        schedule = await self._get_active_schedule(team_id, service_id, now)
        
        if not schedule:
            return {
                'on_call': None,
                'error': 'No active on-call schedule found'
            }
        
        # Calculate who's on-call based on rotation
        on_call_user = await self._calculate_current_rotation(schedule, now)
        
        return {
            'user_id': on_call_user['id'],
            'name': on_call_user['name'],
            'email': on_call_user['email'],
            'phone': on_call_user.get('phone'),
            'schedule_id': schedule['id'],
            'schedule_name': schedule['name'],
            'shift_start': schedule['current_shift_start'],
            'shift_end': schedule['current_shift_end']
        }
    
    async def _check_override(
        self,
        team_id: str,
        service_id: Optional[str],
        timestamp: datetime
    ) -> Optional[Dict]:
        """Check if there's an on-call override for this time"""
        query = self.supabase.table('on_call_overrides').select('*').eq(
            'team_id', team_id
        ).lte('start_time', timestamp.isoformat()).gte(
            'end_time', timestamp.isoformat()
        )
        
        if service_id:
            query = query.eq('service_id', service_id)
        
        result = await query.execute()
        
        if result.data:
            override = result.data[0]
            return {
                'user_id': override['user_id'],
                'name': override['user_name'],
                'email': override['user_email'],
                'is_override': True,
                'reason': override.get('reason', 'Manual override')
            }
        
        return None
    
    async def _get_active_schedule(
        self,
        team_id: str,
        service_id: Optional[str],
        timestamp: datetime
    ) -> Optional[Dict]:
        """Get the active on-call schedule"""
        query = self.supabase.table('on_call_schedules').select(
            '*'
        ).eq('team_id', team_id).eq('is_active', True)
        
        if service_id:
            query = query.eq('service_id', service_id)
        
        result = await query.execute()
        
        if result.data:
            return result.data[0]
        
        return None
    
    async def _calculate_current_rotation(
        self,
        schedule: Dict,
        timestamp: datetime
    ) -> Dict:
        """
        Calculate who's on-call based on rotation type
        
        Supports:
        - weekly: Each person gets a week
        - daily: Each person gets a day
        - custom: Based on shift_duration_hours
        """
        rotation_type = schedule.get('rotation_type', 'weekly')
        participants = schedule['participants']  # List of user IDs
        start_date = datetime.fromisoformat(schedule['start_date'])
        
        if rotation_type == 'weekly':
            shift_duration = timedelta(weeks=1)
        elif rotation_type == 'daily':
            shift_duration = timedelta(days=1)
        else:
            # Custom duration in hours
            hours = schedule.get('shift_duration_hours', 168)  # Default 1 week
            shift_duration = timedelta(hours=hours)
        
        # Calculate elapsed time since schedule start
        elapsed = timestamp - start_date
        
        # Calculate which shift we're in
        shift_number = int(elapsed / shift_duration)
        
        # Round-robin: cycle through participants
        current_index = shift_number % len(participants)
        current_user_id = participants[current_index]
        
        # Get user details
        user_result = await self.supabase.table('users').select(
            'id, name, email, phone'
        ).eq('id', current_user_id).execute()
        
        if user_result.data:
            user = user_result.data[0]
            
            # Calculate shift boundaries
            shift_start = start_date + (shift_duration * shift_number)
            shift_end = shift_start + shift_duration
            
            schedule['current_shift_start'] = shift_start.isoformat()
            schedule['current_shift_end'] = shift_end.isoformat()
            
            return user
        
        # Fallback to first participant
        return await self.supabase.table('users').select(
            'id, name, email, phone'
        ).eq('id', participants[0]).execute().data[0]
    
    async def create_schedule(
        self,
        team_id: str,
        name: str,
        participants: List[str],
        rotation_type: str = 'weekly',
        start_date: Optional[datetime] = None,
        service_id: Optional[str] = None
    ) -> Dict:
        """
        Create a new on-call schedule
        
        Args:
            team_id: Team identifier
            name: Schedule name (e.g., "Primary On-Call")
            participants: List of user IDs in rotation order
            rotation_type: 'weekly', 'daily', or 'custom'
            start_date: When schedule starts (default: now)
            service_id: Optional service-specific schedule
        
        Returns:
            Created schedule
        """
        if not start_date:
            start_date = datetime.utcnow()
        
        schedule = {
            'team_id': team_id,
            'name': name,
            'participants': participants,
            'rotation_type': rotation_type,
            'start_date': start_date.isoformat(),
            'is_active': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        if service_id:
            schedule['service_id'] = service_id
        
        result = await self.supabase.table('on_call_schedules').insert(
            schedule
        ).execute()
        
        return result.data[0]
    
    async def add_override(
        self,
        team_id: str,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        reason: str = 'Manual override',
        service_id: Optional[str] = None
    ) -> Dict:
        """
        Override on-call assignment for a specific time period
        
        Use cases:
        - Vacation coverage
        - Emergency reassignment
        - Special events
        """
        # Get user details
        user = await self.supabase.table('users').select(
            'name, email'
        ).eq('id', user_id).execute()
        
        if not user.data:
            raise ValueError(f'User {user_id} not found')
        
        override = {
            'team_id': team_id,
            'user_id': user_id,
            'user_name': user.data[0]['name'],
            'user_email': user.data[0]['email'],
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'reason': reason,
            'created_at': datetime.utcnow().isoformat()
        }
        
        if service_id:
            override['service_id'] = service_id
        
        result = await self.supabase.table('on_call_overrides').insert(
            override
        ).execute()
        
        return result.data[0]
    
    async def get_escalation_chain(
        self,
        team_id: str,
        severity: str
    ) -> List[Dict]:
        """
        Get escalation chain for a given severity
        
        Returns list of escalation levels:
        [
            {'level': 1, 'user_id': '...', 'wait_minutes': 5},
            {'level': 2, 'user_id': '...', 'wait_minutes': 10},
            ...
        ]
        """
        result = await self.supabase.table('escalation_policies').select(
            '*'
        ).eq('team_id', team_id).eq('severity', severity).order(
            'level'
        ).execute()
        
        if result.data:
            return result.data
        
        # Default fallback: escalate to team owner after 15 minutes
        team_result = await self.supabase.table('teams').select(
            'owner_id'
        ).eq('id', team_id).execute()
        
        if team_result.data:
            return [{
                'level': 1,
                'user_id': team_result.data[0]['owner_id'],
                'wait_minutes': 15
            }]
        
        return []
    
    async def trigger_escalation(
        self,
        incident_id: str,
        current_level: int = 0
    ) -> Dict:
        """
        Trigger next level of escalation
        
        Args:
            incident_id: Incident to escalate
            current_level: Current escalation level (0 = not escalated yet)
        
        Returns:
            Next on-call person to notify
        """
        # Get incident details
        incident = await self.supabase.table('incidents').select(
            'team_id, severity'
        ).eq('id', incident_id).execute()
        
        if not incident.data:
            raise ValueError(f'Incident {incident_id} not found')
        
        team_id = incident.data[0]['team_id']
        severity = incident.data[0]['severity']
        
        # Get escalation chain
        chain = await self.get_escalation_chain(team_id, severity)
        
        # Find next level
        next_level = current_level + 1
        next_escalation = next((e for e in chain if e['level'] == next_level), None)
        
        if not next_escalation:
            # No more escalation levels - notify all team
            return {
                'escalated_to': 'team_broadcast',
                'message': 'All escalation levels exhausted. Notifying entire team.'
            }
        
        # Log escalation
        await self.supabase.table('incident_timeline').insert({
            'incident_id': incident_id,
            'event_type': 'escalated',
            'details': {
                'level': next_level,
                'escalated_to': next_escalation['user_id']
            },
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        return {
            'escalated_to': next_escalation['user_id'],
            'level': next_level,
            'wait_minutes': next_escalation.get('wait_minutes', 15)
        }


# Example usage
if __name__ == "__main__":
    async def test_on_call():
        # Mock Supabase client
        class MockSupabase:
            def table(self, name):
                return self
            
            def select(self, *args):
                return self
            
            def eq(self, *args):
                return self
            
            def lte(self, *args):
                return self
            
            def gte(self, *args):
                return self
            
            async def execute(self):
                class Result:
                    data = [{
                        'id': 'user-1',
                        'name': 'Alice',
                        'email': 'alice@example.com',
                        'phone': '+1234567890',
                        'participants': ['user-1', 'user-2', 'user-3'],
                        'rotation_type': 'weekly',
                        'start_date': '2026-01-01T00:00:00'
                    }]
                return Result()
        
        manager = OnCallManager(MockSupabase())
        
        # Get current on-call
        on_call = await manager.get_current_on_call('team-1')
        print(f"Currently on-call: {on_call}")
    
    asyncio.run(test_on_call())
