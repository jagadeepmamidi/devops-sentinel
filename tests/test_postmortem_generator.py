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
    assert result["source"] == "fallback"
    assert result["fallback_reason"] is None
    assert "Payments API" in result["markdown"]
    assert "Rolled back the failing deploy." in result["markdown"]
    assert "not an AI-authored report" in result["markdown"]
    assert "DevOps Sentinel AI" not in result["markdown"]


@pytest.mark.asyncio
async def test_postmortem_falls_back_when_llm_raises(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    async def boom(*_args, **_kwargs):
        raise RuntimeError("LLM HTTP 402: credits")

    monkeypatch.setattr(PostmortemGenerator, "_generate_with_ai", boom)
    result = await PostmortemGenerator().generate(
        {"id": "inc-2", "severity": "high", "service_name": "api"},
        [],
    )

    assert result["source"] == "fallback"
    assert "402" in (result["fallback_reason"] or "")
    assert "LLM call failed" in result["markdown"]
    assert "not an AI-authored report" in result["markdown"]
