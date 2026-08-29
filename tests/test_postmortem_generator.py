import pytest

from sentinel.core.postmortem_generator import PostmortemGenerator


@pytest.mark.asyncio
async def test_postmortem_generator_creates_markdown_without_ai(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    generator = PostmortemGenerator()

    result = await generator.generate(
        incident={
            "id": "inc-123",
            "title": "API outage",
            "severity": "high",
            "service_name": "Payments API",
            "description": "HTTP 503 from upstream",
            "detected_at": "2026-03-01T10:00:00+00:00",
            "resolved_at": "2026-03-01T10:15:00+00:00",
        },
        events=[
            {"timestamp": "2026-03-01T10:00:00+00:00", "description": "Incident detected"},
            {"timestamp": "2026-03-01T10:15:00+00:00", "description": "Service recovered"},
        ],
        resolution="Rolled back the failing deploy.",
    )

    assert result["status"] == "draft"
    assert "Payments API" in result["markdown"]
    assert "Rolled back the failing deploy." in result["markdown"]
