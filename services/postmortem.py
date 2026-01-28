"""
DevOps Sentinel - Postmortem Generator
======================================
AI-powered postmortem generation from incident data.
"""

from typing import Optional
from datetime import datetime
from uuid import UUID

from models import Incident, Postmortem, IncidentStatus
from services.llm_manager import llm_manager
from config import settings


POSTMORTEM_PROMPT = """You are an expert Site Reliability Engineer creating a postmortem document.

Based on the following incident data, generate a comprehensive postmortem:

SERVICE: {service_name}
URL: {service_url}
DETECTED AT: {detected_at}
RESOLVED AT: {resolved_at}
ERROR CODE: {error_code}
ERROR MESSAGE: {error_message}

INVESTIGATION REPORT:
{investigation_report}

ACTION PLAN:
{action_plan}

TIMELINE:
{timeline}

Generate a professional postmortem with the following sections:
1. SUMMARY - Brief description of what happened
2. TIMELINE - Key events in chronological order
3. ROOT CAUSE ANALYSIS - Technical explanation of why this happened
4. ACTION ITEMS - Numbered list of specific, actionable remediation steps
5. LESSONS LEARNED - What the team should take away from this incident

Format your response as structured text. Be specific and technical.
"""


class PostmortemGenerator:
    """Generates AI-powered postmortems from incident data."""
    
    def generate(self, incident: Incident) -> Optional[Postmortem]:
        """
        Generate a postmortem from an incident.
        
        Args:
            incident: The resolved incident to generate postmortem for.
        
        Returns:
            Postmortem object with generated content.
        """
        if incident.status != IncidentStatus.RESOLVED:
            return None
        
        # Format timeline
        timeline_str = "\n".join([
            f"- {event.timestamp.isoformat()}: [{event.event_type}] {event.description}"
            for event in incident.timeline
        ])
        
        prompt = POSTMORTEM_PROMPT.format(
            service_name=incident.service_name,
            service_url=incident.service_url,
            detected_at=incident.detected_at.isoformat(),
            resolved_at=incident.resolved_at.isoformat() if incident.resolved_at else "Ongoing",
            error_code=incident.error_code or "N/A",
            error_message=incident.error_message or "N/A",
            investigation_report=incident.investigation_report or "No investigation report available.",
            action_plan=incident.action_plan or "No action plan available.",
            timeline=timeline_str or "No timeline events recorded."
        )
        
        if settings.enable_privacy_logging:
            print(f"[PRIVACY] Generating postmortem for incident: {incident.id}")
            print(f"[PRIVACY] Data sent to LLM: service_name, service_url, timestamps, error details")
        
        try:
            llm = llm_manager.get_llm()
            response = llm.invoke(prompt)
            content = response.content
            
            # Parse the response into structured sections
            postmortem = self._parse_response(content, incident)
            return postmortem
            
        except Exception as e:
            print(f"[ERROR] Postmortem generation failed: {e}")
            return None
    
    def _parse_response(self, content: str, incident: Incident) -> Postmortem:
        """Parse LLM response into structured postmortem."""
        # Extract sections from the response
        sections = {
            "summary": "",
            "timeline": "",
            "root_cause": "",
            "action_items": [],
            "lessons": ""
        }
        
        current_section = None
        lines = content.split("\n")
        
        for line in lines:
            line_lower = line.lower().strip()
            
            if "summary" in line_lower and len(line) < 50:
                current_section = "summary"
            elif "timeline" in line_lower and len(line) < 50:
                current_section = "timeline"
            elif "root cause" in line_lower and len(line) < 50:
                current_section = "root_cause"
            elif "action item" in line_lower and len(line) < 50:
                current_section = "action_items"
            elif "lesson" in line_lower and len(line) < 50:
                current_section = "lessons"
            elif current_section:
                if current_section == "action_items":
                    # Parse numbered items
                    stripped = line.strip()
                    if stripped and (stripped[0].isdigit() or stripped.startswith("-")):
                        # Remove leading numbers/bullets
                        item = stripped.lstrip("0123456789.-) ").strip()
                        if item:
                            sections["action_items"].append(item)
                else:
                    sections[current_section] += line + "\n"
        
        # Calculate MTTR if resolved
        mttr_str = ""
        if incident.resolved_at and incident.detected_at:
            mttr = (incident.resolved_at - incident.detected_at).total_seconds()
            mttr_str = f"MTTR: {mttr:.0f} seconds"
        
        return Postmortem(
            incident_id=incident.id,
            title=f"Incident Postmortem: {incident.service_name} - {incident.detected_at.strftime('%Y-%m-%d')}",
            summary=sections["summary"].strip() or f"{incident.service_name} experienced an outage.",
            timeline_markdown=sections["timeline"].strip() or "Timeline not available.",
            root_cause_analysis=sections["root_cause"].strip() or "Root cause analysis pending.",
            action_items=sections["action_items"] or ["Review incident and add action items."],
            lessons_learned=sections["lessons"].strip() or None,
            generated_by_model=settings.default_model
        )


# Singleton instance
postmortem_generator = PostmortemGenerator()
