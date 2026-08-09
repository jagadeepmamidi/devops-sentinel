"""
Team Assignment System - Collaborative Incident Ownership
==========================================================

Assign incidents to team members and track ownership
"""

from datetime import datetime
from typing import Dict, List, Optional
import asyncio


class TeamAssignmentSystem:
    """
    Manage incident assignments and team collaboration
    
    Features:
    - Auto-assign based on on-call schedule
    - Manual assignment override
    - Load balancing across team
    - Assignment history tracking
    - Workload metrics
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    async def assign_incident(
        self,
        incident_id: str,
        assigned_to: Optional[str] = None,
        assigned_by: Optional[str] = None,
        reason: str = 'auto'
    ) -> Dict:
        """
        Assign incident to team member
        
        Args:
            incident_id: Incident ID
            assigned_to: User ID to assign to (if None, auto-assign)
            assigned_by: User who made the assignment
            reason: 'auto', 'manual', 'escalation'
        
        Returns:
            Assignment record
        """
        # Get incident details
        incident = await self.supabase.table('incidents').select(
            'team_id, severity, service_id'
        ).eq('id', incident_id).execute()
        
        if not incident.data:
            raise ValueError(f'Incident {incident_id} not found')
        
        team_id = incident.data[0]['team_id']
        severity = incident.data[0]['severity']
        
        # Auto-assign if no assignee specified
        if not assigned_to:
            assigned_to = await self._auto_assign(team_id, severity)
        
        # Create assignment
        assignment = {
            'incident_id': incident_id,
            'assigned_to': assigned_to,
            'assigned_by': assigned_by or 'system',
            'assigned_at': datetime.utcnow().isoformat(),
            'reason': reason,
            'status': 'assigned'
        }
        
        await self.supabase.table('incident_assignments').insert(
            assignment
        ).execute()
        
        # Update incident
        await self.supabase.table('incidents').update({
            'assigned_to': assigned_to,
            'status': 'assigned'
        }).eq('id', incident_id).execute()
        
        # Log to timeline
        await self._log_assignment(incident_id, assignment)
        
        return assignment
    
    async def _auto_assign(self, team_id: str, severity: str) -> str:
        """
        Auto-assign based on on-call schedule or load balancing
        
        Strategy:
        - P0/P1: Assign to current on-call
        - P2/P3: Load balance across team
        """
        if severity in ['P0', 'P1']:
            # Get on-call person
            on_call = await self.supabase.table('on_call_schedules').select(
                'current_user_id'
            ).eq('team_id', team_id).eq('is_active', True).execute()
            
            if on_call.data:
                return on_call.data[0]['current_user_id']
        
        # Load balance: assign to person with least active incidents
        workload = await self.get_team_workload(team_id)
        
        if workload:
            # Sort by active incidents (ascending)
            sorted_members = sorted(workload, key=lambda x: x['active_incidents'])
            return sorted_members[0]['user_id']
        
        # Fallback: assign to team owner
        team = await self.supabase.table('teams').select(
            'owner_id'
        ).eq('id', team_id).execute()
        
        return team.data[0]['owner_id'] if team.data else None
    
    async def reassign_incident(
        self,
        incident_id: str,
        new_assignee: str,
        reassigned_by: str,
        reason: str = 'manual'
    ) -> Dict:
        """
        Reassign incident to different team member
        
        Args:
            incident_id: Incident ID
            new_assignee: New user ID
            reassigned_by: User making the change
            reason: Reason for reassignment
        """
        # Get current assignment
        current = await self.supabase.table('incident_assignments').select(
            '*'
        ).eq('incident_id', incident_id).eq('status', 'assigned').execute()
        
        if current.data:
            # Mark old assignment as superseded
            await self.supabase.table('incident_assignments').update({
                'status': 'reassigned',
                'reassigned_at': datetime.utcnow().isoformat()
            }).eq('id', current.data[0]['id']).execute()
        
        # Create new assignment
        return await self.assign_incident(
            incident_id,
            assigned_to=new_assignee,
            assigned_by=reassigned_by,
            reason=reason
        )
    
    async def unassign_incident(
        self,
        incident_id: str,
        unassigned_by: str
    ) -> Dict:
        """
        Remove assignment from incident
        
        Args:
            incident_id: Incident ID
            unassigned_by: User removing assignment
        """
        # Mark assignment as unassigned
        await self.supabase.table('incident_assignments').update({
            'status': 'unassigned',
            'unassigned_at': datetime.utcnow().isoformat(),
            'unassigned_by': unassigned_by
        }).eq('incident_id', incident_id).eq('status', 'assigned').execute()
        
        # Update incident
        await self.supabase.table('incidents').update({
            'assigned_to': None,
            'status': 'open'
        }).eq('id', incident_id).execute()
        
        return {'incident_id': incident_id, 'status': 'unassigned'}
    
    async def get_team_workload(self, team_id: str) -> List[Dict]:
        """
        Get current workload for all team members
        
        Returns:
            List of team members with workload metrics
        """
        # Get team members
        members = await self.supabase.table('team_members').select(
            'user_id, name, role'
        ).eq('team_id', team_id).execute()
        
        if not members.data:
            return []
        
        workload = []
        for member in members.data:
            # Count active incidents
            active = await self.supabase.table('incidents').select(
                'id', count='exact'
            ).eq('assigned_to', member['user_id']).eq(
                'status', 'assigned'
            ).execute()
            
            # Count resolved this week
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            resolved = await self.supabase.table('incidents').select(
                'id', count='exact'
            ).eq('assigned_to', member['user_id']).eq(
                'status', 'resolved'
            ).gte('resolved_at', week_ago).execute()
            
            workload.append({
                'user_id': member['user_id'],
                'name': member['name'],
                'role': member['role'],
                'active_incidents': active.count or 0,
                'resolved_this_week': resolved.count or 0,
                'load_score': (active.count or 0) * 2  # Weight active incidents higher
            })
        
        return workload
    
    async def get_user_assignments(
        self,
        user_id: str,
        status: str = 'assigned',
        limit: int = 20
    ) -> List[Dict]:
        """
        Get all assignments for a user
        
        Args:
            user_id: User ID
            status: 'assigned', 'all'
            limit: Max results
        
        Returns:
            List of assigned incidents
        """
        query = self.supabase.table('incidents').select(
            'id, severity, service_id, service_name, created_at, status'
        ).eq('assigned_to', user_id)
        
        if status != 'all':
            query = query.eq('status', status)
        
        result = await query.order('created_at', desc=True).limit(limit).execute()
        
        return result.data or []
    
    async def get_assignment_history(
        self,
        incident_id: str
    ) -> List[Dict]:
        """
        Get full assignment history for incident
        
        Returns:
            List of all assignments in chronological order
        """
        history = await self.supabase.table('incident_assignments').select(
            '*'
        ).eq('incident_id', incident_id).order('assigned_at').execute()
        
        return history.data or []
    
    async def _log_assignment(
        self,
        incident_id: str,
        assignment: Dict
    ):
        """Log assignment to incident timeline"""
        await self.supabase.table('incident_timeline').insert({
            'incident_id': incident_id,
            'event_type': 'assigned',
            'details': {
                'assigned_to': assignment['assigned_to'],
                'assigned_by': assignment['assigned_by'],
                'reason': assignment['reason']
            },
            'created_at': datetime.utcnow().isoformat()
        }).execute()
    
    async def get_team_stats(self, team_id: str) -> Dict:
        """
        Get team assignment statistics
        
        Returns:
            Team-level metrics
        """
        # Get all team incidents
        incidents = await self.supabase.table('incidents').select(
            'id, severity, assigned_to, status, created_at, resolved_at'
        ).eq('team_id', team_id).execute()
        
        total = len(incidents.data)
        assigned = sum(1 for i in incidents.data if i.get('assigned_to'))
        unassigned = total - assigned
        
        # Average time to assignment
        assignment_times = []
        for incident in incidents.data:
            if incident.get('assigned_to'):
                assignments = await self.get_assignment_history(incident['id'])
                if assignments:
                    created = datetime.fromisoformat(incident['created_at'])
                    first_assigned = datetime.fromisoformat(assignments[0]['assigned_at'])
                    assignment_times.append((first_assigned - created).total_seconds() / 60)
        
        avg_assignment_time = sum(assignment_times) / len(assignment_times) if assignment_times else 0
        
        return {
            'total_incidents': total,
            'assigned': assigned,
            'unassigned': unassigned,
            'avg_time_to_assignment_minutes': round(avg_assignment_time, 2),
            'assignment_rate': round((assigned / total * 100), 2) if total > 0 else 0
        }


# Helper to avoid circular import
from datetime import timedelta


# Example usage
if __name__ == "__main__":
    async def test_assignment():
        # Mock Supabase
        class MockSupabase:
            def table(self, name):
                return self
            
            def select(self, *args, **kwargs):
                return self
            
            def insert(self, *args):
                return self
            
            def update(self, *args):
                return self
            
            def eq(self, *args):
                return self
            
            def gte(self, *args):
                return self
            
            def order(self, *args, **kwargs):
                return self
            
            def limit(self, *args):
                return self
            
            async def execute(self):
                class Result:
                    data = [{'team_id': 'team-1', 'severity': 'P1', 'service_id': 'svc-1'}]
                    count = 2
                return Result()
        
        system = TeamAssignmentSystem(MockSupabase())
        
        # Assign incident
        assignment = await system.assign_incident('inc-123')
        print(f"Assignment: {assignment}")
    
    asyncio.run(test_assignment())
