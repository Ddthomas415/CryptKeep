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

import orchestrator.main as orchestrator  # noqa: E402
from shared.models import ExplainRequest  # noqa: E402


async def _noop_audit(*args, **kwargs) -> None:
    return None


def test_explain_endpoint_uses_safe_fallback_shape(monkeypatch) -> None:
    class DisabledClient:
        enabled = False

    async def fake_market(asset: str) -> dict:
        return {
            "ok": True,
            "asset": asset,
            "symbol": f"{asset}/USDT",
            "price": 187.42,
            "bid": 187.3,
            "ask": 187.54,
            "volume": 412000.0,
            "exchange": "binance",
            "as_of": "2026-03-12T12:00:00Z",
            "source": "fallback",
        }

    async def fake_signal(asset: str) -> dict:
        return {
            "asset": asset,
            "market": {"ok": True, "latest_price": 187.42, "change_pct": 6.9, "window_samples": 14},
            "recent_news": [{"title": f"Fresh ecosystem headline for {asset}", "source": "newsapi"}],
            "past_context": [{"title": f"Past precedent for {asset}", "source": "archive"}],
            "future_context": [{"title": f"Future catalyst for {asset}", "source": "calendar"}],
            "vector_matches": [],
            "counts": {"recent_news": 1, "past_context": 1, "future_context": 1, "vector_matches": 0},
            "source": "fallback",
        }

    async def fake_risk() -> dict:
        return {"execution_mode": "DISABLED", "gate": "NO_TRADING", "allow_trading": False}

    monkeypatch.setattr(orchestrator, "llm_client", DisabledClient())
    monkeypatch.setattr(orchestrator, "get_market_snapshot", fake_market)
    monkeypatch.setattr(orchestrator, "get_signal_summary", fake_signal)
    monkeypatch.setattr(orchestrator, "get_risk_summary", fake_risk)
    monkeypatch.setattr(orchestrator, "emit_audit_event", _noop_audit)

    payload = asyncio.run(
        orchestrator.explain(
            ExplainRequest(asset="SOL", question="Why is SOL moving?", lookback_minutes=60)
        )
    )
    assert payload["asset"] == "SOL"
    assert payload["past_precedent"] == payload["relevant_past_precedent"]
    assert payload["execution_disabled"] is True
    assert payload["execution"]["enabled"] is False
    assert payload["risk_note"] == "Research only. Execution disabled."
    assert payload["assistant_status"]["provider"] == "fallback"
    assert isinstance(payload["evidence"], list) and payload["evidence"]


def test_explain_endpoint_uses_openai_tool_reasoning_loop(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    class EnabledClient:
        enabled = True

        async def create_response(self, **kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                return SimpleNamespace(
                    id="resp_1",
                    output=[
                        SimpleNamespace(
                            type="function_call",
                            name="get_market_snapshot",
                            arguments='{"asset":"SOL"}',
                            call_id="call_market",
                        ),
                        SimpleNamespace(
                            type="function_call",
                            name="get_risk_summary",
                            arguments="{}",
                            call_id="call_risk",
                        ),
                    ],
                    output_text="",
                )
            return SimpleNamespace(
                id="resp_2",
                output=[],
                output_text=(
                    '{"current_cause":"SOL is firming on spot demand.",'
                    '"past_precedent":"Prior ecosystem rotations showed similar accumulation.",'
                    '"future_catalyst":"Upcoming ecosystem milestones could sustain attention.",'
                    '"confidence":0.81}'
                ),
            )

    async def fake_execute_tool_call(name: str, raw_arguments):
        if name == "get_market_snapshot":
            return {
                "ok": True,
                "asset": "SOL",
                "symbol": "SOL/USDT",
                "price": 187.42,
                "bid": 187.3,
                "ask": 187.54,
                "volume": 412000.0,
                "exchange": "binance",
                "as_of": "2026-03-12T12:00:00Z",
                "source": "market-data",
            }
        if name == "get_risk_summary":
            return {"execution_mode": "DISABLED", "gate": "NO_TRADING", "allow_trading": False}
        return {}

    async def fake_market(asset: str) -> dict:
        return {
            "ok": True,
            "asset": asset,
            "symbol": f"{asset}/USDT",
            "price": 187.42,
            "bid": 187.3,
            "ask": 187.54,
            "volume": 412000.0,
            "exchange": "binance",
            "as_of": "2026-03-12T12:00:00Z",
            "source": "market-data",
        }

    async def fake_signal(asset: str) -> dict:
        return {
            "asset": asset,
            "market": {"ok": True, "latest_price": 187.42, "change_pct": 6.9, "window_samples": 14},
            "recent_news": [{"title": f"Fresh ecosystem headline for {asset}", "source": "newsapi"}],
            "past_context": [{"title": f"Past precedent for {asset}", "source": "archive"}],
            "future_context": [{"title": f"Future catalyst for {asset}", "source": "calendar"}],
            "vector_matches": [],
            "counts": {"recent_news": 1, "past_context": 1, "future_context": 1, "vector_matches": 0},
            "source": "memory-retrieval",
        }

    async def fake_risk() -> dict:
        return {"execution_mode": "DISABLED", "gate": "NO_TRADING", "allow_trading": False}

    monkeypatch.setattr(orchestrator, "llm_client", EnabledClient())
    monkeypatch.setattr(orchestrator, "execute_tool_call", fake_execute_tool_call)
    monkeypatch.setattr(orchestrator, "get_market_snapshot", fake_market)
    monkeypatch.setattr(orchestrator, "get_signal_summary", fake_signal)
    monkeypatch.setattr(orchestrator, "get_risk_summary", fake_risk)
    monkeypatch.setattr(orchestrator, "emit_audit_event", _noop_audit)

    payload = asyncio.run(
        orchestrator.explain(
            ExplainRequest(asset="SOL", question="Why is SOL moving?", lookback_minutes=60)
        )
    )

    assert payload["assistant_status"]["provider"] == "openai"
    assert payload["current_cause"] == "SOL is firming on spot demand."
    assert payload["confidence_score"] == 0.81
    assert len(payload["evidence"]) >= 1
    assert len(calls) == 2
    assert calls[0]["instructions"] == calls[1]["instructions"]
    assert calls[1]["previous_response_id"] == "resp_1"
