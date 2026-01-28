"""
DevOps Sentinel - Monitoring Orchestrator
==========================================
Coordinates continuous monitoring and incident lifecycle.
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from models import (
    ServiceConfig, 
    HealthCheckResult, 
    Incident, 
    IncidentStatus,
    IncidentSeverity
)
from config import settings


class MonitoringOrchestrator:
    """
    Central coordinator for service monitoring.
    
    Responsibilities:
    - Manage service registry
    - Schedule health checks
    - Detect incidents
    - Coordinate agent response
    """
    
    def __init__(self):
        self.services: Dict[UUID, ServiceConfig] = {}
        self.active_incidents: Dict[UUID, Incident] = {}
        self.is_running: bool = False
        self._callbacks: List = []
    
    def add_service(self, service: ServiceConfig) -> None:
        """Add a service to monitor."""
        self.services[service.id] = service
        
        if settings.enable_privacy_logging:
            print(f"[PRIVACY] Service added: {service.name} ({service.url})")
    
    def remove_service(self, service_id: UUID) -> None:
        """Remove a service from monitoring."""
        if service_id in self.services:
            del self.services[service_id]
    
    def on_event(self, callback) -> None:
        """Register an event callback for real-time updates."""
        self._callbacks.append(callback)
    
    async def _emit_event(self, event_type: str, data: dict) -> None:
        """Emit an event to all registered callbacks."""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, data)
                else:
                    callback(event_type, data)
            except Exception as e:
                print(f"[ERROR] Event callback failed: {e}")
    
    async def check_service(self, service: ServiceConfig) -> HealthCheckResult:
        """
        Perform a health check on a service.
        
        Returns:
            HealthCheckResult with status and timing.
        """
        from tools import health_check_tool
        
        start_time = time.time()
        result_str = await health_check_tool._arun(service.url)
        response_time = (time.time() - start_time) * 1000
        
        # Parse result
        is_healthy = "FAILED" not in result_str and "200" in result_str
        status_code = None
        
        if "Status Code:" in result_str:
            try:
                code_str = result_str.split("Status Code:")[1].split("\n")[0].strip()
                status_code = int(code_str)
            except (ValueError, IndexError):
                pass
        
        result = HealthCheckResult(
            service_id=service.id,
            status_code=status_code,
            response_time_ms=response_time,
            is_healthy=is_healthy,
            error_message=result_str if not is_healthy else None
        )
        
        # Emit event
        await self._emit_event("health_check", {
            "service_id": str(service.id),
            "service_name": service.name,
            "is_healthy": is_healthy,
            "response_time_ms": response_time,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return result
    
    async def _handle_failure(self, service: ServiceConfig, result: HealthCheckResult) -> None:
        """Handle a service failure by creating an incident."""
        # Check if there's already an active incident for this service
        for incident in self.active_incidents.values():
            if incident.service_id == service.id and incident.status != IncidentStatus.RESOLVED:
                return  # Already tracking this incident
        
        # Create new incident
        incident = Incident(
            service_id=service.id,
            service_name=service.name,
            service_url=service.url,
            status=IncidentStatus.DETECTING,
            severity=IncidentSeverity.HIGH if result.status_code and result.status_code >= 500 else IncidentSeverity.MEDIUM,
            error_code=result.status_code,
            error_message=result.error_message
        )
        
        # Calculate MTTD
        incident.mttd_seconds = (datetime.utcnow() - incident.detected_at).total_seconds()
        
        incident.add_event(
            event_type="detected",
            description=f"Service failure detected. Status: {result.status_code}",
            agent="MonitoringOrchestrator"
        )
        
        self.active_incidents[incident.id] = incident
        
        # Emit event
        await self._emit_event("incident_created", {
            "incident_id": str(incident.id),
            "service_name": service.name,
            "severity": incident.severity.value,
            "mttd_seconds": incident.mttd_seconds
        })
        
        # Trigger agent response
        await self._trigger_agent_response(incident)
    
    async def _trigger_agent_response(self, incident: Incident) -> None:
        """Trigger the agent crew to respond to an incident."""
        from crewai import Crew, Process
        from agents import SentinelAgents
        from tasks import SentinelTasks
        
        # Update incident status
        incident.status = IncidentStatus.ALERTING
        incident.add_event("alerting", "Notifying team via Slack", "FirstResponder")
        
        await self._emit_event("incident_updated", {
            "incident_id": str(incident.id),
            "status": incident.status.value
        })
        
        # Initialize agents
        agents = SentinelAgents()
        tasks = SentinelTasks()
        
        # Create the crew
        watcher = agents.watcher_agent()
        responder = agents.first_responder_agent()
        investigator = agents.investigator_agent()
        strategist = agents.strategist_agent()
        
        # Create tasks
        monitor_task = tasks.monitor_task(watcher, incident.service_url)
        alert_task = tasks.alert_task(responder, monitor_task)
        investigate_task = tasks.investigate_task(investigator, monitor_task)
        strategize_task = tasks.strategize_task(strategist, investigate_task)
        
        # Update status to investigating
        incident.status = IncidentStatus.INVESTIGATING
        incident.add_event("investigating", "Agents analyzing root cause", "Investigator")
        
        # Execute crew
        crew = Crew(
            agents=[watcher, responder, investigator, strategist],
            tasks=[monitor_task, alert_task, investigate_task, strategize_task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        
        # Store results in incident
        incident.action_plan = str(result)
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.utcnow()
        incident.mttr_seconds = (incident.resolved_at - incident.detected_at).total_seconds()
        
        incident.add_event("resolved", "Action plan generated", "Strategist")
        
        # Emit completion event
        await self._emit_event("incident_resolved", {
            "incident_id": str(incident.id),
            "mttr_seconds": incident.mttr_seconds,
            "action_plan": incident.action_plan[:500]  # Truncate for event
        })
        
        # Save to database
        from services.supabase_client import supabase_client
        if supabase_client.is_connected:
            supabase_client.create_incident(incident)
            supabase_client.update_incident(incident)
    
    async def run(self) -> None:
        """
        Start the continuous monitoring loop.
        
        Runs health checks on all services at their configured intervals.
        """
        self.is_running = True
        
        print("[INFO] Monitoring orchestrator started")
        
        while self.is_running:
            tasks = []
            
            for service in self.services.values():
                if service.is_active:
                    tasks.append(self._check_and_handle(service))
            
            if tasks:
                await asyncio.gather(*tasks)
            
            # Wait for the shortest interval
            min_interval = min(
                (s.check_interval for s in self.services.values() if s.is_active),
                default=settings.check_interval_seconds
            )
            
            await asyncio.sleep(min_interval)
    
    async def _check_and_handle(self, service: ServiceConfig) -> None:
        """Check a service and handle failures."""
        result = await self.check_service(service)
        
        if not result.is_healthy:
            await self._handle_failure(service, result)
    
    def stop(self) -> None:
        """Stop the monitoring loop."""
        self.is_running = False


# Singleton instance
orchestrator = MonitoringOrchestrator()
