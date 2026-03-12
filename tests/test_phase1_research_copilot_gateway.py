from __future__ import annotations

import asyncio
import sys
from types import SimpleNamespace
from types import ModuleType
from pathlib import Path


PHASE1_ROOT = Path(__file__).resolve().parents[1] / "phase1_research_copilot"
if str(PHASE1_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE1_ROOT))

if "httpx" not in sys.modules:
    httpx_stub = ModuleType("httpx")

    class _AsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False

        async def request(self, *args, **kwargs):
            raise RuntimeError("httpx stub should not be called in tests")

        async def post(self, *args, **kwargs):
            raise RuntimeError("httpx stub should not be called in tests")

        async def get(self, *args, **kwargs):
            raise RuntimeError("httpx stub should not be called in tests")

    httpx_stub.AsyncClient = _AsyncClient
    sys.modules["httpx"] = httpx_stub

import gateway.main as gateway  # noqa: E402


async def _noop_audit(*args, **kwargs) -> None:
    return None


def test_chat_endpoint_adds_assistant_response(monkeypatch) -> None:
    async def fake_retry_async(fn, **kwargs):
        return {
            "ok": True,
            "asset": "BTC",
            "question": "Why is BTC moving?",
            "current_cause": "BTC is firming with strong spot support.",
            "past_precedent": "Past breakouts held when liquidity stayed firm.",
            "future_catalyst": "Macro data later this week could matter.",
            "confidence": 0.72,
            "risk_note": "Research only. Execution disabled.",
            "execution_disabled": True,
            "evidence": [],
        }

    async def fake_generate(payload):
        return "BTC is firming with strong spot support. Risk note: research only.", {
            "provider": "fallback",
            "model": None,
            "fallback": True,
        }

    monkeypatch.setattr(gateway, "retry_async", fake_retry_async)
    monkeypatch.setattr(gateway, "_generate_chat_response", fake_generate)
    monkeypatch.setattr(gateway, "emit_audit_event", _noop_audit)

    payload = asyncio.run(
        gateway.chat(
            gateway.ChatRequest(asset="BTC", question="Why is BTC moving?", lookback_minutes=60)
        )
    )
    assert payload["assistant_response"].startswith("BTC is firming")
    assert payload["chat_status"]["provider"] == "fallback"
    assert payload["asset"] == "BTC"
    assert payload["reasoning_summary"] == "Explain: Unknown\nChat: Fallback | fallback"


def test_chat_endpoint_falls_back_when_orchestrator_is_unavailable(monkeypatch) -> None:
    async def fake_retry_async(fn, **kwargs):
        raise RuntimeError("orchestrator unavailable")

    monkeypatch.setattr(gateway, "retry_async", fake_retry_async)
    monkeypatch.setattr(gateway, "emit_audit_event", _noop_audit)

    payload = asyncio.run(
        gateway.chat(
            gateway.ChatRequest(asset="ETH", question="Why is ETH moving?", lookback_minutes=60)
        )
    )

    assert payload["asset"] == "ETH"
    assert payload["execution_disabled"] is True
    assert payload["assistant_status"]["provider"] == "gateway_fallback"
    assert payload["chat_status"]["provider"] == "fallback"
    assert payload["chat_status"]["upstream_fallback"] is True
    assert payload["chat_status"]["upstream_reason"] == "RuntimeError"
    assert payload["assistant_response"].startswith("ETH:")
    assert (
        payload["reasoning_summary"]
        == "Explain: Gateway Fallback | fallback\nChat: Fallback | fallback | upstream RuntimeError"
    )


def test_generate_chat_response_uses_openai_when_enabled(monkeypatch) -> None:
    class EnabledClient:
        enabled = True

        async def create_response(self, **kwargs):
            return SimpleNamespace(output_text="BTC is firming on spot support. Risk note: research only.")

    monkeypatch.setattr(gateway, "llm_client", EnabledClient())

    text, status = asyncio.run(
        gateway._generate_chat_response(
            {
                "asset": "BTC",
                "question": "Why is BTC moving?",
                "current_cause": "BTC is firming on spot support.",
                "past_precedent": "Past breakouts held on stronger liquidity.",
                "future_catalyst": "Macro data later this week could matter.",
                "confidence": 0.72,
                "risk_note": "Research only. Execution disabled.",
                "execution_disabled": True,
            }
        )
    )

    assert text.startswith("BTC is firming")
    assert status == {
        "provider": "openai",
        "model": gateway.settings.openai_model,
        "fallback": False,
    }


def test_build_reasoning_summary_formats_explain_and_chat_status() -> None:
    summary = gateway._build_reasoning_summary(
        {"provider": "openai", "model": "gpt-4.1-mini", "fallback": False},
        {"provider": "fallback", "fallback": True, "upstream_fallback": True, "upstream_reason": "TimeoutError"},
    )

    assert summary == (
        "Explain: OpenAI | gpt-4.1-mini\n"
        "Chat: Fallback | fallback | upstream TimeoutError"
    )
