"""
Cost Tracker - AI Usage Monitoring and Budget Management
=========================================================

Track AI API costs per user and prevent budget overruns
"""

from datetime import datetime, timedelta
from typing import Dict, Optional
import asyncio


class CostTracker:
    """
    Track and limit AI usage costs per user
    
    Features:
    - Log every AI API call with cost
    - Monthly budget limits per tier
    - Admin alerts for over-budget users
    - Cost dashboard for admins
    """
    
    TIER_BUDGETS = {
        'free': 0.50,      # $0.50/month max
        'pro': 10.00,      # $10/month max
        'enterprise': -1   # unlimited
    }
    
    MODEL_COSTS = {
        # Per 1K tokens (input + output averaged)
        'gemini-1.5-flash': 0.0001,
        'gemini-1.5-pro': 0.0025,
        'gemini-2.0-flash': 0.00015,
        'gpt-4': 0.03,
        'gpt-4-turbo': 0.01,
        'gpt-3.5-turbo': 0.0015,
        'claude-3-sonnet': 0.003,
        'claude-3-haiku': 0.00025,
        'text-embedding-3-small': 0.00002,
        'text-embedding-3-large': 0.00013
    }
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    async def log_ai_call(
        self,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        operation: str = 'unknown'
    ) -> Dict:
        """
        Log every AI API call
        
        Args:
            user_id: User making the call
            model: AI model used
            input_tokens: Tokens in prompt
            output_tokens: Tokens in response
            operation: What this call was for (postmortem, embedding, etc)
        
        Returns:
            Cost info and budget status
        """
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        
        # Log to database
        await self.supabase.table('ai_usage').insert({
            'user_id': user_id,
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost_usd': cost,
            'operation': operation,
            'timestamp': datetime.utcnow().isoformat()
        }).execute()
        
        # Check budget
        monthly_cost = await self.get_monthly_cost(user_id)
        user_tier = await self.get_user_tier(user_id)
        budget = self.TIER_BUDGETS.get(user_tier, 1.0)
        
        budget_status = {
            'cost_usd': cost,
            'monthly_total': monthly_cost,
            'budget': budget,
            'remaining': budget - monthly_cost if budget > 0 else float('inf'),
            'tier': user_tier
        }
        
        # Alert if over budget
        if budget > 0 and monthly_cost > budget:
            await self._alert_over_budget(user_id, monthly_cost, budget, user_tier)
            budget_status['over_budget'] = True
        
        # Warn if approaching limit (80%)
        if budget > 0 and monthly_cost > budget * 0.8:
            budget_status['warning'] = 'Approaching monthly budget limit'
        
        return budget_status
    
    async def check_budget_before_call(
        self,
        user_id: str,
        estimated_tokens: int = 2000
    ) -> bool:
        """
        Check if user has budget for an AI call
        
        Args:
            user_id: User to check
            estimated_tokens: Expected token usage
        
        Returns:
            True if call allowed, False if over budget
        
        Raises:
            BudgetExceeded if user is over limit
        """
        monthly_cost = await self.get_monthly_cost(user_id)
        user_tier = await self.get_user_tier(user_id)
        budget = self.TIER_BUDGETS.get(user_tier, 1.0)
        
        # Enterprise = unlimited
        if budget < 0:
            return True
        
        # Check if already over
        if monthly_cost >= budget:
            raise BudgetExceeded(
                f"Monthly AI budget exceeded for {user_tier} tier. "
                f"Used: ${monthly_cost:.2f} / Budget: ${budget:.2f}. "
                f"Upgrade to Pro for higher limits."
            )
        
        return True
    
    async def get_monthly_cost(self, user_id: str) -> float:
        """Get user's total AI costs this month"""
        month_start = datetime.utcnow().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        
        result = await self.supabase.table('ai_usage').select(
            'cost_usd'
        ).eq('user_id', user_id).gte(
            'timestamp', month_start.isoformat()
        ).execute()
        
        if not result.data:
            return 0.0
        
        return sum(r['cost_usd'] for r in result.data)
    
    async def get_user_tier(self, user_id: str) -> str:
        """Get user's subscription tier"""
        result = await self.supabase.table('users').select(
            'subscription_tier'
        ).eq('id', user_id).execute()
        
        if result.data:
            return result.data[0].get('subscription_tier', 'free')
        
        return 'free'
    
    async def get_usage_breakdown(self, user_id: str) -> Dict:
        """Get detailed usage breakdown for user"""
        month_start = datetime.utcnow().replace(day=1)
        
        result = await self.supabase.table('ai_usage').select(
            '*'
        ).eq('user_id', user_id).gte(
            'timestamp', month_start.isoformat()
        ).execute()
        
        if not result.data:
            return {'total_cost': 0, 'calls': 0, 'by_operation': {}}
        
        by_operation = {}
        by_model = {}
        
        for record in result.data:
            op = record.get('operation', 'unknown')
            model = record.get('model', 'unknown')
            cost = record.get('cost_usd', 0)
            
            by_operation[op] = by_operation.get(op, 0) + cost
            by_model[model] = by_model.get(model, 0) + cost
        
        return {
            'total_cost': sum(r['cost_usd'] for r in result.data),
            'total_tokens': sum(
                r.get('input_tokens', 0) + r.get('output_tokens', 0) 
                for r in result.data
            ),
            'calls': len(result.data),
            'by_operation': by_operation,
            'by_model': by_model
        }
    
    async def get_admin_dashboard(self) -> Dict:
        """Admin view of all AI costs"""
        month_start = datetime.utcnow().replace(day=1)
        
        # Total costs this month
        result = await self.supabase.table('ai_usage').select(
            'user_id, cost_usd'
        ).gte('timestamp', month_start.isoformat()).execute()
        
        if not result.data:
            return {
                'total_month': 0,
                'per_user_avg': 0,
                'top_users': [],
                'budget_alerts': []
            }
        
        total = sum(r['cost_usd'] for r in result.data)
        
        # Per user costs
        user_costs = {}
        for r in result.data:
            uid = r['user_id']
            user_costs[uid] = user_costs.get(uid, 0) + r['cost_usd']
        
        # Top 10 users by cost
        top_users = sorted(
            user_costs.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        # Find over-budget users
        over_budget = []
        for uid, cost in user_costs.items():
            tier = await self.get_user_tier(uid)
            budget = self.TIER_BUDGETS.get(tier, 1.0)
            if budget > 0 and cost > budget:
                over_budget.append({
                    'user_id': uid,
                    'cost': cost,
                    'budget': budget,
                    'tier': tier
                })
        
        return {
            'total_month': total,
            'unique_users': len(user_costs),
            'per_user_avg': total / len(user_costs) if user_costs else 0,
            'top_users': [{'user_id': u, 'cost': c} for u, c in top_users],
            'over_budget_users': over_budget
        }
    
    def _calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """Calculate cost for API call"""
        rate = self.MODEL_COSTS.get(model, 0.001)  # Default rate
        total_tokens = input_tokens + output_tokens
        return (total_tokens / 1000) * rate
    
    async def _alert_over_budget(
        self,
        user_id: str,
        current: float,
        budget: float,
        tier: str
    ):
        """Alert admin about over-budget user"""
        await self.supabase.table('admin_alerts').insert({
            'type': 'budget_exceeded',
            'user_id': user_id,
            'message': f"User {user_id} exceeded {tier} budget: ${current:.2f} / ${budget:.2f}",
            'severity': 'warning',
            'created_at': datetime.utcnow().isoformat()
        }).execute()


class BudgetExceeded(Exception):
    """Raised when user exceeds AI budget"""
    pass


# Example usage
if __name__ == "__main__":
    async def demo():
        class MockSupabase:
            def table(self, name):
                return self
            def insert(self, data):
                return self
            def select(self, *args):
                return self
            def eq(self, *args):
                return self
            def gte(self, *args):
                return self
            async def execute(self):
                class R:
                    data = [{'cost_usd': 0.01, 'subscription_tier': 'free'}]
                return R()
        
        tracker = CostTracker(MockSupabase())
        
        # Log a call
        result = await tracker.log_ai_call(
            user_id='user-123',
            model='gemini-1.5-flash',
            input_tokens=1000,
            output_tokens=500,
            operation='postmortem'
        )
        
        print(f"Cost: ${result['cost_usd']:.4f}")
        print(f"Monthly total: ${result['monthly_total']:.2f}")
        print(f"Budget remaining: ${result['remaining']:.2f}")
    
    asyncio.run(demo())
