from __future__ import annotations

import asyncio
import sys
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
