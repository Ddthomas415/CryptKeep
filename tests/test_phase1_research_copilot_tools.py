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


def test_execute_tool_call_rejects_unknown_tool() -> None:
    payload = asyncio.run(tools.execute_tool_call("nope", {}))
    assert payload == {"ok": False, "error": "unsupported_tool:nope"}
