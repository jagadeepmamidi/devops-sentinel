"""
AI Postmortem Generator
=======================

Generate structured postmortems from incident data using AI
"""

from datetime import datetime
from typing import Dict, List, Optional
import json
import logging

try:
    from langchain_core.messages import SystemMessage, HumanMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class PostmortemGenerator:
    """
    AI-powered postmortem generation
    
    Features:
    - Auto-generate from incident timeline
    - SRE-standard format
    - Action item extraction
    - Blameless language enforcement
    """
    
    # Standard postmortem template
    TEMPLATE = """
# Incident Postmortem: {title}

**Date:** {date}  
**Severity:** {severity}  
**Duration:** {duration}  
**Author:** {author}  

---

## Summary

{summary}

## Impact

{impact}

## Timeline

{timeline}

## Root Cause

{root_cause}

## Contributing Factors

{contributing_factors}

## What Went Well

{what_went_well}

## What Could Be Improved

{improvements}

## Action Items

{action_items}

## Lessons Learned

{lessons}

---

*Generated with DevOps Sentinel AI. Review and edit before sharing.*
"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
    
    async def generate(
        self,
        incident: Dict,
        events: List[Dict],
        resolution: Optional[str] = None
    ) -> Dict:
        """
        Generate postmortem from incident data
        
        Args:
            incident: Incident record
            events: Timeline events
            resolution: Optional resolution notes
        
        Returns:
            Generated postmortem with sections
        """
        # Extract key information
        title = incident.get('title', 'Untitled Incident')
        severity = incident.get('severity', 'P2')
        service = incident.get('service_name', 'Unknown')
        description = incident.get('description', '')
        
        # Calculate duration
        start = incident.get('detected_at')
        end = incident.get('resolved_at')
        duration = self._calculate_duration(start, end)
        
        # Build timeline
        timeline = self._format_timeline(events)
        
        # Generate AI sections (or use templates if no AI)
        if self.ai_client:
            sections = await self._generate_with_ai(
                incident, events, resolution
            )
        else:
            sections = self._generate_template_sections(
                incident, events, resolution
            )
        
        # Compile postmortem
        postmortem = self.TEMPLATE.format(
            title=title,
            date=datetime.utcnow().strftime('%Y-%m-%d'),
            severity=severity,
            duration=duration,
            author='DevOps Sentinel AI',
            summary=sections.get('summary', 'N/A'),
            impact=sections.get('impact', 'N/A'),
            timeline=timeline,
            root_cause=sections.get('root_cause', 'N/A'),
            contributing_factors=sections.get('contributing_factors', 'N/A'),
            what_went_well=sections.get('what_went_well', 'N/A'),
            improvements=sections.get('improvements', 'N/A'),
            action_items=sections.get('action_items', 'N/A'),
            lessons=sections.get('lessons', 'N/A')
        )
        
        return {
            'markdown': postmortem,
            'sections': sections,
            'incident_id': incident.get('id'),
            'generated_at': datetime.utcnow().isoformat(),
            'status': 'draft'
        }
    
    async def _generate_with_ai(
        self,
        incident: Dict,
        events: List[Dict],
        resolution: Optional[str]
    ) -> Dict:
        """Generate sections using AI"""
        if not LANGCHAIN_AVAILABLE:
            return self._generate_template_sections(incident, events, resolution)

        prompt = self._construct_prompt(incident, events, resolution)

        try:
            messages = [
                SystemMessage(content="You are an expert Site Reliability Engineer (SRE). Your task is to generate a comprehensive, blameless incident postmortem based on the provided incident details and timeline."),
                HumanMessage(content=prompt)
            ]

            response = await self.ai_client.ainvoke(messages)
            content = response.content

            # Attempt to parse JSON
            # Sometimes LLMs wrap JSON in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].strip()

            return json.loads(content)

        except Exception as e:
            logging.error(f"Error generating AI postmortem: {e}")
            # Fallback to template
            return self._generate_template_sections(incident, events, resolution)

    def _construct_prompt(self, incident: Dict, events: List[Dict], resolution: Optional[str]) -> str:
        """Construct the prompt for the AI."""
        service = incident.get('service_name', 'Unknown Service')
        title = incident.get('title', 'Untitled Incident')
        severity = incident.get('severity', 'Unknown')
        description = incident.get('description', 'No description provided.')

        # Fallback to incident resolution if not provided
        resolution_text = resolution or incident.get('resolution_notes') or 'None'

        events_str = "\n".join([f"- {e.get('timestamp', 'Unknown Time')}: {e.get('description', 'Event')}" for e in events])

        return f"""
Please generate a postmortem for the following incident in JSON format.

**Incident Details:**
- Service: {service}
- Title: {title}
- Severity: {severity}
- Description: {description}
- Resolution Notes: {resolution_text}

**Timeline:**
{events_str}

**Requirements:**
1. Be blameless. Focus on systems and processes, not individuals.
2. Be professional and concise.
3. Provide the output as a valid JSON object with the following keys:
   - "summary": A brief summary of the incident.
   - "impact": The impact on users and the business.
   - "root_cause": The technical root cause.
   - "contributing_factors": Factors that contributed to the incident.
   - "what_went_well": Positive aspects of the response.
   - "improvements": Areas for improvement.
   - "action_items": A markdown table of action items (Priority, Action, Owner, Due).
   - "lessons": Key lessons learned.

