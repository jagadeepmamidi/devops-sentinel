"""Postmortem markdown from incident evidence. Uses an LLM when a key is set; otherwise a labeled template."""

from datetime import datetime, timezone
import json
import os

import httpx


class PostmortemGenerator:
    """Build a draft postmortem from stored incident data."""

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

*{footer}*
"""

    def __init__(self, ai_client=None):
        self.ai_client = ai_client

    async def generate(
        self, incident: dict, events: list[dict], resolution: str | None = None
    ) -> dict:
        """
        Generate postmortem from incident data

        Args:
            incident: Incident record
            events: Timeline events
            resolution: Optional resolution notes

        Returns:
            Generated postmortem with sections
        """
        title = (
            incident.get("title")
            or incident.get("error_message")
            or (incident.get("services") or {}).get("name")
            or incident.get("service_name")
            or "Untitled Incident"
        )
        severity = incident.get("severity", "P2")
        incident = {
            **incident,
            "title": title,
            "service_name": incident.get("service_name")
            or (incident.get("services") or {}).get("name")
            or "the service",
            "description": incident.get("description") or incident.get("error_message") or "",
        }

        # Calculate duration
        start = incident.get("detected_at")
        end = incident.get("resolved_at")
        duration = self._calculate_duration(start, end)

        # Build timeline
        timeline = self._format_timeline(events)

        source = "fallback"
        fallback_reason = None
        if self.ai_client or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY"):
            try:
                sections = await self._generate_with_ai(incident, events, resolution)
                source = "ai"
            except Exception as error:  # noqa: BLE001 — fall back for any provider failure
                fallback_reason = str(error)
                sections = self._generate_template_sections(incident, events, resolution)
        else:
            sections = self._generate_template_sections(incident, events, resolution)

        postmortem = self.TEMPLATE.format(
            title=title,
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            severity=severity,
            duration=duration,
            author="DevOps Sentinel",
            summary=sections["summary"],
            impact=sections["impact"],
            timeline=timeline,
            root_cause=sections["root_cause"],
            contributing_factors=sections["contributing_factors"],
            what_went_well=sections["what_went_well"],
            improvements=sections["improvements"],
            action_items=sections["action_items"],
            lessons=sections["lessons"],
            footer=self._source_footer(source, fallback_reason),
        )

        return {
            "markdown": postmortem,
            "sections": sections,
            "incident_id": incident.get("id"),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "draft",
            "source": source,
            "fallback_reason": fallback_reason,
        }

    @staticmethod
    def _source_footer(source: str, fallback_reason: str | None) -> str:
        if source == "ai":
            return "Generated with an LLM. Review and edit before sharing."
        if fallback_reason:
            reason = fallback_reason.replace("\n", " ").strip()[:180]
            return (
                "Template postmortem — the LLM call failed, so this is not an AI-authored report. "
                f"Reason: {reason}"
            )
        return (
            "Template postmortem — no LLM key configured. This is not an AI-authored report."
        )

    async def _generate_with_ai(
        self, incident: dict, events: list[dict], resolution: str | None
    ) -> dict:
        """Generate sections using OpenRouter or OpenAI. Raises on provider failure."""
        if self.ai_client and hasattr(self.ai_client, "generate_sections"):
            return await self.ai_client.generate_sections(incident, events, resolution)

        openrouter_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
        openai_key = (os.getenv("OPENAI_API_KEY") or "").strip()
        if not openrouter_key and not openai_key:
            raise RuntimeError("No LLM API key configured")

        if openrouter_key:
            base_url = "https://openrouter.ai/api/v1/chat/completions"
            api_key = openrouter_key
            model = os.getenv("DEFAULT_MODEL", "openai/gpt-4o-mini")
        else:
            base_url = "https://api.openai.com/v1/chat/completions"
            api_key = openai_key
            model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

        try:
            max_tokens = int(os.getenv("SENTINEL_LLM_MAX_TOKENS", "1024"))
        except ValueError:
            max_tokens = 1024

        timeline = self._format_timeline(events)
        prompt = (
            "You are an SRE writing a blameless postmortem. Return ONLY a JSON object with keys: "
            "summary, impact, root_cause, contributing_factors, what_went_well, "
            "improvements, action_items, lessons. Values are markdown strings. No markdown fences.\n"
            f"Service: {incident.get('service_name')}\n"
            f"Severity: {incident.get('severity')}\n"
            f"Error: {incident.get('error_message') or incident.get('description')}\n"
            f"Resolution: {resolution or 'n/a'}\n"
            f"Timeline:\n{timeline}\n"
        )
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if openrouter_key:
            headers["HTTP-Referer"] = "https://github.com/jagadeepmamidi/devops-sentinel"
            headers["X-Title"] = "DevOps Sentinel"
        payload = {
            "model": model,
            "temperature": 0,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        }
        with httpx.Client(timeout=45) as client:
            response = client.post(base_url, headers=headers, json=payload)
        if response.status_code >= 400:
            raise RuntimeError(f"LLM HTTP {response.status_code}: {response.text[:300]}")
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("LLM response was empty")
        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end == -1:
            raise RuntimeError("LLM response was not JSON")
        parsed = json.loads(content[start : end + 1])
        template = self._generate_template_sections(incident, events, resolution)
        for key in template:
            value = parsed.get(key)
            if isinstance(value, str) and value.strip():
                template[key] = value.strip()
        return template

    def _generate_template_sections(
        self, incident: dict, events: list[dict], resolution: str | None
    ) -> dict:
        """Generate sections using templates (no AI)"""
        service = incident.get("service_name", "the service")
        title = incident.get("title", "the incident")
        severity = incident.get("severity", "P2")
        description = incident.get("description", "")

        # Summary
        summary = (
            f"On {datetime.now(timezone.utc).strftime('%B %d, %Y')}, {service} experienced "
            f"a {severity} incident: {title}. "
            f"The incident was detected by automated monitoring and "
            f"resolved through {'the following actions: ' + resolution if resolution else 'standard remediation procedures'}."
        )

        # Impact (estimate based on severity)
        impact_levels = {
            "critical": "Complete service outage affecting all users. Critical business functions unavailable.",
            "high": "Major degradation affecting significant portion of users. Key features unavailable.",
            "medium": "Partial degradation affecting some users. Non-critical features impacted.",
            "low": "Minor issue with limited user impact. Workarounds available.",
            "P0": "Complete service outage affecting all users. Critical business functions unavailable.",
            "P1": "Major degradation affecting significant portion of users. Key features unavailable.",
            "P2": "Partial degradation affecting some users. Non-critical features impacted.",
            "P3": "Minor issue with limited user impact. Workarounds available.",
        }
        impact = impact_levels.get(severity, impact_levels["medium"])

        # Root cause
        root_cause = (
            description
            if description
            else "Root cause is under investigation. Initial analysis suggests "
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
            "summary": summary,
            "impact": impact,
            "root_cause": root_cause,
            "contributing_factors": contributing_factors,
            "what_went_well": what_went_well,
            "improvements": improvements,
            "action_items": action_items,
            "lessons": lessons,
        }

    def _format_timeline(self, events: list[dict]) -> str:
        """Format events into timeline"""
        if not events:
            return "| Time | Event |\n|------|-------|\n| N/A | No events recorded |"

        lines = ["| Time | Event |", "|------|-------|"]

        for event in events:
            time = event.get("timestamp") or event.get("created_at") or "Unknown"
            if isinstance(time, str) and "T" in time:
                time = time.split("T")[1][:8]  # Extract time portion

            description = event.get("description", event.get("type", "Event"))
            lines.append(f"| {time} | {description[:80]} |")

        return "\n".join(lines)

    def _calculate_duration(self, start: str | None, end: str | None) -> str:
        """Calculate incident duration"""
        if not start or not end:
            return "Unknown"

        try:
            start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))

            duration = end_dt - start_dt
            minutes = int(duration.total_seconds() / 60)

            if minutes < 60:
                return f"{minutes} minutes"

            hours = minutes // 60
            mins = minutes % 60
            return f"{hours}h {mins}m"

        except Exception:
            return "Unknown"

    def enforce_blameless(self, text: str) -> str:
        """
        Remove blameful language from text

        Replaces phrases like "X caused" with "the change resulted in"
        """
        replacements = [
            (r"\b(\w+) caused\b", "a change resulted in"),
            (r"\b(\w+) broke\b", "an issue occurred in"),
            (r"\b(\w+)\'s fault\b", "a contributing factor"),
            (r"\bfailed to\b", "did not"),
            (r"\bshould have\b", "could have"),
            (r"\bbad code\b", "an issue in the code"),
            (r"\bstupid\b", "unexpected"),
            (r"\bcareless\b", "inadvertent"),
        ]

        import re

        result = text
        for pattern, replacement in replacements:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result
