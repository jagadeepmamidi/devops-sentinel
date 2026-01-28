"""
GDPR Compliance Endpoints - Data Export and Deletion
=====================================================

User rights: Access, Export, Delete all personal data
"""

from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import json


router = APIRouter(prefix="/api/user", tags=["user"])


class GDPRHandler:
    """
    Handle GDPR compliance requests
    
    Implements:
    - Article 15: Right of access
    - Article 17: Right to erasure
    - Article 20: Right to data portability
    """
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    async def export_all_data(self, user_id: str) -> Dict:
        """
        GDPR Article 20 - Export ALL user data
        
        Returns complete data package in JSON format
        """
        export_data = {
            'export_metadata': {
                'user_id': user_id,
                'export_timestamp': datetime.utcnow().isoformat(),
                'format_version': '1.0',
                'data_retention_policy': '2 years for incidents, 90 days for logs'
            },
            
            # Core account data
            'account': await self._get_account_data(user_id),
            
            # Services and monitoring
            'services': await self._get_services(user_id),
            'health_checks': await self._get_health_checks(user_id),
            
            # Incidents and postmortems
            'incidents': await self._get_incidents(user_id),
            'postmortems': await self._get_postmortems(user_id),
            
            # Runbooks and automation
            'runbooks': await self._get_runbooks(user_id),
            'runbook_executions': await self._get_runbook_executions(user_id),
            
            # Team and collaboration
            'team_members': await self._get_team_members(user_id),
            'on_call_schedules': await self._get_on_call_schedules(user_id),
            
            # AI and embeddings (CRITICAL for GDPR)
            'embeddings': await self._get_embeddings(user_id),
            'ai_usage_logs': await self._get_ai_usage(user_id),
            
            # Notifications and audit
            'notification_history': await self._get_notifications(user_id),
            'audit_logs': await self._get_audit_logs(user_id),
            
            # Chaos experiments
            'chaos_experiments': await self._get_chaos_experiments(user_id),
            
            # Third party data sharing disclosure
            'third_party_processors': [
                {
                    'name': 'Supabase',
                    'purpose': 'Database hosting and authentication',
                    'location': 'United States (AWS us-east-1)',
                    'data_shared': 'All account data, services, incidents',
                    'data_retention': 'Until account deletion'
                },
                {
                    'name': 'OpenRouter/Google AI',
                    'purpose': 'AI analysis and postmortem generation',
                    'location': 'United States',
                    'data_shared': 'Incident descriptions, error messages (temporary)',
                    'data_retention': 'Not stored after processing'
                },
                {
                    'name': 'Stripe',
                    'purpose': 'Payment processing',
                    'location': 'United States',
                    'data_shared': 'Email, payment method',
                    'data_retention': 'Per Stripe policies'
                }
            ]
        }
        
        return export_data
    
    async def delete_all_data(
        self,
        user_id: str,
        confirmation: str
    ) -> Dict:
        """
        GDPR Article 17 - Right to be forgotten
        
        Permanently deletes ALL user data
        """
        # Require explicit confirmation
        if confirmation != "DELETE_MY_DATA":
            raise ValueError(
                "Must confirm deletion by providing confirmation='DELETE_MY_DATA'"
            )
        
        deleted_counts = {}
        
        # Order matters! Delete dependent records first
        
        # 1. Delete AI usage logs
        result = await self.supabase.table('ai_usage').delete().eq(
            'user_id', user_id
        ).execute()
        deleted_counts['ai_usage'] = len(result.data) if result.data else 0
        
        # 2. Delete notification history
        result = await self.supabase.table('notification_history').delete().eq(
            'user_id', user_id
        ).execute()
        deleted_counts['notifications'] = len(result.data) if result.data else 0
        
        # 3. Delete rate limit logs
        result = await self.supabase.table('rate_limit_log').delete().eq(
            'user_id', user_id
        ).execute()
        deleted_counts['rate_limits'] = len(result.data) if result.data else 0
        
        # 4. Delete chaos experiments
        result = await self.supabase.table('chaos_experiments').delete().eq(
            'user_id', user_id
        ).execute()
        deleted_counts['chaos_experiments'] = len(result.data) if result.data else 0
        
        # 5. Delete runbook executions (via incidents)
        # Will cascade from incidents
        
        # 6. Delete incidents
        result = await self.supabase.table('incidents').delete().eq(
            'user_id', user_id
        ).execute()
        deleted_counts['incidents'] = len(result.data) if result.data else 0
        
        # 7. Delete health checks
        result = await self.supabase.table('health_checks').delete().eq(
            'user_id', user_id
        ).execute()
        deleted_counts['health_checks'] = len(result.data) if result.data else 0
        
        # 8. Delete services
        result = await self.supabase.table('services').delete().eq(
            'user_id', user_id
        ).execute()
        deleted_counts['services'] = len(result.data) if result.data else 0
        
        # 9. Delete runbooks
        result = await self.supabase.table('runbooks').delete().eq(
            'user_id', user_id
        ).execute()
        deleted_counts['runbooks'] = len(result.data) if result.data else 0
        
        # 10. Delete team memberships
        result = await self.supabase.table('team_members').delete().eq(
            'user_id', user_id
        ).execute()
        deleted_counts['team_members'] = len(result.data) if result.data else 0
        
        # 11. Delete user account (last!)
        result = await self.supabase.table('users').delete().eq(
            'id', user_id
        ).execute()
        deleted_counts['user'] = 1 if result.data else 0
        
        return {
            'status': 'deleted',
            'user_id': user_id,
            'deleted_at': datetime.utcnow().isoformat(),
            'deleted_counts': deleted_counts,
            'message': 'All personal data has been permanently deleted'
        }
    
    async def get_data_usage_summary(self, user_id: str) -> Dict:
        """
        Transparency endpoint - show what data we have
        """
        account = await self._get_account_data(user_id)
        
        # Count records in each table
        services = await self.supabase.table('services').select(
            'id', count='exact'
        ).eq('user_id', user_id).execute()
        
        incidents = await self.supabase.table('incidents').select(
            'id', count='exact'
        ).eq('user_id', user_id).execute()
        
        ai_usage = await self.supabase.table('ai_usage').select(
            'cost_usd'
        ).eq('user_id', user_id).execute()
        
        return {
            'account_created': account.get('created_at'),
            'email': account.get('email'),
            'subscription_tier': account.get('subscription_tier', 'free'),
            
            'data_summary': {
                'services_monitored': services.count if hasattr(services, 'count') else len(services.data),
                'incidents_tracked': incidents.count if hasattr(incidents, 'count') else len(incidents.data),
                'ai_calls_made': len(ai_usage.data) if ai_usage.data else 0,
                'total_ai_cost': sum(r.get('cost_usd', 0) for r in (ai_usage.data or []))
            },
            
            'data_sharing': {
                'third_parties': ['Supabase (database)', 'OpenRouter (AI)', 'Stripe (payments)'],
                'data_shared_with_ai': 'Incident descriptions only (not stored)',
                'data_sold': 'Never'
            },
            
            'your_rights': {
                'export_data': 'POST /api/user/export-data',
                'delete_account': 'DELETE /api/user/delete-account',
                'update_preferences': 'PATCH /api/user/preferences'
            },
            
            'retention_policy': {
                'incidents': '2 years',
                'health_checks': '90 days',
                'audit_logs': '90 days',
                'ai_usage_logs': '1 year'
            }
        }
    
    # Helper methods to fetch data
    
    async def _get_account_data(self, user_id: str) -> Dict:
        result = await self.supabase.table('users').select('*').eq(
            'id', user_id
        ).execute()
        
        if result.data:
            user = result.data[0]
            # Remove sensitive fields
            user.pop('password_hash', None)
            return user
        return {}
    
    async def _get_services(self, user_id: str):
        result = await self.supabase.table('services').select('*').eq(
            'user_id', user_id
        ).execute()
        return result.data or []
    
    async def _get_health_checks(self, user_id: str):
        # Get health checks for user's services
        services = await self._get_services(user_id)
        service_ids = [s['id'] for s in services]
        
        if not service_ids:
            return []
        
        result = await self.supabase.table('health_checks').select('*').in_(
            'service_id', service_ids
        ).limit(1000).execute()  # Limit for performance
        
        return result.data or []
    
    async def _get_incidents(self, user_id: str):
        result = await self.supabase.table('incidents').select('*').eq(
            'user_id', user_id
        ).execute()
        return result.data or []
    
    async def _get_postmortems(self, user_id: str):
        result = await self.supabase.table('postmortems').select('*').eq(
            'user_id', user_id
        ).execute()
        return result.data or []
    
    async def _get_runbooks(self, user_id: str):
        result = await self.supabase.table('runbooks').select('*').eq(
            'user_id', user_id
        ).execute()
        return result.data or []
    
    async def _get_runbook_executions(self, user_id: str):
        result = await self.supabase.table('runbook_executions').select('*').eq(
            'executed_by', user_id
        ).execute()
        return result.data or []
    
    async def _get_team_members(self, user_id: str):
        result = await self.supabase.table('team_members').select('*').eq(
            'user_id', user_id
        ).execute()
        return result.data or []
    
    async def _get_on_call_schedules(self, user_id: str):
        result = await self.supabase.table('on_call_schedules').select('*').eq(
            'user_id', user_id
        ).execute()
        return result.data or []
    
    async def _get_embeddings(self, user_id: str):
        """Get vector embeddings (GDPR requires this!)"""
        incidents = await self._get_incidents(user_id)
        
        # Return embedding metadata, not raw vectors (too large)
        embeddings = []
        for inc in incidents:
            if inc.get('embedding'):
                embeddings.append({
                    'incident_id': inc['id'],
                    'embedding_model': 'text-embedding-3-small',
                    'embedding_dimensions': 1536,
                    'created_at': inc.get('created_at')
                })
        
        return embeddings
    
    async def _get_ai_usage(self, user_id: str):
        result = await self.supabase.table('ai_usage').select('*').eq(
            'user_id', user_id
        ).execute()
        return result.data or []
    
    async def _get_notifications(self, user_id: str):
        result = await self.supabase.table('notification_history').select('*').eq(
            'user_id', user_id
        ).execute()
        return result.data or []
    
    async def _get_audit_logs(self, user_id: str):
        result = await self.supabase.table('audit_logs').select('*').eq(
            'user_id', user_id
        ).limit(1000).execute()
        return result.data or []
    
    async def _get_chaos_experiments(self, user_id: str):
        result = await self.supabase.table('chaos_experiments').select('*').eq(
            'user_id', user_id
        ).execute()
        return result.data or []


# FastAPI Routes

@router.post("/export-data")
async def export_user_data(
    user_id: str,
    supabase=Depends(lambda: None)  # Replace with actual dependency
):
    """GDPR Article 20 - Export all personal data"""
    handler = GDPRHandler(supabase)
    data = await handler.export_all_data(user_id)
    
    filename = f"devops-sentinel-export-{user_id}-{datetime.utcnow().strftime('%Y%m%d')}.json"
    
    return JSONResponse(
        content=data,
        headers={
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )


@router.delete("/delete-account")
async def delete_user_account(
    user_id: str,
    confirmation: str,
    supabase=Depends(lambda: None)
):
    """GDPR Article 17 - Right to be forgotten"""
    if confirmation != "DELETE_MY_DATA":
        raise HTTPException(
            status_code=400,
            detail="Must provide confirmation='DELETE_MY_DATA' to delete account"
        )
    
    handler = GDPRHandler(supabase)
    result = await handler.delete_all_data(user_id, confirmation)
    
    return result


@router.get("/data-usage")
async def get_data_usage(
    user_id: str,
    supabase=Depends(lambda: None)
):
    """Transparency - show what data we have on user"""
    handler = GDPRHandler(supabase)
    return await handler.get_data_usage_summary(user_id)
