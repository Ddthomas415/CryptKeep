import asyncio

import pytest

pytest.importorskip("sqlalchemy")

from services.gateway.routes import query as gateway_query
from services.orchestrator import app as orchestrator_app
from services.orchestrator.workflows.explain_asset import build_explanation
from shared.schemas.explain import ExplainRequest
from shared.schemas.trade import TradeProposalRequest


def test_build_explanation_schema_minimum():
    out = build_explanation(
        asset="SOL",
        question="Why is SOL moving?",
        market_snapshot={
            "exchange": "coinbase",
            "last_price": "145.20",
            "bid": "145.10",
            "ask": "145.30",
            "timestamp": "2026-03-10T21:00:00Z",
        },
        news_items=[{"source": "newsapi", "title": "SOL activity up", "published_at": "2026-03-10T20:40:00Z"}],
        archive_items=[{"source": "wayback", "title": "Historical SOL precedent", "timestamp": "2025-03-10T21:00:00Z"}],
        future_docs=[{"title": "Upcoming SOL governance vote"}],
    )

    assert out["asset"] == "SOL"
    assert out["question"] == "Why is SOL moving?"
    assert "current_cause" in out
    assert "past_precedent" in out
    assert "future_catalyst" in out
    assert isinstance(out["confidence"], float)
    assert out["execution_disabled"] is True
    assert len(out["evidence"]) >= 1


def test_query_explain_returns_expected_schema_without_external_apis(monkeypatch):
    async def _fake_call(payload):
        return {
            "asset": payload["asset"],
            "question": payload["question"],
            "current_cause": "Recent price and volume expansion plus news mentions.",
            "past_precedent": "Similar historical roadmap move found.",
            "future_catalyst": "Governance event pending.",
            "confidence": 0.78,
            "evidence": [{"type": "market", "source": "coinbase", "timestamp": "2026-03-10T21:00:00Z"}],
            "execution_disabled": True,
        }

    monkeypatch.setattr(gateway_query, "_call_orchestrator", _fake_call)

    req = ExplainRequest(asset="SOL", question="Why is SOL moving?")
    out = asyncio.run(gateway_query.explain(req))

    assert out.asset == "SOL"
    assert out.execution_disabled is True
    assert out.current_cause
    assert isinstance(out.evidence, list)


def test_orchestrator_propose_trade_holds_when_risk_blocks(monkeypatch):
    async def _fake_explain_asset_flow(*, settings, logger, question, asset):
        _ = (settings, logger, question, asset)
        return "req-1", {
            "asset": "SOL",
            "question": "Should we open a SOL paper position now?",
            "current_cause": "Momentum setup detected.",
            "past_precedent": "Past setup matched.",
            "future_catalyst": "Governance vote pending.",
            "confidence": 0.85,
            "evidence": [],
            "execution_disabled": True,
        }

    async def _fake_request_json_with_retry(*, method, url, payload=None, retries=2):
        _ = (payload, retries)
        if method == "GET" and "/market/" in url:
            return {"last_price": "145.0"}
        if method == "POST" and "/risk/evaluate" in url:
            return {"paper_approved": False, "gate": "FULL_STOP", "execution_disabled": True}
        return {}

    monkeypatch.setattr(orchestrator_app, "explain_asset_flow", _fake_explain_asset_flow)
    monkeypatch.setattr(orchestrator_app, "_request_json_with_retry", _fake_request_json_with_retry)

    out = asyncio.run(orchestrator_app.propose_trade(TradeProposalRequest(asset="SOL")))
    assert out.asset == "SOL"
    assert out.side == "hold"
    assert out.execution_disabled is True
