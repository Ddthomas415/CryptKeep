from __future__ import annotations

import importlib.util

import pytest


def _has_module(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


if not _has_module("phase1_research_copilot"):
    pytest.skip("phase1_research_copilot package not present in this repo checkout", allow_module_level=True)

if not _has_module("phase1_research_copilot.shared.tools"):
    pytest.skip("phase1_research_copilot.shared.tools surface not present in this repo checkout", allow_module_level=True)

import asyncio
import sys
from types import ModuleType
from pathlib import Path


PHASE1_ROOT = Path(__file__).resolve().parents[1] / "phase1_research_copilot"
if not PHASE1_ROOT.exists():
    pytest.skip("phase1_research_copilot sidecar not present", allow_module_level=True)

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

try:
    from phase1_research_copilot.shared import tools  # noqa: E402
except ModuleNotFoundError:
    pytest.skip("phase1_research_copilot module surface not present", allow_module_level=True)


def test_tool_definitions_expose_read_only_functions() -> None:
    names = [item["name"] for item in tools.OPENAI_TOOL_DEFINITIONS if item.get("type") == "function"]
    assert names == [
        "get_market_snapshot",
        "get_risk_summary",
        "get_operations_summary",
        "get_signal_summary",
        "get_crypto_edge_report",
        "get_latest_live_crypto_edge_snapshot",
        "get_crypto_edge_change_summary",
        "get_crypto_edge_staleness_summary",
        "get_crypto_edge_staleness_digest",
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


def test_get_crypto_edge_report_uses_dashboard_workspace(monkeypatch) -> None:
    from dashboard.services import crypto_edge_research

    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_workspace",
        lambda history_limit=5: {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": True,
            "data_origin_label": "Live Public",
            "freshness_summary": "Fresh",
            "provenance_rows": [{"theme": "funding", "source": "Live Public"}],
        },
    )

    payload = asyncio.run(tools.get_crypto_edge_report())

    assert payload["ok"] is True
    assert payload["data_origin_label"] == "Live Public"
    assert payload["freshness_summary"] == "Fresh"


def test_get_latest_live_crypto_edge_snapshot_uses_dashboard_loader(monkeypatch) -> None:
    from dashboard.services import crypto_edge_research

    monkeypatch.setattr(
        crypto_edge_research,
        "load_latest_live_crypto_edge_snapshot",
        lambda: {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": True,
            "has_live_data": True,
            "data_origin_label": "Live Public",
            "freshness_summary": "Recent",
            "summary_text": "Live Public snapshot shows funding bias long_pays.",
        },
    )

    payload = asyncio.run(tools.get_latest_live_crypto_edge_snapshot())

    assert payload["ok"] is True
    assert payload["has_live_data"] is True
    assert payload["data_origin_label"] == "Live Public"
    assert payload["freshness_summary"] == "Recent"


def test_get_crypto_edge_change_summary_uses_dashboard_loader(monkeypatch) -> None:
    from dashboard.services import crypto_edge_research

    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_change_summary",
        lambda history_limit=5: {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": True,
            "has_change_data": True,
            "summary_text": "Recent structural changes from stored snapshots: Funding 12.00% (+4.00 pts).",
            "rows": [{"theme": "funding"}],
        },
    )

    payload = asyncio.run(tools.get_crypto_edge_change_summary())

    assert payload["ok"] is True
    assert payload["has_change_data"] is True
    assert "Recent structural changes" in payload["summary_text"]


def test_get_crypto_edge_staleness_summary_uses_dashboard_loader(monkeypatch) -> None:
    from dashboard.services import crypto_edge_research

    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_staleness_summary",
        lambda: {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "needs_attention": True,
            "severity": "warn",
            "summary_text": "Structural-edge freshness needs attention: collector loop is stopped.",
        },
    )

    payload = asyncio.run(tools.get_crypto_edge_staleness_summary())

    assert payload["ok"] is True
    assert payload["needs_attention"] is True
    assert payload["severity"] == "warn"


def test_get_crypto_edge_staleness_digest_uses_dashboard_loader(monkeypatch) -> None:
    from dashboard.services import crypto_edge_research

    monkeypatch.setattr(
        crypto_edge_research,
        "load_crypto_edge_staleness_digest",
        lambda: {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "needs_attention": True,
            "severity": "warn",
            "headline": "Structural-edge data needs attention",
            "while_away_summary": "Structural-edge freshness needs attention: collector loop is stopped. Restart the collector loop.",
        },
    )

    payload = asyncio.run(tools.get_crypto_edge_staleness_digest())

    assert payload["ok"] is True
    assert payload["needs_attention"] is True
    assert "collector loop is stopped" in payload["while_away_summary"]
