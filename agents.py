"""
DevOps Sentinel - Agent Definitions
====================================
Production-grade CrewAI agents with proper tool assignments.
"""

from crewai import Agent

from services.llm_manager import llm_manager
from tools import (
    health_check_tool,
    slack_alert_tool,
    log_analysis_tool,
    deployment_history_tool,
    database_health_tool
)


class SentinelAgents:
    """
    Factory for creating DevOps Sentinel agents.
    
    Agents:
    - Watcher: Monitors service health
    - First Responder: Sends alerts
    - Investigator: Performs root cause analysis
    - Strategist: Creates action plans and postmortems
    """
    
    def __init__(self):
        self.llm = llm_manager.get_llm()
    
    def watcher_agent(self) -> Agent:
        """
        Create the Watcher agent for health monitoring.
        
        Responsibilities:
        - Check service health endpoints
        - Report status codes and response times
        - Detect failures and anomalies
        """
        return Agent(
            role="Vigilant Uptime Monitor",
            goal="Monitor service health endpoints and immediately detect any failures or degradation.",
            backstory=(
                "You are DevOps Sentinel's first line of defense. "
                "Your sole purpose is to continuously check the health of web services "
                "and provide accurate, real-time status reports. You are precise, "
                "efficient, and never miss a single health check failure."
            ),
            llm=self.llm,
            tools=[health_check_tool],
            verbose=True,
            allow_delegation=False
        )
    
    def first_responder_agent(self) -> Agent:
        """
        Create the First Responder agent for alerting.
        
        Responsibilities:
        - Send Slack alerts for incidents
        - Format alerts professionally
        - Include relevant incident details
        """
        return Agent(
            role="Incident Alert Coordinator",
            goal="Immediately notify the engineering team of any service incidents via Slack.",
            backstory=(
                "You are the voice of the Sentinel system. When an incident is detected, "
                "you craft clear, professional, and informative alerts that give engineers "
                "all the context they need. You use markdown formatting to make alerts "
                "scannable and actionable. Every second counts, so you act swiftly."
            ),
            llm=self.llm,
            tools=[slack_alert_tool],
            verbose=True,
            allow_delegation=False
        )
    
    def investigator_agent(self) -> Agent:
        """
        Create the Investigator agent for root cause analysis.
        
        Responsibilities:
        - Analyze application logs
        - Check deployment history
        - Verify database health
        - Correlate findings into a hypothesis
        """
        return Agent(
            role="SRE Root Cause Analyst",
            goal="Conduct thorough root cause analysis using all available diagnostic tools.",
            backstory=(
                "You are a seasoned Site Reliability Engineer in AI form. "
                "When a service fails, you methodically investigate the cause. "
                "You check logs for errors, review recent deployments, verify database health, "
                "and correlate your findings into a clear hypothesis. "
                "Your analysis is evidence-based and technically precise."
            ),
            llm=self.llm,
            tools=[log_analysis_tool, deployment_history_tool, database_health_tool],
            verbose=True,
            allow_delegation=False
        )
    
    def strategist_agent(self) -> Agent:
        """
        Create the Strategist agent for action planning.
        
        Responsibilities:
        - Create prioritized action plans
        - Generate postmortem documents
        - Provide specific remediation steps
        """
        return Agent(
            role="SRE Resolution Strategist",
            goal="Create actionable, prioritized remediation plans based on investigation findings.",
            backstory=(
                "You are the strategic mind of the Sentinel system. "
                "After the Investigator presents their findings, you synthesize the information "
                "into a clear, prioritized action plan. You think like a senior SRE - "
                "considering both immediate fixes and long-term improvements. "
                "Your plans are specific, actionable, and numbered for easy execution."
            ),
            llm=self.llm,
            tools=[],
            verbose=True,
            allow_delegation=False
        )


# Singleton instance
sentinel_agents = SentinelAgents()