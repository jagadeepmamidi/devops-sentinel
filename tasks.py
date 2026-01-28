"""
DevOps Sentinel - Task Definitions
===================================
CrewAI tasks for the monitoring pipeline.
"""

from crewai import Task, Agent

from tools import (
    health_check_tool,
    slack_alert_tool,
    log_analysis_tool,
    deployment_history_tool,
    database_health_tool
)


class SentinelTasks:
    """
    Factory for creating DevOps Sentinel tasks.
    
    Pipeline:
    1. Monitor - Check service health
    2. Alert - Send Slack notification (on failure)
    3. Investigate - Analyze logs, deployments, DB
    4. Strategize - Create action plan
    5. Postmortem - Generate incident report
    """
    
    def monitor_task(self, agent: Agent, url: str) -> Task:
        """
        Create a health monitoring task.
        
        Args:
            agent: The Watcher agent.
            url: URL to monitor.
        
        Returns:
            Task configured for health checking.
        """
        return Task(
            description=(
                f"Check the health of the service at: {url}\n\n"
                "Your task:\n"
                "1. Use the health_check tool to check the URL\n"
                "2. Report the HTTP status code\n"
                "3. Report the response time\n"
                "4. If the status code indicates failure (4xx or 5xx), "
                "include the response body for diagnosis\n\n"
                "Be precise and include all relevant metrics."
            ),
            agent=agent,
            expected_output=(
                "A concise health report including: "
                "status code, response time, and health status (HEALTHY/UNHEALTHY). "
                "Include error details if unhealthy."
            ),
            tools=[health_check_tool]
        )
    
    def alert_task(self, agent: Agent, context: Task) -> Task:
        """
        Create an alerting task.
        
        Args:
            agent: The First Responder agent.
            context: The monitoring task to get incident details from.
        
        Returns:
            Task configured for Slack alerting.
        """
        return Task(
            description=(
                "An incident has been detected. Your task is to alert the team.\n\n"
                "Compose a Slack alert with:\n"
                "1. Clear incident title (e.g., 'Service Outage Detected')\n"
                "2. Affected service URL\n"
                "3. HTTP status code and error message\n"
                "4. Timestamp of detection\n"
                "5. Severity indicator (CRITICAL/HIGH/MEDIUM)\n\n"
                "Format using Slack markdown. Be professional and concise."
            ),
            agent=agent,
            context=[context],
            expected_output="Confirmation that the Slack alert was sent successfully.",
            tools=[slack_alert_tool]
        )
    
    def investigate_task(self, agent: Agent, context: Task) -> Task:
        """
        Create a root cause analysis task.
        
        Args:
            agent: The Investigator agent.
            context: The monitoring task with incident details.
        
        Returns:
            Task configured for investigation.
        """
        return Task(
            description=(
                "A service is experiencing issues. Conduct a root cause analysis.\n\n"
                "Your investigation steps:\n"
                "1. Use log_analysis to check recent application logs for errors\n"
                "2. Use deployment_history to see recent deployments\n"
                "3. Use database_health to verify database connectivity\n\n"
                "Correlate your findings to form a hypothesis about the root cause. "
                "Consider: Was there a recent deployment? Are there database errors? "
                "What patterns appear in the logs?"
            ),
            agent=agent,
            context=[context],
            expected_output=(
                "A detailed investigation report with:\n"
                "- Log analysis findings\n"
                "- Deployment history review\n"
                "- Database health status\n"
                "- Root cause hypothesis\n"
                "Format as markdown."
            ),
            tools=[log_analysis_tool, deployment_history_tool, database_health_tool]
        )
    
    def strategize_task(self, agent: Agent, context: Task) -> Task:
        """
        Create an action planning task.
        
        Args:
            agent: The Strategist agent.
            context: The investigation task with RCA findings.
        
        Returns:
            Task configured for action planning.
        """
        return Task(
            description=(
                "Based on the investigation findings, create a remediation plan.\n\n"
                "Your action plan should include:\n"
                "1. Immediate actions (to restore service quickly)\n"
                "2. Short-term fixes (to prevent recurrence)\n"
                "3. Long-term improvements (to improve resilience)\n\n"
                "Number each action item. Be specific about what to do, "
                "not just what went wrong. Frame it as advice to a colleague."
            ),
            agent=agent,
            context=[context],
            expected_output=(
                "A prioritized, numbered action plan with:\n"
                "- Immediate actions (1-2 items)\n"
                "- Short-term fixes (2-3 items)\n"
                "- Long-term improvements (2-3 items)\n"
                "Format as markdown."
            )
        )
    
    def postmortem_task(self, agent: Agent, context: Task, incident_data: dict) -> Task:
        """
        Create a postmortem generation task.
        
        Args:
            agent: The Strategist agent.
            context: The strategize task with action plan.
            incident_data: Additional incident metadata.
        
        Returns:
            Task configured for postmortem generation.
        """
        return Task(
            description=(
                f"Generate a formal postmortem document for this incident.\n\n"
                f"Service: {incident_data.get('service_name', 'Unknown')}\n"
                f"URL: {incident_data.get('service_url', 'Unknown')}\n"
                f"Detected: {incident_data.get('detected_at', 'Unknown')}\n"
                f"Resolved: {incident_data.get('resolved_at', 'Unknown')}\n\n"
                "Your postmortem should include:\n"
                "1. Executive Summary - Brief description of the incident\n"
                "2. Timeline - Key events in chronological order\n"
                "3. Root Cause - Technical explanation of what went wrong\n"
                "4. Impact - Services and users affected\n"
                "5. Action Items - Numbered list of remediation steps\n"
                "6. Lessons Learned - What the team should take away\n\n"
                "Format as a professional markdown document."
            ),
            agent=agent,
            context=[context],
            expected_output=(
                "A complete postmortem document in markdown format, "
                "suitable for archiving and sharing with stakeholders."
            )
        )


# Singleton instance
sentinel_tasks = SentinelTasks()