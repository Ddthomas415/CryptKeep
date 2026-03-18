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

from shared import tools  # noqa: E402


def test_tool_definitions_expose_read_only_functions() -> None:
    names = [item["name"] for item in tools.OPENAI_TOOL_DEFINITIONS if item.get("type") == "function"]
    assert names == [
        "get_market_snapshot",
        "get_risk_summary",
        "get_operations_summary",
        "get_signal_summary",
        "get_crypto_edge_report",
    ]


def test_get_market_snapshot_falls_back_without_service(monkeypatch) -> None:
    async def fake_request_json(*args, **kwargs):
        return None

    monkeypatch.setattr(tools, "_request_json", fake_request_json)
    payload = asyncio.run(tools.get_market_snapshot("SOL"))

    assert payload["asset"] == "SOL"
    assert payload["source"] == "fallback"
    assert payload["ok"] is True


def test_get_risk_summary_falls_back_without_service(monkeypatch) -> None:
    async def fake_request_json(*args, **kwargs):
        return None

    monkeypatch.setattr(tools, "_request_json", fake_request_json)
    payload = asyncio.run(tools.get_risk_summary())

    assert payload["execution_mode"] == "DISABLED"
    assert payload["gate"] == "NO_TRADING"
    assert payload["allow_trading"] is False


def test_get_signal_summary_falls_back_without_service(monkeypatch) -> None:
    async def fake_request_json(*args, **kwargs):
        return None

    monkeypatch.setattr(tools, "_request_json", fake_request_json)
    payload = asyncio.run(tools.get_signal_summary("BTC"))

    assert payload["asset"] == "BTC"
    assert payload["source"] == "fallback"
    assert payload["counts"]["recent_news"] == 1
    assert isinstance(payload["intelligence"], dict)
    assert payload["intelligence"]["regime"] == "trend_up"
    assert payload["intelligence"]["category"]


def test_get_signal_summary_includes_intelligence_for_live_payload(monkeypatch) -> None:
    async def fake_request_json(method, url, *, params=None, payload=None):
        if "memory/retrieve" in url:
            return {
                "market": {"latest_price": 187.42, "change_pct": 6.9, "window_samples": 12},
                "recent_news": [{"title": "Fresh ecosystem catalyst", "source": "feed"}],
                "past_context": [{"title": "Prior continuation setup", "source": "archive"}],
                "future_context": [{"title": "Governance milestone ahead", "source": "calendar"}],
                "vector_matches": [],
            }
        if "market/latest" in url:
            return {
                "tick": {
                    "symbol": "SOL/USDT",
                    "price": 187.42,
                    "bid": 187.3,
                    "ask": 187.54,
                    "volume": 412000.0,
                    "exchange": "binance",
                    "source": "market-data",
                    "event_ts": "2026-03-12T10:00:00Z",
                }
            }
        return None

    monkeypatch.setattr(tools, "_request_json", fake_request_json)
    payload = asyncio.run(tools.get_signal_summary("SOL"))

    assert payload["asset"] == "SOL"
    assert payload["source"] == "memory-retrieval"
    assert payload["intelligence"]["regime"] == "trend_up"
    assert payload["intelligence"]["opportunity_score"] > 0.0


def test_execute_tool_call_rejects_unknown_tool() -> None:
    payload = asyncio.run(tools.execute_tool_call("nope", {}))
    assert payload == {"ok": False, "error": "unsupported_tool:nope"}


def test_get_crypto_edge_report_falls_back_without_store(monkeypatch) -> None:
    original_import = __import__

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "storage.crypto_edge_store_sqlite":
            raise ImportError("store unavailable")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", fake_import)
    payload = asyncio.run(tools.get_crypto_edge_report())

    assert payload["ok"] is False
    assert payload["research_only"] is True
    assert payload["execution_enabled"] is False
    assert payload["reason"] == "store_import_failed:ImportError"