**JSON Output:**
"""

    def _generate_template_sections(
        self,
        incident: Dict,
        events: List[Dict],
        resolution: Optional[str]
    ) -> Dict:
        """Generate sections using templates (no AI)"""
        service = incident.get('service_name', 'the service')
        title = incident.get('title', 'the incident')
        severity = incident.get('severity', 'P2')
        description = incident.get('description', '')
        
        # Summary
        summary = (
            f"On {datetime.utcnow().strftime('%B %d, %Y')}, {service} experienced "
            f"a {severity} incident: {title}. "
            f"The incident was detected by automated monitoring and "
            f"resolved through {'the following actions: ' + resolution if resolution else 'standard remediation procedures'}."
        )
        
        # Impact (estimate based on severity)
        impact_levels = {
            'P0': 'Complete service outage affecting all users. Critical business functions unavailable.',
            'P1': 'Major degradation affecting significant portion of users. Key features unavailable.',
            'P2': 'Partial degradation affecting some users. Non-critical features impacted.',
            'P3': 'Minor issue with limited user impact. Workarounds available.'
        }
        impact = impact_levels.get(severity, impact_levels['P2'])
        
        # Root cause
        root_cause = (
            description if description else
            "Root cause is under investigation. Initial analysis suggests "
            "infrastructure-related issues that triggered the monitoring alerts."
        )
        
        # Contributing factors
        contributing_factors = (
            "- Recent changes in system configuration\n"
            "- Increased traffic patterns\n"
            "- Dependencies on external services"
        )
        
        # What went well
        what_went_well = (
            "- Monitoring detected the issue quickly\n"
            "- On-call engineer responded promptly\n"
            "- Communication channels worked effectively\n"
            "- Rollback procedures were documented"
        )
        
        # Improvements
        improvements = (
            "- Detection time could be reduced with more granular alerting\n"
            "- Runbook could be more detailed for this scenario\n"
            "- Consider adding automated remediation"
        )
        
        # Action items
        action_items = (
            "| Priority | Action | Owner | Due |\n"
            "|----------|--------|-------|-----|\n"
            "| High | Review and update runbook | TBD | +7 days |\n"
            "| Medium | Add additional monitoring | TBD | +14 days |\n"
            "| Medium | Conduct team retrospective | TBD | +7 days |\n"
            "| Low | Document lessons learned | TBD | +21 days |"
        )
        
        # Lessons
        lessons = (
            "- Importance of comprehensive monitoring coverage\n"
            "- Value of documented runbooks for rapid response\n"
            "- Need for regular review of incident response procedures"
        )
        
        return {
            'summary': summary,
            'impact': impact,
            'root_cause': root_cause,
            'contributing_factors': contributing_factors,
            'what_went_well': what_went_well,
            'improvements': improvements,
            'action_items': action_items,
            'lessons': lessons
        }
    
    def _format_timeline(self, events: List[Dict]) -> str:
        """Format events into timeline"""
        if not events:
            return "| Time | Event |\n|------|-------|\n| N/A | No events recorded |"
        
        lines = ["| Time | Event |", "|------|-------|"]
        
        for event in events:
            time = event.get('timestamp', 'Unknown')
            if isinstance(time, str) and 'T' in time:
                time = time.split('T')[1][:8]  # Extract time portion
            
            description = event.get('description', event.get('type', 'Event'))
            lines.append(f"| {time} | {description[:80]} |")
        
        return "\n".join(lines)
    
    def _calculate_duration(
        self,
        start: Optional[str],
        end: Optional[str]
    ) -> str:
        """Calculate incident duration"""
        if not start or not end:
            return "Unknown"
        
        try:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            
            duration = end_dt - start_dt
            minutes = int(duration.total_seconds() / 60)
            
            if minutes < 60:
                return f"{minutes} minutes"
            
            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h {mins}m"
            
        except:
            return "Unknown"
    
    def enforce_blameless(self, text: str) -> str:
        """
        Remove blameful language from text
        
        Replaces phrases like "X caused" with "the change resulted in"
        """
        replacements = [
            (r'\b(\w+) caused\b', 'a change resulted in'),
            (r'\b(\w+) broke\b', 'an issue occurred in'),
            (r'\b(\w+)\'s fault\b', 'a contributing factor'),
            (r'\bfailed to\b', 'did not'),
            (r'\bshould have\b', 'could have'),
            (r'\bbad code\b', 'an issue in the code'),
            (r'\bstupid\b', 'unexpected'),
            (r'\bcareless\b', 'inadvertent'),
        ]
        
        import re
        result = text
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result


# FastAPI routes
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/postmortems", tags=["postmortems"])


class GenerateRequest(BaseModel):
    incident_id: str
    resolution_notes: Optional[str] = None


@router.post("/generate")
async def generate_postmortem(request: GenerateRequest, supabase=None):
    """Generate AI postmortem for an incident"""
    # Get incident
    result = await supabase.table('incidents').select(
        '*'
    ).eq('id', request.incident_id).execute()
    
    if not result.data:
        raise HTTPException(404, "Incident not found")
    
    incident = result.data[0]
    
    # Get events
    events_result = await supabase.table('incident_events').select(
        '*'
    ).eq('incident_id', request.incident_id).order('timestamp').execute()
    
    events = events_result.data or []
    
    # Generate postmortem
    generator = PostmortemGenerator()
    postmortem = await generator.generate(
        incident=incident,
        events=events,
        resolution=request.resolution_notes
    )
    
    # Store
    await supabase.table('postmortems').insert({
        'incident_id': request.incident_id,
        'content': postmortem['markdown'],
        'sections': postmortem['sections'],
        'status': 'draft',
        'created_at': datetime.utcnow().isoformat()
    }).execute()
    
    return postmortem


@router.get("/{incident_id}")
async def get_postmortem(incident_id: str, supabase=None):
    """Get postmortem for an incident"""
    result = await supabase.table('postmortems').select(
        '*'
    ).eq('incident_id', incident_id).order('created_at', desc=True).limit(1).execute()
    
    if not result.data:
        raise HTTPException(404, "Postmortem not found")
    
    return result.data[0]
