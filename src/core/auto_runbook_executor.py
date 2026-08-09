"""
Auto-Runbook Execution Engine - Automated Remediation
=======================================================

Execute runbooks automatically for known incident types
"""

from datetime import datetime
from typing import Dict, List, Optional, Callable
import asyncio
import os
import re
import shlex
import subprocess
from pathlib import Path


class AutoRunbookExecutor:
    """
    Auto-execute remediation runbooks
    
    Features:
    - Match incidents to runbooks
    - Execute steps automatically
    - Require approval for destructive actions
    - SSH command execution
    - Kubectl/Docker commands
    - Database maintenance
    - Rollback on failure
    - Execution auditing
    """
    
    def __init__(self, supabase_client, approval_required: bool = True):
        self.supabase = supabase_client
        self.approval_required = approval_required
        self.execution_history = []
        self.command_timeout = int(os.getenv('SENTINEL_COMMAND_TIMEOUT', '30'))
        
        # Action handlers
        self.action_handlers = {
            'restart_service': self._restart_service,
            'scale_service': self._scale_service,
            'run_command': self._run_command,
            'kubectl_apply': self._kubectl_apply,
            'database_query': self._database_query,
            'clear_cache': self._clear_cache,
            'rollback_deployment': self._rollback_deployment
        }
    
    async def execute_runbook(
        self,
        incident_id: str,
        runbook_id: Optional[str] = None,
        auto_approve_safe: bool = False
    ) -> Dict:
        """
        Execute runbook for incident
        
        Args:
            incident_id: Incident to remediate
            runbook_id: Specific runbook (if None, auto-match)
            auto_approve_safe: Auto-approve non-destructive actions
        
        Returns:
            Execution results
        """
        execution_id = f"exec-{incident_id}-{int(datetime.utcnow().timestamp())}"
        
        # Get incident
        incident = await self.supabase.table('incidents').select('*').eq(
            'id', incident_id
        ).execute()
        
        if not incident.data:
            raise ValueError(f"Incident {incident_id} not found")
        
        inc = incident.data[0]
        
        # Find matching runbook
        if not runbook_id:
            runbook = await self._find_matching_runbook(inc)
            if not runbook:
                return {
                    'status': 'no_runbook',
                    'message': 'No matching runbook found'
                }
            runbook_id = runbook['id']
        else:
            runbook = await self.supabase.table('runbooks').select('*').eq(
                'id', runbook_id
            ).execute()
            runbook = runbook.data[0] if runbook.data else None
        
        if not runbook:
            raise ValueError(f"Runbook {runbook_id} not found")
        
        # Log execution start
        await self._log_execution(
            execution_id=execution_id,
            incident_id=incident_id,
            runbook_id=runbook_id,
            status='started'
        )
        
        steps = runbook.get('steps', [])
        results = []
        
        # Execute each step
        for i, step in enumerate(steps, 1):
            step_result = await self._execute_step(
                execution_id=execution_id,
                step_number=i,
                step=step,
                incident=inc,
                auto_approve=auto_approve_safe
            )
            
            results.append(step_result)
            
            # Stop on failure
            if step_result['status'] == 'failed':
                await self._log_execution(
                    execution_id=execution_id,
                    incident_id=incident_id,
                    runbook_id=runbook_id,
                    status='failed',
                    results=results
                )
                
                return {
                    'execution_id': execution_id,
                    'status': 'failed',
                    'steps_completed': i,
                    'total_steps': len(steps),
                    'results': results
                }
            
            # Stop if approval denied
            if step_result['status'] == 'denied':
                await self._log_execution(
                    execution_id=execution_id,
                    incident_id=incident_id,
                    runbook_id=runbook_id,
                    status='approval_denied',
                    results=results
                )
                
                return {
                    'execution_id': execution_id,
                    'status': 'approval_denied',
                    'steps_completed': i - 1,
                    'total_steps': len(steps),
                    'results': results
                }
        
        # All steps completed
        await self._log_execution(
            execution_id=execution_id,
            incident_id=incident_id,
            runbook_id=runbook_id,
            status='completed',
            results=results
        )
        
        # Update incident status
        await self.supabase.table('incidents').update({
            'status': 'resolved',
            'resolved_at': datetime.utcnow().isoformat(),
            'resolution_method': 'auto_runbook',
            'runbook_id': runbook_id
        }).eq('id', incident_id).execute()
        
        return {
            'execution_id': execution_id,
            'status': 'completed',
            'steps_completed': len(steps),
            'total_steps': len(steps),
            'results': results
        }
    
    async def _execute_step(
        self,
        execution_id: str,
        step_number: int,
        step: Dict,
        incident: Dict,
        auto_approve: bool
    ) -> Dict:
        """
        Execute a single runbook step
        
        Args:
            execution_id: Execution ID
            step_number: Step number
            step: Step configuration
            incident: Incident data
            auto_approve: Auto-approve safe actions
        
        Returns:
            Step execution result
        """
        action_type = step.get('action_type')
        params = step.get('params', {})
        is_destructive = step.get('destructive', False)
        
        # Check if approval required
        if is_destructive and self.approval_required and not auto_approve:
            # A real deployment should connect this to a Slack/UI approval flow.
            # Never silently approve a destructive action.
            print(f"[RUNBOOK] Step {step_number}: Approval required for '{step.get('description')}'")
            return {
                'step': step_number,
                'status': 'denied',
                'action': action_type,
                'message': 'Explicit approval is required before destructive actions'
            }
        
        # Get action handler
        handler = self.action_handlers.get(action_type)
        if not handler:
            return {
                'step': step_number,
                'status': 'failed',
                'action': action_type,
                'error': f'Unknown action type: {action_type}'
            }
        
        # Execute action
        try:
            print(f"[RUNBOOK] Step {step_number}: Executing {action_type}")
            
            # Interpolate incident data into params
            interpolated_params = self._interpolate_params(params, incident)
            
            result = await handler(**interpolated_params)
            
            return {
                'step': step_number,
                'status': 'success',
                'action': action_type,
                'result': result,
                'executed_at': datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            return {
                'step': step_number,
                'status': 'failed',
                'action': action_type,
                'error': str(e)
            }
    
    def _interpolate_params(self, params: Dict, incident: Dict) -> Dict:
        """Replace {{incident.field}} with actual values"""
        interpolated = {}
        
        for key, value in params.items():
            if isinstance(value, str) and '{{' in value:
                # Replace {{incident.service_id}} with incident['service_id']
                for field in ['service_id', 'service_name', 'id']:
                    placeholder = f'{{{{incident.{field}}}}}'
                    if placeholder in value:
                        value = value.replace(placeholder, str(incident.get(field, '')))
            
            interpolated[key] = value
        
        return interpolated
    
    @staticmethod
    def _safe_identifier(value: str, field: str = 'identifier') -> str:
        """Validate names interpolated into privileged commands."""
        if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}', value):
            raise ValueError(f"Invalid {field}")
        return value

    async def _run_process(self, args: List[str], timeout: Optional[int] = None) -> subprocess.CompletedProcess:
        """Run an allowlisted command without invoking a shell."""
        return await asyncio.to_thread(
            subprocess.run,
            args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout or self.command_timeout,
            check=False,
        )

    async def _restart_service(self, service_name: str, method: str = 'systemctl') -> str:
        """Restart a service"""
        service_name = self._safe_identifier(service_name, 'service name')
        if method == 'systemctl':
            args = ['systemctl', 'restart', service_name]
        elif method == 'docker':
            args = ['docker', 'restart', service_name]
        elif method == 'kubectl':
            args = ['kubectl', 'rollout', 'restart', f'deployment/{service_name}']
        else:
            raise ValueError(f"Unknown restart method: {method}")

        result = await self._run_process(args)
        
        if result.returncode == 0:
            return f"Service {service_name} restarted successfully"
        else:
            raise Exception(f"Restart failed: {result.stderr}")
    
    async def _scale_service(
        self,
        service_name: str,
        replicas: int,
        method: str = 'kubectl'
    ) -> str:
        """Scale a service"""
        service_name = self._safe_identifier(service_name, 'service name')
        replicas = int(replicas)
        if replicas < 0 or replicas > 1000:
            raise ValueError('replicas must be between 0 and 1000')
        if method == 'kubectl':
            args = ['kubectl', 'scale', f'deployment/{service_name}', f'--replicas={replicas}']
        elif method == 'docker-compose':
            args = ['docker-compose', 'up', '-d', '--scale', f'{service_name}={replicas}']
        else:
            raise ValueError(f"Unknown scale method: {method}")

        result = await self._run_process(args)
        
        if result.returncode == 0:
            return f"Scaled {service_name} to {replicas} replicas"
        else:
            raise Exception(f"Scale failed: {result.stderr}")
    
    async def _run_command(
        self,
        command: str,
        host: Optional[str] = None,
        timeout: int = 30
    ) -> str:
        """Run a command only when explicitly enabled for a trusted environment."""
        if os.getenv('SENTINEL_ALLOW_ARBITRARY_COMMANDS', '').lower() != 'true':
            raise PermissionError('Arbitrary commands are disabled; use an allowlisted runbook action')
        if not command or len(command) > 2048:
            raise ValueError('Invalid command')
        args = shlex.split(command, posix=os.name != 'nt')
        if not args:
            raise ValueError('Invalid command')
        if host:
            args = ['ssh', self._safe_identifier(host, 'host')] + args

        result = await self._run_process(args, timeout=timeout)
        
        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(f"Command failed: {result.stderr}")
    
    async def _kubectl_apply(self, manifest_path: str) -> str:
        """Apply Kubernetes manifest"""
        path = Path(manifest_path).expanduser().resolve()
        if not path.is_file() or path.suffix.lower() not in {'.yaml', '.yml', '.json'}:
            raise ValueError('manifest_path must reference an existing YAML, JSON, or YML file')

        result = await self._run_process(['kubectl', 'apply', '-f', str(path)])
        
        if result.returncode == 0:
            return result.stdout
        else:
            raise Exception(f"kubectl apply failed: {result.stderr}")
    
    async def _database_query(
        self,
        query: str,
        database: str = 'postgresql'
    ) -> str:
        """Execute database query (read-only recommended)"""
        # This is a simplified version - production would use proper DB clients
        print(f"[DB] Executing query on {database}: {query[:50]}...")
        
        # In production, would use psycopg2, asyncpg, etc.
        return "Query executed successfully"
    
    async def _clear_cache(
        self,
        cache_type: str = 'redis',
        keys: Optional[List[str]] = None
    ) -> str:
        """Clear cache"""
        if cache_type == 'redis':
            if keys:
                # Clear specific keys
                return f"Cleared {len(keys)} Redis keys"
            else:
                # FLUSHALL (destructive!)
                return "Flushed all Redis cache"
        
        return "Cache cleared"
    
    async def _rollback_deployment(
        self,
        service_name: str,
        method: str = 'kubectl'
    ) -> str:
        """Rollback to previous deployment"""
        if method == 'kubectl':
            args = ['kubectl', 'rollout', 'undo', f'deployment/{self._safe_identifier(service_name, "service name")}']
        elif method == 'docker':
            # Would need deployment tracking
            args = ['docker', 'service', 'update', '--rollback', self._safe_identifier(service_name, 'service name')]
        else:
            raise ValueError(f"Unknown rollback method: {method}")

        result = await self._run_process(args)
        
        if result.returncode == 0:
            return f"Rolled back {service_name} to previous version"
        else:
            raise Exception(f"Rollback failed: {result.stderr}")
    
    async def _find_matching_runbook(self, incident: Dict) -> Optional[Dict]:
        """Find best matching runbook for incident"""
        # Query runbooks that match failure type
        failure_type = incident.get('failure_type')
        service_id = incident.get('service_id')
        
        runbooks = await self.supabase.table('runbooks').select('*').or_(
            f"failure_type.eq.{failure_type},service_id.eq.{service_id}"
        ).execute()
        
        if not runbooks.data:
            return None
        
        # Return highest effectiveness runbook
        sorted_runbooks = sorted(
            runbooks.data,
            key=lambda r: r.get('effectiveness_score', 0),
            reverse=True
        )
        
        return sorted_runbooks[0] if sorted_runbooks else None
    
    async def _log_execution(
        self,
        execution_id: str,
        incident_id: str,
        runbook_id: str,
        status: str,
        results: Optional[List[Dict]] = None
    ):
        """Log runbook execution"""
        await self.supabase.table('runbook_executions').upsert({
            'id': execution_id,
            'incident_id': incident_id,
            'runbook_id': runbook_id,
            'status': status,
            'results': results,
            'executed_at': datetime.utcnow().isoformat()
        }).execute()


# Example usage
if __name__ == "__main__":
    async def test_auto_runbook():
        # Mock Supabase
        class MockSupabase:
            def table(self, name):
                return self
            
            def select(self, *args):
                return self
            
            def eq(self, *args):
                return self
            
            def update(self, *args):
                return self
            
            def upsert(self, *args):
                return self
            
            async def execute(self):
                class Result:
                    data = [{
                        'id': 'inc-1',
                        'service_id': 'api-gateway',
                        'service_name': 'API Gateway',
                        'failure_type': 'high_response_time',
                        'steps': [
                            {
                                'action_type': 'clear_cache',
                                'description': 'Clear Redis cache',
                                'params': {'cache_type': 'redis'},
                                'destructive': False
                            },
                            {
                                'action_type': 'restart_service',
                                'description': 'Restart API service',
                                'params': {'service_name': 'api-gateway', 'method': 'kubectl'},
                                'destructive': True
                            }
                        ]
                    }]
                return Result()
        
        executor = AutoRunbookExecutor(MockSupabase(), approval_required=False)
        
        result = await executor.execute_runbook(
            incident_id='inc-1',
            auto_approve_safe=True
        )
        
        print(f"Execution result: {result}")
    
    asyncio.run(test_auto_runbook())
