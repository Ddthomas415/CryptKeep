from __future__ import annotations

from services.ai_copilot.incident_analyst import analyze_incident, quick_health_check


def test_analyze_incident_uses_provider_layer(monkeypatch):
    monkeypatch.setattr(
        "services.ai_copilot.incident_analyst.collect_incident_context",
        lambda extra_notes="": "ctx-block",
    )
    monkeypatch.setattr(
        "services.ai_copilot.incident_analyst.call_llm",
        lambda **_: {
            "ok": True,
            "text": "System looks healthy.",
            "provider": "anthropic",
            "model": "claude-sonnet-test",
        },
    )

    result = analyze_incident(question="what is wrong?", extra_notes="none")

    assert result["ok"] is True
    assert result["analysis"] == "System looks healthy."
    assert result["provider"] == "anthropic"
    assert result["model"] == "claude-sonnet-test"
    assert result["context_chars"] == len("ctx-block")


def test_analyze_incident_surfaces_provider_error(monkeypatch):
    monkeypatch.setattr(
        "services.ai_copilot.incident_analyst.collect_incident_context",
        lambda extra_notes="": "ctx-block",
    )
    monkeypatch.setattr(
        "services.ai_copilot.incident_analyst.call_llm",
        lambda **_: {"ok": False, "error": "Missing API key", "provider": "anthropic", "model": "claude"},
    )

    result = analyze_incident(question="why", extra_notes="")

    assert result["ok"] is False
    assert result["error"] == "Missing API key"
    assert result["provider"] == "anthropic"
    assert result["model"] == "claude"


def test_quick_health_check_uses_standard_prompt(monkeypatch):
    captured: dict[str, str] = {}

    def _fake(question: str = "", extra_notes: str = ""):
        captured["question"] = question
        captured["extra_notes"] = extra_notes
        return {"ok": True}

    monkeypatch.setattr("services.ai_copilot.incident_analyst.analyze_incident", _fake)

    result = quick_health_check()

    assert result == {"ok": True}
    assert "brief health check" in captured["question"]
    assert captured["extra_notes"] == ""
