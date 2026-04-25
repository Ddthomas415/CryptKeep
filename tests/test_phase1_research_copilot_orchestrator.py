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

if not _has_module("phase1_research_copilot.orchestrator.main"):
    pytest.skip("phase1_research_copilot.orchestrator.main surface not present in this repo checkout", allow_module_level=True)

import asyncio
import sys
from types import SimpleNamespace
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

import phase1_research_copilot.orchestrator.main as orchestrator  # noqa: E402
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

    async def fake_operations() -> dict:
        return {"healthy_services": 3, "total_services": 3, "services": [], "source": "healthz"}

    async def fake_crypto_edges() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": True,
            "data_origin_label": "Live Public",
            "freshness_summary": "Fresh",
            "funding_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "basis_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "quote_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "funding": {"dominant_bias": "long_pays", "count": 1},
            "basis": {"avg_basis_bps": 8.4, "count": 1},
            "dislocations": {"positive_count": 2, "count": 2},
        }

    async def fake_latest_live_edges() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": True,
            "has_live_data": True,
            "data_origin_label": "Live Public",
            "freshness_summary": "Recent",
            "funding": {"dominant_bias": "long_pays"},
            "basis": {"avg_basis_bps": 7.8},
            "dislocations": {"positive_count": 3},
        }

    async def fake_crypto_edge_changes() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": True,
            "has_change_data": True,
            "summary_text": "Recent structural changes from stored snapshots: Funding 12.00% (+4.00 pts); Basis 8.40 bps (+1.10 bps).",
            "rows": [{"theme": "funding"}, {"theme": "basis"}],
        }

    async def fake_crypto_edge_staleness() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "needs_attention": True,
            "severity": "warn",
            "summary_text": "Structural-edge freshness needs attention: collector loop is stopped.",
            "action_text": "Restart the collector loop.",
        }

    async def fake_crypto_edge_digest() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "needs_attention": True,
            "severity": "warn",
            "headline": "Structural-edge data needs attention",
            "while_away_summary": "Structural-edge freshness needs attention: collector loop is stopped. Restart the collector loop.",
        }

    monkeypatch.setattr(orchestrator, "llm_client", DisabledClient())
    monkeypatch.setattr(orchestrator, "get_market_snapshot", fake_market)
    monkeypatch.setattr(orchestrator, "get_signal_summary", fake_signal)
    monkeypatch.setattr(orchestrator, "get_risk_summary", fake_risk)
    monkeypatch.setattr(orchestrator, "get_operations_summary", fake_operations)
    monkeypatch.setattr(orchestrator, "get_crypto_edge_report", fake_crypto_edges)
    monkeypatch.setattr(orchestrator, "get_latest_live_crypto_edge_snapshot", fake_latest_live_edges)
    monkeypatch.setattr(orchestrator, "get_crypto_edge_change_summary", fake_crypto_edge_changes)
    monkeypatch.setattr(orchestrator, "get_crypto_edge_staleness_summary", fake_crypto_edge_staleness)
    monkeypatch.setattr(orchestrator, "get_crypto_edge_staleness_digest", fake_crypto_edge_digest)
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
    assert payload["evidence_bundle"]["risk"]["gate"] == "NO_TRADING"
    assert payload["evidence_bundle"]["operations"]["healthy_services"] == 3
    assert payload["evidence_bundle"]["crypto_edges"]["research_only"] is True
    assert payload["evidence_bundle"]["latest_live_crypto_edges"]["has_live_data"] is True
    assert payload["evidence_bundle"]["crypto_edge_changes"]["has_change_data"] is True
    assert payload["evidence_bundle"]["crypto_edge_staleness"]["needs_attention"] is True
    assert payload["evidence_bundle"]["crypto_edge_digest"]["needs_attention"] is True
    assert payload["answer_metadata"]["source_type"] == "live_public_structural"
    assert payload["answer_metadata"]["source_family"] == "live_public"
    assert payload["answer_metadata"]["source_name"] == "Live Public"
    assert payload["answer_metadata"]["freshness_status"] == "fresh"
    assert payload["answer_metadata"]["data_timestamp"] == "2026-03-12T12:00:00Z"
    assert payload["answer_metadata"]["confidence_label"] == "High"
    assert payload["answer_metadata"]["partial_provenance"] is True
    assert "timestamp was used" in str(payload["answer_metadata"]["missing_provenance_reason"])
    assert payload["answer_metadata"]["metadata_status"] == "warn"
    assert "collector loop is stopped" in payload["answer_metadata"]["caveat"]
    assert "funding bias long_pays" in payload["current_cause"]
    assert "Live Public" in payload["current_cause"]
    assert "Freshness is Recent" in payload["current_cause"]
    assert "collector loop is stopped" in payload["current_cause"]


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

    async def fake_operations() -> dict:
        return {"healthy_services": 4, "total_services": 4, "services": [], "source": "healthz"}

    async def fake_crypto_edges() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": True,
            "data_origin_label": "Sample Bundle",
            "freshness_summary": "Stale",
            "funding_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "basis_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "quote_meta": {"capture_ts": "2026-03-18T10:00:00Z"},
            "funding": {"dominant_bias": "short_pays", "count": 1},
            "basis": {"avg_basis_bps": -4.2, "count": 1},
            "dislocations": {"positive_count": 1, "count": 1},
        }

    async def fake_latest_live_edges() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": True,
            "has_live_data": True,
            "data_origin_label": "Live Public",
            "freshness_summary": "Fresh",
            "funding": {"dominant_bias": "short_pays"},
            "basis": {"avg_basis_bps": -2.1},
            "dislocations": {"positive_count": 1},
        }

    async def fake_crypto_edge_changes() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": True,
            "has_change_data": True,
            "summary_text": "Recent structural changes from stored snapshots: Dislocations 1 (+1 venues).",
            "rows": [{"theme": "dislocations"}],
        }

    async def fake_crypto_edge_staleness() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "needs_attention": True,
            "severity": "warn",
            "summary_text": "Structural-edge freshness needs attention: collector loop is stopped.",
            "action_text": "Restart the collector loop.",
        }

    async def fake_crypto_edge_digest() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "needs_attention": True,
            "severity": "warn",
            "headline": "Structural-edge data needs attention",
            "while_away_summary": "Structural-edge freshness needs attention: collector loop is stopped. Restart the collector loop.",
        }

    monkeypatch.setattr(orchestrator, "llm_client", EnabledClient())
    monkeypatch.setattr(orchestrator, "execute_tool_call", fake_execute_tool_call)
    monkeypatch.setattr(orchestrator, "get_market_snapshot", fake_market)
    monkeypatch.setattr(orchestrator, "get_signal_summary", fake_signal)
    monkeypatch.setattr(orchestrator, "get_risk_summary", fake_risk)
    monkeypatch.setattr(orchestrator, "get_operations_summary", fake_operations)
    monkeypatch.setattr(orchestrator, "get_crypto_edge_report", fake_crypto_edges)
    monkeypatch.setattr(orchestrator, "get_latest_live_crypto_edge_snapshot", fake_latest_live_edges)
    monkeypatch.setattr(orchestrator, "get_crypto_edge_change_summary", fake_crypto_edge_changes)
    monkeypatch.setattr(orchestrator, "get_crypto_edge_staleness_summary", fake_crypto_edge_staleness)
    monkeypatch.setattr(orchestrator, "get_crypto_edge_staleness_digest", fake_crypto_edge_digest)
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
    assert calls[0]["text_format"]["type"] == "json_schema"
    assert calls[1]["text_format"]["name"] == "research_explain_response"
    assert calls[1]["previous_response_id"] == "resp_1"
    assert payload["evidence_bundle"]["risk"]["gate"] == "NO_TRADING"
    assert payload["evidence_bundle"]["operations"]["healthy_services"] == 4
    assert payload["evidence_bundle"]["crypto_edges"]["research_only"] is True
    assert payload["evidence_bundle"]["latest_live_crypto_edges"]["has_live_data"] is True
    assert payload["evidence_bundle"]["crypto_edge_changes"]["has_change_data"] is True
    assert payload["evidence_bundle"]["crypto_edge_staleness"]["needs_attention"] is True
    assert payload["evidence_bundle"]["crypto_edge_digest"]["needs_attention"] is True


