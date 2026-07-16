from __future__ import annotations

import json
from typing import Any

from services.ai_copilot import providers


def test_call_llm_records_metadata_only_event_for_provider_failure(monkeypatch):
    calls: list[dict[str, Any]] = []

    def _append_operator_event(**kwargs):
        calls.append(kwargs)
        return {"event_id": "evt-ai-1", "path": "/tmp/operator_events.jsonl"}

    monkeypatch.setenv("CBP_COPILOT_PROVIDER", "unsupported_provider")
    monkeypatch.setenv("CBP_COPILOT_MODEL", "model-x")
    monkeypatch.setattr(providers, "append_operator_event", _append_operator_event)

    result = providers.call_llm(
        system="SYSTEM_SECRET_PROMPT",
        user="USER_INCIDENT_CONTEXT_SECRET",
    )

    assert result["ok"] is False
    assert result["operator_event"] == {
        "ok": True,
        "event_id": "evt-ai-1",
        "path": "/tmp/operator_events.jsonl",
    }
    assert len(calls) == 1
    event = calls[0]
    assert event["actor"] == "system"
    assert event["action"] == "ai_copilot_external_provider_call"
    assert event["target"] == "unsupported_provider"
    assert event["result"] == "failed"
    assert event["source"] == "services.ai_copilot.providers"
    assert event["pre_state"] == {
        "provider": "unsupported_provider",
        "model": "model-x",
        "system_prompt_chars": len("SYSTEM_SECRET_PROMPT"),
        "user_prompt_chars": len("USER_INCIDENT_CONTEXT_SECRET"),
    }
    assert event["post_state"]["error_present"] is True
    assert event["extra"] == {"prompt_payload_logged": False}

    serialized = json.dumps(event, sort_keys=True)
    assert "SYSTEM_SECRET_PROMPT" not in serialized
    assert "USER_INCIDENT_CONTEXT_SECRET" not in serialized


def test_call_llm_operator_event_failure_is_explicit(monkeypatch):
    def _append_operator_event(**kwargs):
        raise PermissionError("journal read-only")

    monkeypatch.setenv("CBP_COPILOT_PROVIDER", "unsupported_provider")
    monkeypatch.setenv("CBP_COPILOT_MODEL", "model-x")
    monkeypatch.setattr(providers, "append_operator_event", _append_operator_event)

    result = providers.call_llm(system="system prompt", user="user prompt")

    assert result["ok"] is False
    assert result["operator_event"] == {
        "ok": False,
        "reason": "operator_event_write_failed:PermissionError",
    }


def test_call_llm_provider_allowlist_blocks_before_sdk_path(monkeypatch):
    calls: list[dict[str, Any]] = []

    def _append_operator_event(**kwargs):
        calls.append(kwargs)
        return {"event_id": "evt-ai-policy-1", "path": "/tmp/operator_events.jsonl"}

    monkeypatch.setenv("CBP_COPILOT_PROVIDER", "openai")
    monkeypatch.setenv("CBP_COPILOT_MODEL", "gpt-test")
    monkeypatch.setenv("CBP_COPILOT_ALLOWED_PROVIDERS", "anthropic")
    monkeypatch.delenv("CBP_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(providers, "append_operator_event", _append_operator_event)

    result = providers.call_llm(system="system prompt", user="user prompt")

    assert result["ok"] is False
    assert result["error"] == "provider_not_allowed:openai"
    assert result["provider_policy"] == {
        "ok": False,
        "provider": "openai",
        "reason": "provider_not_allowed:openai",
        "allowed_providers": ["anthropic"],
        "policy_source": "env",
    }
    assert result["operator_event"]["ok"] is True
    event = calls[0]
    assert event["action"] == "ai_copilot_external_provider_call"
    assert event["target"] == "openai"
    assert event["result"] == "failed"
    assert event["post_state"]["error_type"] == "provider_not_allowed"


def test_call_llm_corrupt_provider_allowlist_blocks(monkeypatch):
    calls: list[dict[str, Any]] = []

    def _append_operator_event(**kwargs):
        calls.append(kwargs)
        return {"event_id": "evt-ai-policy-2", "path": "/tmp/operator_events.jsonl"}

    monkeypatch.setenv("CBP_COPILOT_PROVIDER", "anthropic")
    monkeypatch.setenv("CBP_COPILOT_MODEL", "claude-test")
    monkeypatch.setenv("CBP_COPILOT_ALLOWED_PROVIDERS", "anthropic,unknown")
    monkeypatch.setattr(providers, "append_operator_event", _append_operator_event)

    result = providers.call_llm(system="system prompt", user="user prompt")

    assert result["ok"] is False
    assert result["error"] == "invalid_provider_allowlist:unsupported_provider_in_allowlist:unknown"
    assert result["operator_event"]["ok"] is True
    assert calls[0]["post_state"]["error_type"] == "invalid_provider_allowlist"


def test_provider_operator_event_success_metadata(monkeypatch):
    calls: list[dict[str, Any]] = []

    def _append_operator_event(**kwargs):
        calls.append(kwargs)
        return {"event_id": "evt-ai-2", "path": "/tmp/operator_events.jsonl"}

    monkeypatch.setattr(providers, "append_operator_event", _append_operator_event)

    result = providers._with_operator_event(
        provider="openai",
        model="gpt-test",
        system="SYS_SECRET",
        user="USER_SECRET",
        outcome={"ok": True, "text": "summary", "provider": "openai", "model": "gpt-test"},
    )

    assert result["ok"] is True
    assert result["operator_event"]["ok"] is True
    event = calls[0]
    assert event["result"] == "success"
    assert event["post_state"] == {
        "ok": True,
        "provider": "openai",
        "model": "gpt-test",
        "error_present": False,
        "error_type": "",
    }
    serialized = json.dumps(event, sort_keys=True)
    assert "SYS_SECRET" not in serialized
    assert "USER_SECRET" not in serialized