def test_explain_endpoint_prioritizes_change_summary_for_while_away_question(monkeypatch) -> None:
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

    async def fake_operations() -> dict:
        return {"healthy_services": 3, "total_services": 3, "services": [], "source": "healthz"}

    async def fake_crypto_edges() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": True,
            "data_origin_label": "Live Public",
            "freshness_summary": "Fresh",
            "funding": {"dominant_bias": "long_pays", "count": 1},
            "basis": {"avg_basis_bps": 8.4, "count": 1},
            "dislocations": {"positive_count": 2, "count": 2},
        }

    async def fake_latest_live_edges() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": True,
            "has_live_data": True,
            "data_origin_label": "Live Public",
            "freshness_summary": "Recent",
            "funding": {"dominant_bias": "long_pays"},
            "basis": {"avg_basis_bps": 7.8},
            "dislocations": {"positive_count": 3},
        }

    async def fake_crypto_edge_changes() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "has_any_data": True,
            "has_change_data": True,
            "summary_text": "Recent structural changes from stored snapshots: Funding 12.00% (+4.00 pts); Basis 8.40 bps (+1.10 bps).",
            "rows": [{"theme": "funding"}, {"theme": "basis"}],
        }

    async def fake_crypto_edge_staleness() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "needs_attention": True,
            "severity": "warn",
            "summary_text": "Structural-edge freshness needs attention: collector loop is stopped.",
            "action_text": "Restart the collector loop.",
        }

    async def fake_crypto_edge_digest() -> dict:
        return {
            "ok": True,
            "research_only": True,
            "execution_enabled": False,
            "needs_attention": True,
            "severity": "warn",
            "headline": "Structural-edge data needs attention",
            "while_away_summary": "Structural-edge freshness needs attention: collector loop is stopped. Restart the collector loop.",
        }

    monkeypatch.setattr(orchestrator, "llm_client", DisabledClient())
    monkeypatch.setattr(orchestrator, "get_market_snapshot", fake_market)
    monkeypatch.setattr(orchestrator, "get_signal_summary", fake_signal)
    monkeypatch.setattr(orchestrator, "get_risk_summary", fake_risk)
    monkeypatch.setattr(orchestrator, "get_operations_summary", fake_operations)
    monkeypatch.setattr(orchestrator, "get_crypto_edge_report", fake_crypto_edges)
    monkeypatch.setattr(orchestrator, "get_latest_live_crypto_edge_snapshot", fake_latest_live_edges)
    monkeypatch.setattr(orchestrator, "get_crypto_edge_change_summary", fake_crypto_edge_changes)
    monkeypatch.setattr(orchestrator, "get_crypto_edge_staleness_summary", fake_crypto_edge_staleness)
    monkeypatch.setattr(orchestrator, "get_crypto_edge_staleness_digest", fake_crypto_edge_digest)
    monkeypatch.setattr(orchestrator, "emit_audit_event", _noop_audit)

    payload = asyncio.run(
        orchestrator.explain(
            ExplainRequest(asset="SOL", question="What changed while I was away on SOL?", lookback_minutes=60)
        )
    )

    assert payload["current_cause"].startswith("Recent structural changes from stored snapshots:")
    assert "Freshness is Recent" in payload["current_cause"]
    assert "collector loop is stopped" in payload["current_cause"]
