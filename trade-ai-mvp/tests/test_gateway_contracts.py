from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from services.gateway.app import app
from services.gateway.routes import alerts as alerts_routes
from services.gateway.routes import live as live_routes
from services.gateway.routes import paper as paper_routes
from services.gateway.routes import query as query_routes
from shared.schemas.documents import DocumentSearchRequest
from shared.schemas.explain import ExplainRequest
from shared.schemas.live import (
    LiveCustodyKeyVerifyRequest,
    LiveDeploymentArmRequest,
    LiveExecutionPlacePreflightRequest,
    LiveExecutionPlacePreviewRequest,
    LiveExecutionPlaceRouteCompareRequest,
    LiveExecutionPlaceRouteRequest,
    LiveExecutionPlaceRequest,
    LiveExecutionSubmitRequest,
    LiveRouterIncidentActionRequest,
    LiveRouterIncidentOpenRequest,
    LiveOrderIntentRequest,
    LiveRouteAllocationRequest,
    LiveRoutePlanRequest,
    LiveRouteSimulateRequest,
)
from shared.schemas.paper import PaperOrderCreateRequest
from shared.schemas.paper import PaperReplayRequest, PaperShadowCompareRequest
from shared.schemas.trade import TradeProposalRequest


def test_gateway_required_routes_registered():
    paths = {route.path for route in app.routes}
    assert "/query/explain" in paths
    assert "/query/why-moving" in paths
    assert "/query/propose-trade" in paths
    assert "/documents/search" in paths
    assert "/market/{symbol}/snapshot" in paths
    assert "/paper/orders" in paths
    assert "/paper/orders/{order_id}" in paths
    assert "/paper/orders/{order_id}/cancel" in paths
    assert "/paper/positions" in paths
    assert "/paper/balances" in paths
    assert "/paper/fills" in paths
    assert "/paper/equity" in paths
    assert "/paper/equity/snapshot" in paths
    assert "/paper/performance" in paths
    assert "/paper/performance/rollups" in paths
    assert "/paper/performance/rollups/refresh" in paths
    assert "/paper/readiness" in paths
    assert "/paper/maintenance/retention" in paths
    assert "/paper/replay/run" in paths
    assert "/paper/shadow/compare" in paths
    assert "/paper/summary" in paths
    assert "/live/status" in paths
    assert "/live/custody/status" in paths
    assert "/live/custody/providers" in paths
    assert "/live/custody/policy" in paths
    assert "/live/custody/keys" in paths
    assert "/live/custody/keys/verify" in paths
    assert "/live/custody/rotation/plan" in paths
    assert "/live/custody/rotation/run" in paths
    assert "/live/deployment/checklist" in paths
    assert "/live/deployment/state" in paths
    assert "/live/deployment/arm" in paths
    assert "/live/deployment/disarm" in paths
    assert "/live/router/plan" in paths
    assert "/live/router/policy" in paths
    assert "/live/router/simulate" in paths
    assert "/live/router/allocation" in paths
    assert "/live/router/decisions" in paths
    assert "/live/router/analytics" in paths
    assert "/live/router/alerts" in paths
    assert "/live/router/maintenance/retention" in paths
    assert "/live/router/runbook" in paths
    assert "/live/router/gate" in paths
    assert "/live/router/gates" in paths
    assert "/live/router/gates/summary" in paths
    assert "/live/router/gates/maintenance/retention" in paths
    assert "/live/router/incidents/open" in paths
    assert "/live/router/incidents" in paths
    assert "/live/router/incidents/summary" in paths
    assert "/live/router/incidents/maintenance/retention" in paths
    assert "/live/router/incidents/{incident_id}" in paths
    assert "/live/router/incidents/{incident_id}/reopen" in paths
    assert "/live/router/incidents/{incident_id}/ack" in paths
    assert "/live/router/incidents/{incident_id}/resolve" in paths
    assert "/live/order-intent" in paths
    assert "/live/order-intents" in paths
    assert "/live/order-intents/{intent_id}/approve" in paths
    assert "/live/execution/providers" in paths
    assert "/live/execution/submissions" in paths
    assert "/live/execution/submissions/summary" in paths
    assert "/live/execution/place/analytics" in paths
    assert "/live/execution/place/strategy-analytics" in paths
    assert "/live/execution/submissions/sync" in paths
    assert "/live/execution/submissions/{submission_id}/sync" in paths
    assert "/live/execution/submissions/maintenance/retention" in paths
    assert "/live/execution/submissions/{submission_id}" in paths
    assert "/live/execution/orders/{venue_order_id}/status" in paths
    assert "/live/execution/orders/{venue_order_id}/cancel" in paths
    assert "/live/execution/place/preflight" in paths
    assert "/live/execution/place/preview" in paths
    assert "/live/execution/place/route" in paths
    assert "/live/execution/place/route/compare" in paths
    assert "/live/execution/place" in paths
    assert "/live/execution/submit" in paths
    assert "/alerts/paper/risk" in paths
    assert "/health" in paths


def test_gateway_query_explain_contract(monkeypatch):
    async def _fake_orchestrator(payload):
        assert payload["asset"] == "SOL"
        assert payload["question"] == "Why is SOL moving?"
        return {
            "asset": "SOL",
            "question": "Why is SOL moving?",
            "current_cause": "Price expansion and fresh document hits.",
            "past_precedent": "Prior roadmap cycle had a similar reaction.",
            "future_catalyst": "Upcoming governance vote remains pending.",
            "confidence": 0.78,
            "evidence": [{"type": "market", "source": "coinbase", "timestamp": "2026-03-10T21:00:00Z"}],
            "execution_disabled": True,
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(query_routes, "_call_orchestrator", _fake_orchestrator)
    monkeypatch.setattr(query_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(query_routes.explain(ExplainRequest(asset="SOL", question="Why is SOL moving?")))
    assert out.asset == "SOL"
    assert out.execution_disabled is True
    assert isinstance(out.evidence, list)
    assert out.current_cause


def test_gateway_alerts_paper_risk_contract(monkeypatch):
    async def _fake_exec(*, path, params=None, retries=2):
        _ = retries
        if path == "/paper/summary":
            assert params is None
            return {
                "as_of": "2026-03-10T21:10:00Z",
                "cash": 99800.25,
                "realized_pnl": 45.10,
                "unrealized_pnl": 320.30,
                "equity": 100120.55,
                "gross_exposure_usd": 1000.0,
                "positions": [
                    {"symbol": "SOL-USD", "notional_usd": 650.0},
                    {"symbol": "ETH-USD", "notional_usd": 350.0},
                ],
            }
        assert path == "/paper/performance"
        assert params == {"limit": 1000}
        return {
            "as_of": "2026-03-10T21:15:00Z",
            "points": 12,
            "max_drawdown_pct": 12.5,
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(alerts_routes, "_call_execution_sim", _fake_exec)
    monkeypatch.setattr(alerts_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(alerts_routes.settings, "paper_alert_drawdown_pct_threshold", 10.0)
    monkeypatch.setattr(alerts_routes.settings, "paper_alert_concentration_pct_threshold", 60.0)

    out = asyncio.run(alerts_routes.paper_risk_alerts())
    assert out["status"] == "ok"
    assert len(out["triggered"]) == 2
    alert_types = {item["type"] for item in out["triggered"]}
    assert "paper_drawdown_breach" in alert_types
    assert "paper_concentration_breach" in alert_types
    assert out["metrics"]["concentration_pct"] == 65.0


def test_gateway_alerts_concentration_helper():
    pct = alerts_routes._paper_concentration_pct(
        {
            "gross_exposure_usd": 200.0,
            "positions": [
                {"symbol": "BTC-USD", "notional_usd": 120.0},
                {"symbol": "ETH-USD", "notional_usd": 80.0},
            ],
        }
    )
    assert pct == 60.0


def test_gateway_live_status_contract(monkeypatch):
    async def _fake_compute(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=False,
            paper_trading_enabled=True,
            custody_ready=False,
            min_requirements_met=False,
            blockers=["execution_disabled_flag", "missing_exchange_credentials"],
            paper_readiness={"phase3_live_eligible": False},
            risk_snapshot={"gate": "FULL_STOP"},
            notes=["Live order placement remains disabled in this phase scaffold."],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_compute)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(live_routes.live_status("SOL-USD"))
    assert out.execution_enabled is False
    assert "execution_disabled_flag" in out.blockers


def test_gateway_live_route_plan_contract(monkeypatch):
    async def _fake_req(*, method, url, payload=None, params=None, retries=2):
        _ = (payload, retries)
        assert method == "GET"
        if "/market/SOL-USD/snapshot" in url:
            return {"symbol": "SOL-USD", "last_price": "145.0", "bid": "144.95", "ask": "145.05"}
        if "binance.com" in url:
            assert params == {"symbol": "SOLUSDT"}
            return {"bidPrice": "144.0", "askPrice": "146.0"}
        if "kraken.com" in url:
            assert params == {"pair": "SOLUSD"}
            return {"result": {"SOLUSD": {"b": ["143.0"], "a": ["147.0"]}}}
        raise AssertionError(f"unexpected url: {url}")

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "_request_json", _fake_req)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "execution_enabled", False)
    out = asyncio.run(
        live_routes.route_plan(
            LiveRoutePlanRequest(symbol="SOL-USD", side="buy", quantity=1.0, order_type="market")
        )
    )
    assert out.symbol == "SOL-USD"
    assert out.execution_disabled is True
    assert out.selected_venue == "coinbase"
    assert out.candidates[0]["venue"] == "coinbase"
    assert out.route_eligible is True
    assert isinstance(out.routing_policy, dict)


def test_gateway_live_router_policy_contract(monkeypatch):
    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_router_max_spread_bps", 99.0)
    monkeypatch.setattr(live_routes.settings, "live_router_max_estimated_cost_bps", 123.0)
    monkeypatch.setattr(live_routes.settings, "live_router_fee_bps_coinbase", 7.0)
    monkeypatch.setattr(live_routes.settings, "live_router_fee_bps_binance", 9.0)
    monkeypatch.setattr(live_routes.settings, "live_router_fee_bps_kraken", 15.0)

    out = asyncio.run(live_routes.router_policy())
    assert out.execution_disabled is True
    assert out.max_spread_bps == 99.0
    assert out.max_estimated_cost_bps == 123.0
    assert out.venue_fee_bps["coinbase"] == 7.0


def test_gateway_live_router_simulate_contract(monkeypatch):
    async def _fake_route(req):
        _ = req
        return live_routes.LiveRoutePlanResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=1.0,
            order_type="market",
            candidates=[
                {
                    "venue": "coinbase",
                    "score": 88,
                    "estimated_cost_bps": 12.0,
                    "route_eligible": True,
                    "reason": "primary integrated venue",
                },
                {
                    "venue": "kraken",
                    "score": 42,
                    "estimated_cost_bps": 210.0,
                    "route_eligible": False,
                    "reason": "policy_blocked:estimated_cost_above_policy",
                },
            ],
            rejected_venues=[
                {
                    "venue": "kraken",
                    "score": 42,
                    "estimated_cost_bps": 210.0,
                    "route_eligible": False,
                    "reason": "policy_blocked:estimated_cost_above_policy",
                }
            ],
            selected_venue="coinbase",
            selected_reason="primary integrated venue",
            routing_policy={"max_spread_bps": 100.0},
            route_eligible=True,
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "route_plan", _fake_route)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_simulate(
            LiveRouteSimulateRequest(
                symbol="SOL-USD",
                side="buy",
                quantity=1.0,
                order_type="market",
                max_slippage_bps=20.0,
            )
        )
    )
    assert out.execution_disabled is True
    assert out.feasible_route is True
    assert out.selected_venue == "coinbase"
    assert len(out.rejected_venues) == 1


def test_gateway_live_router_simulate_respects_max_slippage(monkeypatch):
    async def _fake_route(req):
        _ = req
        return live_routes.LiveRoutePlanResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=1.0,
            order_type="market",
            candidates=[
                {
                    "venue": "coinbase",
                    "score": 88,
                    "estimated_cost_bps": 25.0,
                    "route_eligible": True,
                    "reason": "primary integrated venue",
                }
            ],
            rejected_venues=[],
            selected_venue="coinbase",
            selected_reason="primary integrated venue",
            routing_policy={"max_spread_bps": 100.0},
            route_eligible=True,
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "route_plan", _fake_route)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_simulate(
            LiveRouteSimulateRequest(
                symbol="SOL-USD",
                side="buy",
                quantity=1.0,
                order_type="market",
                max_slippage_bps=20.0,
            )
        )
    )
    assert out.feasible_route is False
    assert out.selected_venue is None
    assert any(item.get("reason") == "max_slippage_bps_exceeded" for item in out.rejected_venues)


def test_gateway_live_router_allocation_contract(monkeypatch):
    async def _fake_route(req):
        _ = req
        return live_routes.LiveRoutePlanResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=3.0,
            order_type="market",
            candidates=[
                {
                    "venue": "coinbase",
                    "score": 95,
                    "estimated_cost_bps": 12.0,
                    "spread_bps": 7.0,
                    "fee_bps": 5.0,
                    "route_eligible": True,
                    "reason": "primary integrated venue",
                },
                {
                    "venue": "binance",
                    "score": 82,
                    "estimated_cost_bps": 18.0,
                    "spread_bps": 9.0,
                    "fee_bps": 6.0,
                    "route_eligible": True,
                    "reason": "public book ticker",
                },
                {
                    "venue": "kraken",
                    "score": 75,
                    "estimated_cost_bps": 90.0,
                    "spread_bps": 30.0,
                    "fee_bps": 8.0,
                    "route_eligible": True,
                    "reason": "public ticker",
                },
            ],
            rejected_venues=[],
            selected_venue="coinbase",
            selected_reason="primary integrated venue",
            routing_policy={"max_spread_bps": 100.0, "max_estimated_cost_bps": 120.0},
            route_eligible=True,
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "route_plan", _fake_route)
    monkeypatch.setattr(live_routes, "_persist_live_route_decision", lambda **_kwargs: None)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_allocation(
            LiveRouteAllocationRequest(
                symbol="SOL-USD",
                side="buy",
                quantity=3.0,
                order_type="market",
                max_venues=2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.execution_disabled is True
    assert out.feasible_route is True
    assert len(out.recommended_slices) == 2
    assert {item["venue"] for item in out.recommended_slices} == {"coinbase", "binance"}
    ratio_sum = sum(float(item["ratio"]) for item in out.recommended_slices)
    assert abs(ratio_sum - 1.0) < 0.01
    qty_sum = sum(float(item["quantity"]) for item in out.recommended_slices)
    assert abs(qty_sum - 3.0) < 0.000001
    assert out.total_estimated_cost_bps is not None
    assert out.routing_policy["allocation_min_slice_quantity"] == 0.0


def test_gateway_live_router_allocation_rejects_high_cost_routes(monkeypatch):
    async def _fake_route(req):
        _ = req
        return live_routes.LiveRoutePlanResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=1.0,
            order_type="market",
            candidates=[
                {
                    "venue": "coinbase",
                    "score": 80,
                    "estimated_cost_bps": 120.0,
                    "route_eligible": True,
                    "reason": "primary integrated venue",
                }
            ],
            rejected_venues=[],
            selected_venue="coinbase",
            selected_reason="primary integrated venue",
            routing_policy={"max_spread_bps": 100.0, "max_estimated_cost_bps": 120.0},
            route_eligible=True,
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "route_plan", _fake_route)
    monkeypatch.setattr(live_routes, "_persist_live_route_decision", lambda **_kwargs: None)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_allocation(
            LiveRouteAllocationRequest(
                symbol="SOL-USD",
                side="buy",
                quantity=1.0,
                order_type="market",
                max_venues=3,
                max_slippage_bps=20.0,
            )
        )
    )
    assert out.feasible_route is False
    assert out.recommended_slices == []
    assert any(item.get("reason") == "max_slippage_bps_exceeded" for item in out.rejected_venues)


def test_gateway_live_router_allocation_filters_slices_below_min_slice_quantity(monkeypatch):
    async def _fake_route(req):
        _ = req
        return live_routes.LiveRoutePlanResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=1.0,
            order_type="market",
            candidates=[
                {
                    "venue": "coinbase",
                    "score": 100.0,
                    "estimated_cost_bps": 5.0,
                    "route_eligible": True,
                    "reason": "primary integrated venue",
                },
                {
                    "venue": "binance",
                    "score": 1.0,
                    "estimated_cost_bps": 12.0,
                    "route_eligible": True,
                    "reason": "public ticker",
                },
            ],
            rejected_venues=[],
            selected_venue="coinbase",
            selected_reason="primary integrated venue",
            routing_policy={"max_spread_bps": 100.0, "max_estimated_cost_bps": 120.0},
            route_eligible=True,
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "route_plan", _fake_route)
    monkeypatch.setattr(live_routes, "_persist_live_route_decision", lambda **_kwargs: None)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_allocation(
            LiveRouteAllocationRequest(
                symbol="SOL-USD",
                side="buy",
                quantity=1.0,
                order_type="market",
                max_venues=2,
                min_venues=1,
                min_slice_quantity=0.2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.feasible_route is True
    assert len(out.recommended_slices) == 1
    assert out.recommended_slices[0]["venue"] == "coinbase"
    assert out.routing_policy["allocation_min_slice_quantity"] == 0.2
    assert any(item.get("reason") == "min_slice_quantity_not_met" for item in out.rejected_venues)


def test_gateway_live_router_allocation_rejects_unachievable_min_slice_quantity(monkeypatch):
    async def _fake_route(req):
        _ = req
        return live_routes.LiveRoutePlanResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=0.5,
            order_type="market",
            candidates=[
                {
                    "venue": "coinbase",
                    "score": 50.0,
                    "estimated_cost_bps": 6.0,
                    "route_eligible": True,
                    "reason": "primary integrated venue",
                },
                {
                    "venue": "binance",
                    "score": 49.0,
                    "estimated_cost_bps": 7.0,
                    "route_eligible": True,
                    "reason": "public ticker",
                },
            ],
            rejected_venues=[],
            selected_venue="coinbase",
            selected_reason="primary integrated venue",
            routing_policy={"max_spread_bps": 100.0, "max_estimated_cost_bps": 120.0},
            route_eligible=True,
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "route_plan", _fake_route)
    monkeypatch.setattr(live_routes, "_persist_live_route_decision", lambda **_kwargs: None)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_allocation(
            LiveRouteAllocationRequest(
                symbol="SOL-USD",
                side="buy",
                quantity=0.5,
                order_type="market",
                max_venues=2,
                min_venues=2,
                min_slice_quantity=0.3,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.feasible_route is False
    assert out.recommended_slices == []
    assert any(item.get("reason") == "min_slice_quantity_unachievable" for item in out.rejected_venues)


def test_gateway_live_router_allocation_caps_venue_ratio(monkeypatch):
    async def _fake_route(req):
        _ = req
        return live_routes.LiveRoutePlanResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=10.0,
            order_type="market",
            candidates=[
                {
                    "venue": "coinbase",
                    "score": 100.0,
                    "estimated_cost_bps": 5.0,
                    "route_eligible": True,
                    "reason": "primary integrated venue",
                },
                {
                    "venue": "binance",
                    "score": 10.0,
                    "estimated_cost_bps": 10.0,
                    "route_eligible": True,
                    "reason": "public ticker",
                },
            ],
            rejected_venues=[],
            selected_venue="coinbase",
            selected_reason="primary integrated venue",
            routing_policy={"max_spread_bps": 100.0, "max_estimated_cost_bps": 120.0},
            route_eligible=True,
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "route_plan", _fake_route)
    monkeypatch.setattr(live_routes, "_persist_live_route_decision", lambda **_kwargs: None)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_allocation(
            LiveRouteAllocationRequest(
                symbol="SOL-USD",
                side="buy",
                quantity=10.0,
                order_type="market",
                max_venues=2,
                min_venues=2,
                max_venue_ratio=0.6,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.feasible_route is True
    assert len(out.recommended_slices) == 2
    top_ratio = max(float(item["ratio"]) for item in out.recommended_slices)
    assert top_ratio <= 0.600001
    assert any(bool(item.get("ratio_capped")) for item in out.recommended_slices)
    qty_sum = sum(float(item["quantity"]) for item in out.recommended_slices)
    assert abs(qty_sum - 10.0) < 0.000001


def test_gateway_live_router_allocation_rejects_when_min_venues_not_met(monkeypatch):
    async def _fake_route(req):
        _ = req
        return live_routes.LiveRoutePlanResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=1.0,
            order_type="market",
            candidates=[
                {
                    "venue": "coinbase",
                    "score": 90.0,
                    "estimated_cost_bps": 7.0,
                    "route_eligible": True,
                    "reason": "primary integrated venue",
                }
            ],
            rejected_venues=[],
            selected_venue="coinbase",
            selected_reason="primary integrated venue",
            routing_policy={"max_spread_bps": 100.0, "max_estimated_cost_bps": 120.0},
            route_eligible=True,
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "route_plan", _fake_route)
    monkeypatch.setattr(live_routes, "_persist_live_route_decision", lambda **_kwargs: None)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_allocation(
            LiveRouteAllocationRequest(
                symbol="SOL-USD",
                side="buy",
                quantity=1.0,
                order_type="market",
                max_venues=2,
                min_venues=2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.feasible_route is False
    assert out.recommended_slices == []
    assert any(item.get("reason") == "min_venues_not_met" for item in out.rejected_venues)


def test_gateway_live_router_allocation_rejects_min_venues_gt_max_venues(monkeypatch):
    async def _fake_route(req):
        _ = req
        return live_routes.LiveRoutePlanResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=1.0,
            order_type="market",
            candidates=[],
            rejected_venues=[],
            selected_venue=None,
            selected_reason=None,
            routing_policy={},
            route_eligible=False,
            execution_disabled=True,
        )

    monkeypatch.setattr(live_routes, "route_plan", _fake_route)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            live_routes.router_allocation(
                LiveRouteAllocationRequest(
                    symbol="SOL-USD",
                    side="buy",
                    quantity=1.0,
                    order_type="market",
                    max_venues=1,
                    min_venues=2,
                    max_slippage_bps=25.0,
                )
            )
        )
    assert exc.value.status_code == 400


def test_gateway_live_router_decisions_list_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        symbol = _Col()
        source_endpoint = _Col()
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"
        created_at = "2026-03-11T04:00:00Z"
        source_endpoint = "router_plan"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        selected_venue = "coinbase"
        selected_reason = "primary integrated venue"
        route_eligible = True
        feasible_route = True
        max_slippage_bps = None
        execution_disabled = True
        candidates = [{"venue": "coinbase", "route_eligible": True}]
        rejected_venues = []
        routing_policy = {"max_spread_bps": 120.0}
        request_payload = {"symbol": "SOL-USD"}
        response_payload = {"selected_venue": "coinbase"}

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [_Row()]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouteDecision", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_decisions(symbol="SOL-USD", source_endpoint="router_plan", limit=20)
    )
    assert len(out.decisions) == 1
    assert out.decisions[0].symbol == "SOL-USD"
    assert out.decisions[0].selected_venue == "coinbase"


def test_gateway_live_router_analytics_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        symbol = _Col()
        source_endpoint = _Col()
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        def __init__(
            self,
            *,
            created_at,
            selected_venue,
            route_eligible,
            feasible_route,
            estimated_cost_bps,
            rejected_venues,
        ):
            self.id = "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"
            self.created_at = created_at
            self.source_endpoint = "router_plan"
            self.symbol = "SOL-USD"
            self.side = "buy"
            self.quantity = 1.0
            self.order_type = "market"
            self.selected_venue = selected_venue
            self.selected_reason = "reason"
            self.route_eligible = route_eligible
            self.feasible_route = feasible_route
            self.max_slippage_bps = None
            self.execution_disabled = True
            self.candidates = (
                [{"venue": selected_venue, "estimated_cost_bps": estimated_cost_bps}]
                if selected_venue
                else []
            )
            self.rejected_venues = rejected_venues
            self.routing_policy = {"max_spread_bps": 120.0}
            self.request_payload = {"symbol": "SOL-USD"}
            self.response_payload = {"selected_venue": selected_venue}

    now = datetime.now(timezone.utc)
    recent_a = _Row(
        created_at=now.isoformat(),
        selected_venue="coinbase",
        route_eligible=True,
        feasible_route=True,
        estimated_cost_bps=12.0,
        rejected_venues=[],
    )
    recent_b = _Row(
        created_at=now.isoformat(),
        selected_venue=None,
        route_eligible=False,
        feasible_route=False,
        estimated_cost_bps=0.0,
        rejected_venues=[{"policy_blockers": ["spread_above_policy"]}],
    )
    old_row = _Row(
        created_at=(now.replace(year=2020)).isoformat(),
        selected_venue="kraken",
        route_eligible=True,
        feasible_route=True,
        estimated_cost_bps=20.0,
        rejected_venues=[],
    )

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [recent_a, recent_b, old_row]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouteDecision", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.router_analytics(symbol="SOL-USD", source_endpoint="router_plan", window_hours=24, limit=50)
    )
    assert out.total_decisions == 2
    assert out.route_eligible_count == 1
    assert out.feasible_route_count == 1
    assert out.selected_venue_count == 1
    assert out.selected_venue_counts["coinbase"] == 1
    assert out.avg_estimated_cost_bps_by_venue["coinbase"] == 12.0
    assert out.policy_blocker_counts["spread_above_policy"] == 1
    assert out.execution_disabled is True


def test_gateway_live_router_analytics_rejects_nonpositive_window():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.router_analytics(window_hours=0))
    assert exc.value.status_code == 400


def test_gateway_live_router_alerts_contract(monkeypatch):
    async def _fake_analytics(symbol=None, source_endpoint=None, window_hours=24, limit=2000):
        _ = (symbol, source_endpoint, window_hours, limit)
        return live_routes.LiveRouterAnalyticsResponse(
            as_of=datetime.now(timezone.utc),
            symbol="SOL-USD",
            source_endpoint="router_plan",
            window_hours=24,
            total_decisions=100,
            route_eligible_count=52,
            feasible_route_count=49,
            selected_venue_count=52,
            route_eligible_rate=0.52,
            feasible_route_rate=0.49,
            selected_venue_rate=0.52,
            selected_venue_counts={"coinbase": 40, "binance": 12},
            avg_estimated_cost_bps_by_venue={"coinbase": 12.0, "binance": 19.0},
            policy_blocker_counts={"spread_above_policy": 45, "estimated_cost_above_policy": 35},
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "router_analytics", _fake_analytics)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_router_alert_min_decisions", 20)
    monkeypatch.setattr(live_routes.settings, "live_router_alert_min_route_eligible_rate", 0.6)
    monkeypatch.setattr(live_routes.settings, "live_router_alert_min_feasible_route_rate", 0.55)
    monkeypatch.setattr(live_routes.settings, "live_router_alert_max_spread_blocker_ratio", 0.3)
    monkeypatch.setattr(live_routes.settings, "live_router_alert_max_cost_blocker_ratio", 0.3)

    out = asyncio.run(
        live_routes.router_alerts(symbol="SOL-USD", source_endpoint="router_plan", window_hours=24, limit=1000)
    )
    assert out.status == "alerting"
    assert out.execution_disabled is True
    alert_types = {item["type"] for item in out.triggered}
    assert "route_eligibility_degraded" in alert_types
    assert "feasible_route_degraded" in alert_types
    assert "spread_policy_pressure" in alert_types
    assert "cost_policy_pressure" in alert_types


def test_gateway_live_router_alerts_insufficient_data(monkeypatch):
    async def _fake_analytics(symbol=None, source_endpoint=None, window_hours=24, limit=2000):
        _ = (symbol, source_endpoint, window_hours, limit)
        return live_routes.LiveRouterAnalyticsResponse(
            as_of=datetime.now(timezone.utc),
            symbol="SOL-USD",
            source_endpoint="router_plan",
            window_hours=24,
            total_decisions=5,
            route_eligible_count=0,
            feasible_route_count=0,
            selected_venue_count=0,
            route_eligible_rate=0.0,
            feasible_route_rate=0.0,
            selected_venue_rate=0.0,
            selected_venue_counts={},
            avg_estimated_cost_bps_by_venue={},
            policy_blocker_counts={"spread_above_policy": 5},
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "router_analytics", _fake_analytics)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_router_alert_min_decisions", 20)
    out = asyncio.run(live_routes.router_alerts(symbol="SOL-USD", source_endpoint="router_plan"))
    assert out.status == "ok"
    assert out.triggered == []


def test_gateway_live_router_retention_contract(monkeypatch):
    class _Col:
        def __lt__(self, other):
            _ = other
            return self

    class _Model:
        created_at = _Col()

    class _Query:
        def filter(self, *_args, **_kwargs):
            return self

        def delete(self, synchronize_session=False):
            _ = synchronize_session
            return 11

    class _DB:
        def query(self, model):
            _ = model
            return _Query()

        def commit(self):
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouteDecision", _Model)
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(live_routes.router_retention({"days": 30}))
    assert out.retention_days == 30
    assert out.deleted_route_decisions == 11
    assert out.execution_disabled is True


def test_gateway_live_router_retention_rejects_nonpositive_days():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.router_retention({"days": 0}))
    assert exc.value.status_code == 400


def test_gateway_live_router_runbook_contract(monkeypatch):
    async def _fake_alerts(symbol=None, source_endpoint=None, window_hours=24, limit=2000):
        _ = (symbol, source_endpoint, window_hours, limit)
        return live_routes.LiveRouterAlertsResponse(
            status="alerting",
            as_of=datetime.now(timezone.utc),
            symbol="SOL-USD",
            source_endpoint="router_plan",
            window_hours=24,
            total_decisions=100,
            thresholds={},
            metrics={},
            triggered=[
                {"type": "route_eligibility_degraded"},
                {"type": "cost_policy_pressure"},
            ],
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "router_alerts", _fake_alerts)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_runbook(symbol="SOL-USD", source_endpoint="router_plan", window_hours=24, limit=1000)
    )
    assert out.status == "action_required"
    assert out.suggested_gate == "HALT_NEW_POSITIONS"
    assert len(out.actions) >= 2
    assert out.execution_disabled is True


def test_gateway_live_router_runbook_ok_contract(monkeypatch):
    async def _fake_alerts(symbol=None, source_endpoint=None, window_hours=24, limit=2000):
        _ = (symbol, source_endpoint, window_hours, limit)
        return live_routes.LiveRouterAlertsResponse(
            status="ok",
            as_of=datetime.now(timezone.utc),
            symbol="SOL-USD",
            source_endpoint="router_plan",
            window_hours=24,
            total_decisions=10,
            thresholds={},
            metrics={},
            triggered=[],
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "router_alerts", _fake_alerts)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(live_routes.router_runbook(symbol="SOL-USD", source_endpoint="router_plan"))
    assert out.status == "ok"
    assert out.suggested_gate == "ALLOW_TRADING"
    assert out.execution_disabled is True


def test_gateway_live_router_gate_from_incident_contract(monkeypatch):
    class _Col:
        def in_(self, other):
            _ = other
            return self

        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        status = _Col()
        symbol = _Col()
        source_endpoint = _Col()
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"
        status = "open"
        symbol = "SOL-USD"
        source_endpoint = "router_plan"
        window_hours = 24
        suggested_gate = "HALT_NEW_POSITIONS"
        alerts = [{"type": "route_eligibility_degraded", "severity": "medium", "message": "degraded"}]
        rationale = ["Route eligibility degraded below threshold."]
        actions = [{"id": "tighten_new_exposure"}]

    class _Result:
        def scalar_one_or_none(self):
            return _Row()

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    async def _fake_runbook(*args, **kwargs):
        raise AssertionError("runbook should not be used when open incident exists")

    monkeypatch.setattr(live_routes, "LiveRouterIncident", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "router_runbook", _fake_runbook)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(live_routes.router_gate(symbol="SOL-USD", source_endpoint="router_plan", window_hours=24))
    assert out.source == "incident"
    assert out.recommended_gate == "HALT_NEW_POSITIONS"
    assert out.system_stress == "high"
    assert out.regime == "degraded"
    assert out.incident_id == "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"
    assert out.execution_disabled is True


def test_gateway_live_router_gate_fallback_runbook_contract(monkeypatch):
    async def _fake_runbook(symbol=None, source_endpoint=None, window_hours=24, limit=2000):
        _ = (symbol, source_endpoint, window_hours, limit)
        return live_routes.LiveRouterRunbookResponse(
            status="action_required",
            as_of=datetime.now(timezone.utc),
            symbol="SOL-USD",
            source_endpoint="router_plan",
            window_hours=24,
            suggested_gate="ALLOW_ONLY_REDUCTIONS",
            rationale=["Spread policy blockers are elevated."],
            actions=[{"id": "review_spread_policy"}],
            alerts=[{"type": "spread_policy_pressure", "severity": "low", "message": "Spread blockers elevated"}],
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "SessionLocal", None)
    monkeypatch.setattr(live_routes, "router_runbook", _fake_runbook)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(live_routes.router_gate(symbol="SOL-USD", source_endpoint="router_plan", window_hours=24))
    assert out.source == "runbook"
    assert out.recommended_gate == "ALLOW_ONLY_REDUCTIONS"
    assert out.system_stress == "medium"
    assert out.regime == "caution"
    assert out.incident_id is None
    assert out.execution_disabled is True


def test_gateway_live_router_gate_with_binding_risk_overlay_contract(monkeypatch):
    async def _fake_runbook(symbol=None, source_endpoint=None, window_hours=24, limit=2000):
        _ = (symbol, source_endpoint, window_hours, limit)
        return live_routes.LiveRouterRunbookResponse(
            status="ok",
            as_of=datetime.now(timezone.utc),
            symbol="SOL-USD",
            source_endpoint="router_plan",
            window_hours=24,
            suggested_gate="ALLOW_ONLY_REDUCTIONS",
            rationale=["Spread policy blockers are elevated."],
            actions=[{"id": "review_spread_policy"}],
            alerts=[{"type": "spread_policy_pressure", "severity": "low"}],
            execution_disabled=True,
        )

    async def _fake_risk(symbol: str):
        assert symbol == "SOL-USD"
        return {
            "gate": "FULL_STOP",
            "reason": "Daily loss limit breached",
            "execution_disabled": True,
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "SessionLocal", None)
    monkeypatch.setattr(live_routes, "router_runbook", _fake_runbook)
    monkeypatch.setattr(live_routes, "_risk_snapshot", _fake_risk)
    monkeypatch.setattr(live_routes, "_persist_live_router_gate_signal", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_gate(symbol="SOL-USD", source_endpoint="router_plan", window_hours=24, include_risk=True)
    )
    assert out.source == "runbook"
    assert out.router_gate == "ALLOW_ONLY_REDUCTIONS"
    assert out.risk_gate_raw == "FULL_STOP"
    assert out.risk_gate_mapped == "FULL_STOP"
    assert out.risk_gate_binding is True
    assert out.recommended_gate == "FULL_STOP"
    assert out.system_stress == "critical"
    assert "risk" in out.gate_sources


def test_gateway_live_router_gate_with_nonbinding_risk_overlay_contract(monkeypatch):
    async def _fake_runbook(symbol=None, source_endpoint=None, window_hours=24, limit=2000):
        _ = (symbol, source_endpoint, window_hours, limit)
        return live_routes.LiveRouterRunbookResponse(
            status="ok",
            as_of=datetime.now(timezone.utc),
            symbol="SOL-USD",
            source_endpoint="router_plan",
            window_hours=24,
            suggested_gate="ALLOW_ONLY_REDUCTIONS",
            rationale=["Spread policy blockers are elevated."],
            actions=[{"id": "review_spread_policy"}],
            alerts=[],
            execution_disabled=True,
        )

    async def _fake_risk(symbol: str):
        assert symbol == "SOL-USD"
        return {
            "gate": "FULL_STOP",
            "reason": "Phase 1 research mode only",
            "execution_disabled": True,
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "SessionLocal", None)
    monkeypatch.setattr(live_routes, "router_runbook", _fake_runbook)
    monkeypatch.setattr(live_routes, "_risk_snapshot", _fake_risk)
    monkeypatch.setattr(live_routes, "_persist_live_router_gate_signal", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_gate(symbol="SOL-USD", source_endpoint="router_plan", window_hours=24, include_risk=True)
    )
    assert out.router_gate == "ALLOW_ONLY_REDUCTIONS"
    assert out.risk_gate_raw == "FULL_STOP"
    assert out.risk_gate_binding is False
    assert out.recommended_gate == "ALLOW_ONLY_REDUCTIONS"
    assert "risk" not in out.gate_sources


def test_gateway_live_router_gates_list_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        symbol = _Col()
        source_endpoint = _Col()
        source = _Col()
        recommended_gate = _Col()
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "70fa0898-b0a1-4e94-97cc-3c4ef49ca512"
        created_at = "2026-03-11T06:12:00Z"
        symbol = "SOL-USD"
        source_endpoint = "router_plan"
        window_hours = 24
        source = "incident"
        recommended_gate = "HALT_NEW_POSITIONS"
        system_stress = "high"
        regime = "degraded"
        zone = "containment"
        top_hazards = [{"type": "route_eligibility_degraded"}]
        rationale = ["Route eligibility degraded below threshold."]
        actions = [{"id": "tighten_new_exposure"}]
        incident_id = "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"
        incident_status = "open"
        payload = {"recommended_gate": "HALT_NEW_POSITIONS"}
        execution_disabled = True

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [_Row()]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouterGateSignal", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_gates(
            symbol="SOL-USD",
            source_endpoint="router_plan",
            source="incident",
            recommended_gate="HALT_NEW_POSITIONS",
            limit=20,
        )
    )
    assert len(out.signals) == 1
    assert out.signals[0].source == "incident"
    assert out.signals[0].recommended_gate == "HALT_NEW_POSITIONS"


def test_gateway_live_router_gates_summary_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        symbol = _Col()
        source_endpoint = _Col()
        source = _Col()
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    now = datetime.now(timezone.utc)

    class _IncidentRow:
        created_at = now.isoformat()
        source = "incident"
        recommended_gate = "HALT_NEW_POSITIONS"
        system_stress = "high"
        regime = "degraded"
        zone = "containment"

    class _RunbookRow:
        created_at = now.isoformat()
        source = "runbook"
        recommended_gate = "ALLOW_ONLY_REDUCTIONS"
        system_stress = "medium"
        regime = "caution"
        zone = "reduction_only"

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [_IncidentRow(), _RunbookRow()]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouterGateSignal", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_gates_summary(
            symbol="SOL-USD",
            source_endpoint="router_plan",
            source=None,
            window_hours=24,
            limit=100,
        )
    )
    assert out.total_signals == 2
    assert out.by_source["incident"] == 1
    assert out.by_source["runbook"] == 1
    assert out.by_recommended_gate["HALT_NEW_POSITIONS"] == 1
    assert out.by_system_stress["high"] == 1
    assert out.execution_disabled is True


def test_gateway_live_router_gates_summary_rejects_nonpositive_window():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.router_gates_summary(window_hours=0))
    assert exc.value.status_code == 400


def test_gateway_live_router_gates_retention_contract(monkeypatch):
    class _Col:
        def __lt__(self, other):
            _ = other
            return self

    class _Model:
        created_at = _Col()

    class _Query:
        def filter(self, *_args, **_kwargs):
            return self

        def delete(self, synchronize_session=False):
            _ = synchronize_session
            return 5

    class _DB:
        def query(self, model):
            _ = model
            return _Query()

        def commit(self):
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouterGateSignal", _Model)
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(live_routes.router_gates_retention({"days": 120}))
    assert out.retention_days == 120
    assert out.deleted_gate_signals == 5
    assert out.execution_disabled is True


def test_gateway_live_router_gates_retention_rejects_nonpositive_days():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.router_gates_retention({"days": 0}))
    assert exc.value.status_code == 400


def test_gateway_live_router_incident_open_contract(monkeypatch):
    class _Model:
        def __init__(self, **kwargs):
            self.id = "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"
            self.created_at = "2026-03-11T05:20:00Z"
            self.updated_at = "2026-03-11T05:20:00Z"
            self.opened_at = "2026-03-11T05:20:00Z"
            self.closed_at = None
            self.status = kwargs.get("status", "open")
            self.severity = kwargs.get("severity", "medium")
            self.symbol = kwargs.get("symbol")
            self.source_endpoint = kwargs.get("source_endpoint")
            self.window_hours = kwargs.get("window_hours")
            self.suggested_gate = kwargs.get("suggested_gate", "ALLOW_ONLY_REDUCTIONS")
            self.operator = kwargs.get("operator")
            self.note = kwargs.get("note")
            self.resolution_note = kwargs.get("resolution_note")
            self.runbook_payload = kwargs.get("runbook_payload", {})
            self.alerts = kwargs.get("alerts", [])
            self.actions = kwargs.get("actions", [])
            self.rationale = kwargs.get("rationale", [])
            self.execution_disabled = kwargs.get("execution_disabled", True)

    class _DB:
        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_runbook(symbol=None, source_endpoint=None, window_hours=24, limit=2000):
        _ = (symbol, source_endpoint, window_hours, limit)
        return live_routes.LiveRouterRunbookResponse(
            status="action_required",
            as_of=datetime.now(timezone.utc),
            symbol="SOL-USD",
            source_endpoint="router_plan",
            window_hours=24,
            suggested_gate="HALT_NEW_POSITIONS",
            rationale=["Route eligibility degraded below threshold."],
            actions=[{"id": "tighten_new_exposure"}],
            alerts=[{"type": "route_eligibility_degraded"}],
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouterIncident", _Model)
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "router_runbook", _fake_runbook)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_incident_open(
            LiveRouterIncidentOpenRequest(
                operator="ops-oncall",
                symbol="SOL-USD",
                source_endpoint="router_plan",
                window_hours=24,
                limit=1000,
                note="opened from bundle test",
            )
        )
    )
    assert out.status == "open"
    assert out.suggested_gate == "HALT_NEW_POSITIONS"
    assert out.severity == "high"
    assert out.operator == "ops-oncall"
    assert out.execution_disabled is True


def test_gateway_live_router_incident_open_rejects_when_no_action(monkeypatch):
    class _Model:
        pass

    class _DB:
        pass

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_runbook(symbol=None, source_endpoint=None, window_hours=24, limit=2000):
        _ = (symbol, source_endpoint, window_hours, limit)
        return live_routes.LiveRouterRunbookResponse(
            status="ok",
            as_of=datetime.now(timezone.utc),
            symbol="SOL-USD",
            source_endpoint="router_plan",
            window_hours=24,
            suggested_gate="ALLOW_TRADING",
            rationale=[],
            actions=[],
            alerts=[],
            execution_disabled=True,
        )

    monkeypatch.setattr(live_routes, "LiveRouterIncident", _Model)
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "router_runbook", _fake_runbook)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.router_incident_open(LiveRouterIncidentOpenRequest(symbol="SOL-USD")))
    assert exc.value.status_code == 409


def test_gateway_live_router_incidents_list_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        status = _Col()
        symbol = _Col()
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"
        created_at = "2026-03-11T05:20:00Z"
        updated_at = "2026-03-11T05:20:00Z"
        opened_at = "2026-03-11T05:20:00Z"
        closed_at = None
        status = "open"
        severity = "high"
        symbol = "SOL-USD"
        source_endpoint = "router_plan"
        window_hours = 24
        suggested_gate = "HALT_NEW_POSITIONS"
        operator = "ops-oncall"
        note = "opened"
        resolution_note = None
        runbook_payload = {}
        alerts = [{"type": "route_eligibility_degraded"}]
        actions = [{"id": "tighten_new_exposure"}]
        rationale = ["Route eligibility degraded below threshold."]
        execution_disabled = True

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [_Row()]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouterIncident", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(live_routes.router_incidents(status="open", symbol="SOL-USD", limit=20))
    assert len(out.incidents) == 1
    assert out.incidents[0].status == "open"
    assert out.incidents[0].symbol == "SOL-USD"


def test_gateway_live_router_incidents_summary_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        symbol = _Col()
        source_endpoint = _Col()
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    now = datetime.now(timezone.utc)

    class _OpenRow:
        created_at = now.isoformat()
        opened_at = now.isoformat()
        closed_at = None
        status = "open"
        severity = "high"
        suggested_gate = "HALT_NEW_POSITIONS"

    class _ResolvedRow:
        created_at = now.isoformat()
        opened_at = now.isoformat()
        closed_at = (now + timedelta(minutes=10)).isoformat()
        status = "resolved"
        severity = "medium"
        suggested_gate = "ALLOW_ONLY_REDUCTIONS"

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [_OpenRow(), _ResolvedRow()]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouterIncident", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_incidents_summary(symbol="SOL-USD", source_endpoint="router_plan", window_hours=24, limit=100)
    )
    assert out.total_incidents == 2
    assert out.open_count == 1
    assert out.resolved_count == 1
    assert out.severity_counts["high"] == 1
    assert out.suggested_gate_counts["HALT_NEW_POSITIONS"] == 1
    assert out.execution_disabled is True


def test_gateway_live_router_incidents_summary_rejects_nonpositive_window():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.router_incidents_summary(window_hours=0))
    assert exc.value.status_code == 400


def test_gateway_live_router_incidents_retention_contract(monkeypatch):
    class _Col:
        def __lt__(self, other):
            _ = other
            return self

    class _Model:
        created_at = _Col()

    class _Query:
        def filter(self, *_args, **_kwargs):
            return self

        def delete(self, synchronize_session=False):
            _ = synchronize_session
            return 7

    class _DB:
        def query(self, model):
            _ = model
            return _Query()

        def commit(self):
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouterIncident", _Model)
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(live_routes.router_incidents_retention({"days": 45}))
    assert out.retention_days == 45
    assert out.deleted_incidents == 7
    assert out.execution_disabled is True


def test_gateway_live_router_incidents_retention_rejects_nonpositive_days():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.router_incidents_retention({"days": 0}))
    assert exc.value.status_code == 400


def test_gateway_live_router_incident_get_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"
        created_at = "2026-03-11T05:20:00Z"
        updated_at = "2026-03-11T05:25:00Z"
        opened_at = "2026-03-11T05:20:00Z"
        closed_at = None
        status = "acknowledged"
        severity = "high"
        symbol = "SOL-USD"
        source_endpoint = "router_plan"
        window_hours = 24
        suggested_gate = "HALT_NEW_POSITIONS"
        operator = "ops-oncall"
        note = "checking"
        resolution_note = None
        runbook_payload = {}
        alerts = []
        actions = []
        rationale = []
        execution_disabled = True

    class _Result:
        def scalar_one_or_none(self):
            return _Row()

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouterIncident", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(live_routes.router_incident_get("3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"))
    assert out.id == "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"
    assert out.status == "acknowledged"
    assert out.execution_disabled is True


def test_gateway_live_router_incident_reopen_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"
        created_at = "2026-03-11T05:20:00Z"
        updated_at = "2026-03-11T06:00:00Z"
        opened_at = "2026-03-11T05:20:00Z"
        closed_at = "2026-03-11T05:55:00Z"
        status = "resolved"
        severity = "high"
        symbol = "SOL-USD"
        source_endpoint = "router_plan"
        window_hours = 24
        suggested_gate = "HALT_NEW_POSITIONS"
        operator = "ops-oncall"
        note = "resolved earlier"
        resolution_note = "resolved"
        runbook_payload = {}
        alerts = []
        actions = []
        rationale = []
        execution_disabled = True

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouterIncident", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_incident_reopen(
            "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d",
            LiveRouterIncidentActionRequest(operator="ops-oncall", note="reopened for verification"),
        )
    )
    assert out.status == "open"
    assert out.operator == "ops-oncall"
    assert out.note == "reopened for verification"
    assert out.resolution_note is None


def test_gateway_live_router_incident_reopen_rejects_nonresolved(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        status = "open"

    class _Result:
        def scalar_one_or_none(self):
            return _Row()

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(live_routes, "LiveRouterIncident", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            live_routes.router_incident_reopen(
                "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d",
                LiveRouterIncidentActionRequest(operator="ops-oncall", note="reopen"),
            )
        )
    assert exc.value.status_code == 409


def test_gateway_live_router_incident_ack_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"
        created_at = "2026-03-11T05:20:00Z"
        updated_at = "2026-03-11T05:20:00Z"
        opened_at = "2026-03-11T05:20:00Z"
        closed_at = None
        status = "open"
        severity = "high"
        symbol = "SOL-USD"
        source_endpoint = "router_plan"
        window_hours = 24
        suggested_gate = "HALT_NEW_POSITIONS"
        operator = None
        note = None
        resolution_note = None
        runbook_payload = {}
        alerts = []
        actions = []
        rationale = []
        execution_disabled = True

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouterIncident", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_incident_ack(
            "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d",
            LiveRouterIncidentActionRequest(operator="ops-oncall", note="acknowledged"),
        )
    )
    assert out.status == "acknowledged"
    assert out.operator == "ops-oncall"


def test_gateway_live_router_incident_resolve_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d"
        created_at = "2026-03-11T05:20:00Z"
        updated_at = "2026-03-11T05:20:00Z"
        opened_at = "2026-03-11T05:20:00Z"
        closed_at = None
        status = "acknowledged"
        severity = "high"
        symbol = "SOL-USD"
        source_endpoint = "router_plan"
        window_hours = 24
        suggested_gate = "HALT_NEW_POSITIONS"
        operator = None
        note = None
        resolution_note = None
        runbook_payload = {}
        alerts = []
        actions = []
        rationale = []
        execution_disabled = True

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveRouterIncident", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.router_incident_resolve(
            "3bf89f6b-8d2a-4718-9b5c-8b86059ec31d",
            LiveRouterIncidentActionRequest(operator="ops-oncall", note="resolved"),
        )
    )
    assert out.status == "resolved"
    assert out.operator == "ops-oncall"
    assert out.resolution_note == "resolved"


def test_gateway_live_custody_status_contract(monkeypatch):
    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "coinbase_api_key", "abc123")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_secret", "xyz789")
    out = asyncio.run(live_routes.custody_status())
    assert out.provider == "coinbase"
    assert out.ready is True
    assert out.key_present is True
    assert out.secret_present is True
    assert out.key_fingerprint is not None
    assert out.secret_fingerprint is not None


def test_gateway_live_custody_providers_contract(monkeypatch):
    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_custody_provider", "vault_stub")
    monkeypatch.setattr(live_routes.settings, "live_custody_key_id", "vault://coinbase/key/main")
    monkeypatch.setattr(live_routes.settings, "live_custody_secret_id", "")

    out = asyncio.run(live_routes.custody_providers())
    assert out.configured_provider == "vault_stub"
    assert out.execution_disabled is True
    assert len(out.providers) >= 2
    providers = {item.name: item for item in out.providers}
    assert providers["vault_stub"].configured is True
    assert providers["vault_stub"].ready is False
    assert "missing_custody_secret_ref" in providers["vault_stub"].blockers


def test_gateway_live_custody_policy_contract(monkeypatch):
    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_custody_provider", "vault_stub")
    monkeypatch.setattr(live_routes.settings, "live_custody_key_id", "vault://coinbase/key/main")
    monkeypatch.setattr(live_routes.settings, "live_custody_secret_id", "vault://coinbase/secret/main")
    monkeypatch.setattr(
        live_routes.settings,
        "live_custody_last_rotated_at",
        (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
    )
    monkeypatch.setattr(live_routes.settings, "live_custody_rotation_max_age_days", 30)

    out = asyncio.run(live_routes.custody_policy())
    assert out.configured_provider == "vault_stub"
    assert out.rotation_max_age_days == 30
    assert out.rotation_within_policy is True
    assert out.rotation_age_days is not None
    assert out.rotation_age_days <= 30
    assert out.blockers == []


def test_gateway_live_custody_keys_contract(monkeypatch):
    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_custody_provider", "vault_stub")
    monkeypatch.setattr(live_routes.settings, "live_custody_key_id", "vault://coinbase/key/main")
    monkeypatch.setattr(live_routes.settings, "live_custody_secret_id", "vault://coinbase/secret/main")
    monkeypatch.setattr(
        live_routes.settings,
        "live_custody_last_rotated_at",
        (datetime.now(timezone.utc) - timedelta(days=4)).isoformat(),
    )
    monkeypatch.setattr(live_routes.settings, "live_custody_rotation_max_age_days", 30)

    out = asyncio.run(live_routes.custody_keys())
    assert out.configured_provider == "vault_stub"
    assert out.provider == "coinbase:vault_stub"
    assert out.key_present is True
    assert out.secret_present is True
    assert out.key_id is not None
    assert out.secret_id is not None
    assert out.rotation_within_policy is True
    assert out.verify_ready is True
    assert out.execution_disabled is True


def test_gateway_live_custody_keys_verify_contract(monkeypatch):
    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_custody_provider", "env")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_key", "abc123")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_secret", "xyz789")
    monkeypatch.setattr(
        live_routes.settings,
        "live_custody_last_rotated_at",
        (datetime.now(timezone.utc) - timedelta(days=8)).isoformat(),
    )
    monkeypatch.setattr(live_routes.settings, "live_custody_rotation_max_age_days", 30)

    out = asyncio.run(
        live_routes.custody_keys_verify(
            LiveCustodyKeyVerifyRequest(
                operator="ops-oncall",
                ticket_id="SEC-2042",
                note="verification before cutover",
                strict=True,
            )
        )
    )
    assert out.configured_provider == "env"
    assert out.provider == "coinbase"
    assert out.strict is True
    assert out.verified is True
    assert out.reason == "custody_key_verification_passed"
    check_ids = {item["id"] for item in out.checks}
    assert "phase2_metadata_only" in check_ids
    assert out.blockers == []


def test_gateway_live_custody_keys_verify_non_strict_rotation_breach_contract(monkeypatch):
    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_custody_provider", "env")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_key", "abc123")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_secret", "xyz789")
    monkeypatch.setattr(
        live_routes.settings,
        "live_custody_last_rotated_at",
        (datetime.now(timezone.utc) - timedelta(days=120)).isoformat(),
    )
    monkeypatch.setattr(live_routes.settings, "live_custody_rotation_max_age_days", 30)

    out = asyncio.run(
        live_routes.custody_keys_verify(
            LiveCustodyKeyVerifyRequest(
                operator="ops-oncall",
                ticket_id="SEC-2043",
                strict=False,
            )
        )
    )
    assert out.strict is False
    assert out.verified is True
    assert "custody_rotation_sla_breached" in out.blockers


def test_gateway_live_custody_rotation_plan_contract(monkeypatch):
    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_custody_provider", "vault_stub")
    monkeypatch.setattr(live_routes.settings, "live_custody_key_id", "vault://coinbase/key/main")
    monkeypatch.setattr(live_routes.settings, "live_custody_secret_id", "vault://coinbase/secret/main")
    monkeypatch.setattr(
        live_routes.settings,
        "live_custody_last_rotated_at",
        (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
    )
    monkeypatch.setattr(live_routes.settings, "live_custody_rotation_max_age_days", 30)

    out = asyncio.run(live_routes.custody_rotation_plan())
    assert out.configured_provider == "vault_stub"
    assert out.rotation_within_policy is True
    assert out.rotation_required is False
    assert out.recommended_action == "no_action"
    assert out.blockers == []


def test_gateway_live_custody_rotation_run_contract(monkeypatch):
    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_custody_provider", "env")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_key", "abc123")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_secret", "xyz789")
    monkeypatch.setattr(
        live_routes.settings,
        "live_custody_last_rotated_at",
        (datetime.now(timezone.utc) - timedelta(days=120)).isoformat(),
    )
    monkeypatch.setattr(live_routes.settings, "live_custody_rotation_max_age_days", 30)

    out = asyncio.run(
        live_routes.custody_rotation_run(
            live_routes.LiveCustodyRotationRunRequest(
                operator="ops-oncall",
                note="quarterly-rotation",
                ticket_id="SEC-1234",
                force=True,
            )
        )
    )
    assert out.attempted is True
    assert out.accepted is False
    assert out.executed is False
    assert out.operator == "ops-oncall"
    assert out.ticket_id == "SEC-1234"
    assert "phase2_custody_key_management_disabled" in out.blockers
    assert "phase2_custody_key_management_disabled" in out.reason


def test_gateway_live_execution_providers_contract(monkeypatch):
    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_execution_sandbox_enabled", True)
    monkeypatch.setattr(live_routes.settings, "live_execution_provider", "coinbase_sandbox")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_key", "abc123")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_secret", "xyz789")
    monkeypatch.setattr(live_routes.settings, "coinbase_use_sandbox", True)

    out = asyncio.run(live_routes.execution_providers())
    assert out.sandbox_enabled is True
    assert out.configured_provider == "coinbase_sandbox"
    assert len(out.providers) >= 2
    selected = {item.name: item for item in out.providers}
    assert "mock" in selected
    assert "coinbase_sandbox" in selected
    assert selected["coinbase_sandbox"].configured is True
    assert selected["coinbase_sandbox"].enabled is True
    assert selected["coinbase_sandbox"].ready is True


def test_gateway_live_execution_submissions_list_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
        created_at = "2026-03-11T08:20:00Z"
        intent_id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        mode = "sandbox_submit"
        provider = "mock"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "submitted_sandbox"
        accepted = True
        execution_disabled = False
        reason = "submitted_to_exchange_sandbox"
        venue = "coinbase"
        venue_order_id = "sbox-coinbase-livedryrun001"
        submitted_at = "2026-03-11T08:20:00Z"
        sandbox = True
        blockers = []
        request_payload = {"intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56", "mode": "sandbox_submit"}
        response_payload = {"accepted": True}

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [_Row()]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(live_routes.execution_submissions(limit=20))
    assert len(out.submissions) == 1
    assert out.submissions[0].mode == "sandbox_submit"
    assert out.submissions[0].provider == "mock"
    assert out.submissions[0].accepted is True


def test_gateway_live_execution_submission_get_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
        created_at = "2026-03-11T08:20:00Z"
        intent_id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        mode = "sandbox_submit"
        provider = "mock"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "submitted_sandbox"
        accepted = True
        execution_disabled = False
        reason = "submitted_to_exchange_sandbox"
        venue = "coinbase"
        venue_order_id = "sbox-coinbase-livedryrun001"
        submitted_at = "2026-03-11T08:20:00Z"
        sandbox = True
        blockers = []
        request_payload = {"intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56", "mode": "sandbox_submit"}
        response_payload = {"accepted": True}

    class _Result:
        def scalar_one_or_none(self):
            return _Row()

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(live_routes.execution_submission_get("8c2192ca-9bf3-4c27-a366-6f9ad30089dd"))
    assert out.id == "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
    assert out.provider == "mock"
    assert out.accepted is True


def test_gateway_live_execution_submission_sync_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
        created_at = "2026-03-11T08:20:00Z"
        intent_id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        mode = "sandbox_submit"
        provider = "mock"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "submitted_sandbox"
        accepted = True
        execution_disabled = False
        reason = "submitted_to_exchange_sandbox"
        venue = "coinbase"
        venue_order_id = "sbox-coinbase-livedryrun001"
        submitted_at = "2026-03-11T08:20:00Z"
        sandbox = True
        blockers = []
        request_payload = {"intent_id": "2d8f5913-4dc3-4924-af80-574147f38b56", "mode": "sandbox_submit"}
        response_payload = {"accepted": True}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item
            return None

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(live_routes.execution_submission_sync("8c2192ca-9bf3-4c27-a366-6f9ad30089dd"))
    assert out.synced is True
    assert out.order_status == "open"
    assert out.transport == "stub"
    assert out.submission.status == "submitted_sandbox"
    assert "last_status_sync" in out.submission.response_payload


def test_gateway_live_execution_submission_sync_rejects_invalid_id():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.execution_submission_sync("not-a-uuid"))
    assert exc.value.status_code == 400


def test_gateway_live_execution_submissions_summary_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        def __init__(self, *, status: str, accepted: bool, mode: str, provider: str):
            self.id = "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
            self.created_at = "2026-03-11T08:20:00Z"
            self.intent_id = "2d8f5913-4dc3-4924-af80-574147f38b56"
            self.mode = mode
            self.provider = provider
            self.symbol = "SOL-USD"
            self.side = "buy"
            self.quantity = 1.0
            self.order_type = "market"
            self.limit_price = None
            self.venue_preference = None
            self.client_order_id = "live-dryrun-001"
            self.status = status
            self.accepted = accepted
            self.execution_disabled = not accepted
            self.reason = "submitted_to_exchange_sandbox" if accepted else "execution_disabled_flag"
            self.venue = "coinbase" if accepted else None
            self.venue_order_id = "sbox-coinbase-livedryrun001" if accepted else None
            self.submitted_at = "2026-03-11T08:20:00Z" if accepted else None
            self.sandbox = True
            self.blockers = [] if accepted else ["execution_disabled_flag"]
            self.request_payload = {"mode": mode}
            self.response_payload = {"accepted": accepted}

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [
                _Row(status="submitted_sandbox", accepted=True, mode="sandbox_submit", provider="mock"),
                _Row(status="submit_blocked_dry_run", accepted=False, mode="dry_run", provider="none"),
            ]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(live_routes.execution_submissions_summary(window_hours=24, limit=200))
    assert out.total_submissions == 2
    assert out.accepted_count == 1
    assert out.blocked_count == 1
    assert out.by_mode["sandbox_submit"] == 1
    assert out.by_mode["dry_run"] == 1


def test_gateway_live_execution_place_analytics_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        created_at = _Col()
        mode = _Col()
        symbol = _Col()
        provider = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        def __init__(self, *, status: str, accepted: bool, provider: str, blockers: list[str]):
            self.id = "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
            self.created_at = "2026-03-11T08:20:00Z"
            self.mode = "live_place"
            self.provider = provider
            self.symbol = "SOL-USD"
            self.status = status
            self.accepted = accepted
            self.blockers = blockers

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [
                _Row(
                    status="submit_blocked_live",
                    accepted=False,
                    provider="coinbase_sandbox",
                    blockers=["phase2_live_execution_path_disabled"],
                ),
                _Row(
                    status="submit_blocked_live",
                    accepted=False,
                    provider="coinbase_sandbox",
                    blockers=["deployment_not_armed", "phase2_live_execution_path_disabled"],
                ),
            ]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(live_routes.execution_place_analytics(symbol="SOL-USD", window_hours=24, limit=200))
    assert out.total_attempts == 2
    assert out.accepted_count == 0
    assert out.blocked_count == 2
    assert out.by_provider["coinbase_sandbox"] == 2
    assert out.by_status["submit_blocked_live"] == 2
    assert out.blocker_counts["phase2_live_execution_path_disabled"] == 2
    assert out.blocker_counts["deployment_not_armed"] == 1


def test_gateway_live_execution_place_analytics_rejects_nonpositive_window():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.execution_place_analytics(window_hours=0))
    assert exc.value.status_code == 400


def test_gateway_live_execution_place_strategy_analytics_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        created_at = _Col()
        mode = _Col()
        symbol = _Col()
        provider = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        def __init__(
            self,
            *,
            created_at: str,
            requested_strategy: str,
            resolved_strategy: str,
            resolution_reason: str | None,
            resolution_tie_break_reason: str | None,
            feasible_route: bool,
            provider_compatible: bool,
            blockers: list[str],
            estimated_cost_bps: float | None = None,
            nested_estimated_cost_bps: float | None = None,
            allocation_coverage_ratio: float | None = None,
            allocation_shortfall_quantity: float | None = None,
            nested_allocation_coverage_ratio: float | None = None,
            nested_allocation_shortfall_quantity: float | None = None,
        ):
            self.id = "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
            self.created_at = created_at
            self.mode = "live_place"
            self.provider = "coinbase_sandbox"
            self.symbol = "SOL-USD"
            self.status = "submit_blocked_live"
            self.accepted = False
            self.blockers = blockers
            self.request_payload = {"strategy": requested_strategy}
            self.response_payload = {
                "strategy": resolved_strategy,
                "requested_strategy": requested_strategy,
                "resolved_strategy": resolved_strategy,
                "strategy_resolution_reason": resolution_reason,
                "strategy_resolution_tie_break_reason": resolution_tie_break_reason,
                "feasible_route": feasible_route,
                "provider_venue_compatible": provider_compatible,
                "total_estimated_cost_bps": estimated_cost_bps,
                "recommended_slices": [],
                "rejected_venues": [],
                "allocation_coverage_ratio": allocation_coverage_ratio,
                "allocation_shortfall_quantity": allocation_shortfall_quantity,
            }
            if nested_estimated_cost_bps is not None:
                self.response_payload["live_place_attempt"] = {
                    "total_estimated_cost_bps": nested_estimated_cost_bps,
                    "recommended_slices": [
                        {"venue": "coinbase", "ratio": 0.6, "quantity": 0.6, "ratio_capped": True}
                    ],
                    "rejected_venues": [
                        {"venue": "kraken", "reason": "min_venues_not_met"},
                    ],
                    "allocation_coverage_ratio": nested_allocation_coverage_ratio,
                    "allocation_shortfall_quantity": nested_allocation_shortfall_quantity,
                }

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [
                _Row(
                    created_at="2026-03-11T08:20:00Z",
                    requested_strategy="auto",
                    resolved_strategy="single_venue",
                    resolution_reason="feasible_route_with_lowest_blockers",
                    resolution_tie_break_reason="lowest_estimated_cost_bps",
                    feasible_route=True,
                    provider_compatible=True,
                    blockers=["phase2_live_execution_path_disabled"],
                    estimated_cost_bps=8.0,
                    allocation_coverage_ratio=1.0,
                    allocation_shortfall_quantity=0.0,
                ),
                _Row(
                    created_at="2026-03-11T08:15:00Z",
                    requested_strategy="multi_venue",
                    resolved_strategy="multi_venue",
                    resolution_reason=None,
                    resolution_tie_break_reason=None,
                    feasible_route=False,
                    provider_compatible=False,
                    blockers=[
                        "phase2_live_execution_path_disabled",
                        "provider_venue_mismatch",
                        "route_not_feasible",
                        "allocation_min_venues_not_met",
                    ],
                    estimated_cost_bps=None,
                    nested_estimated_cost_bps=12.0,
                    nested_allocation_coverage_ratio=0.6,
                    nested_allocation_shortfall_quantity=0.4,
                ),
            ]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_strategy_analytics(symbol="SOL-USD", provider="coinbase_sandbox", window_hours=24)
    )
    assert out.total_attempts == 2
    assert out.by_requested_strategy["auto"] == 1
    assert out.by_requested_strategy["multi_venue"] == 1
    assert out.by_resolved_strategy["single_venue"] == 1
    assert out.by_resolved_strategy["multi_venue"] == 1
    assert out.requested_resolved_transitions["auto->single_venue"] == 1
    assert out.requested_resolved_transitions["multi_venue->multi_venue"] == 1
    assert out.by_resolution_reason["feasible_route_with_lowest_blockers"] == 1
    assert out.by_resolution_tie_break_reason["lowest_estimated_cost_bps"] == 1
    assert out.auto_resolution_rate == 1.0
    assert out.auto_resolved_to_intent_count == 0
    assert out.auto_resolved_to_intent_rate == 0.0
    assert out.estimated_cost_samples == 2
    assert out.avg_estimated_cost_bps == 10.0
    assert out.min_estimated_cost_bps == 8.0
    assert out.max_estimated_cost_bps == 12.0
    assert out.avg_estimated_cost_bps_by_requested_strategy["auto"] == 8.0
    assert out.avg_estimated_cost_bps_by_requested_strategy["multi_venue"] == 12.0
    assert out.avg_estimated_cost_bps_by_resolved_strategy["single_venue"] == 8.0
    assert out.avg_estimated_cost_bps_by_resolved_strategy["multi_venue"] == 12.0
    assert out.auto_avg_estimated_cost_bps == 8.0
    assert out.non_auto_avg_estimated_cost_bps == 12.0
    assert out.auto_vs_non_auto_cost_delta_bps == -4.0
    assert out.allocation_rejection_counts["min_venues_not_met"] == 1
    assert out.allocation_blocker_counts["allocation_min_venues_not_met"] == 1
    assert out.avg_allocation_coverage_ratio == 0.8
    assert out.avg_allocation_coverage_ratio_by_requested_strategy["auto"] == 1.0
    assert out.avg_allocation_coverage_ratio_by_requested_strategy["multi_venue"] == 0.6
    assert out.avg_allocation_coverage_ratio_by_resolved_strategy["single_venue"] == 1.0
    assert out.avg_allocation_coverage_ratio_by_resolved_strategy["multi_venue"] == 0.6
    assert out.allocation_shortfall_attempt_count == 1
    assert out.allocation_shortfall_attempt_rate == 0.5
    assert out.constraint_failure_attempt_count == 1
    assert out.constraint_failure_attempt_rate == 0.5
    assert out.ratio_capped_attempt_count == 1
    assert out.ratio_capped_attempt_rate == 0.5
    assert out.provider_venue_compatible_count == 1
    assert out.provider_venue_mismatch_count == 1
    assert out.provider_venue_compatible_rate == 0.5
    assert out.route_feasible_count == 1
    assert out.route_not_feasible_count == 1
    assert out.route_feasible_rate == 0.5


def test_gateway_live_execution_place_strategy_analytics_rejects_nonpositive_window():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.execution_place_strategy_analytics(window_hours=0))
    assert exc.value.status_code == 400


def test_gateway_live_execution_place_strategy_analytics_rejects_invalid_min_coverage_ratio():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.execution_place_strategy_analytics(min_coverage_ratio=1.2))
    assert exc.value.status_code == 400


def test_gateway_live_execution_place_strategy_analytics_filters_by_strategy(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        created_at = _Col()
        mode = _Col()
        symbol = _Col()
        provider = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        def __init__(self, *, requested_strategy: str, resolved_strategy: str, cost: float):
            self.id = "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
            self.created_at = "2026-03-11T08:20:00Z"
            self.mode = "live_place"
            self.provider = "coinbase_sandbox"
            self.symbol = "SOL-USD"
            self.status = "submit_blocked_live"
            self.accepted = False
            self.blockers = ["phase2_live_execution_path_disabled"]
            self.request_payload = {"strategy": requested_strategy}
            self.response_payload = {
                "strategy": resolved_strategy,
                "requested_strategy": requested_strategy,
                "resolved_strategy": resolved_strategy,
                "strategy_resolution_reason": "feasible_route_with_lowest_blockers",
                "feasible_route": True,
                "provider_venue_compatible": True,
                "total_estimated_cost_bps": cost,
                "recommended_slices": [],
                "rejected_venues": [],
            }

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [
                _Row(requested_strategy="auto", resolved_strategy="single_venue", cost=8.0),
                _Row(requested_strategy="multi_venue", resolved_strategy="multi_venue", cost=12.0),
            ]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_strategy_analytics(
            symbol="SOL-USD",
            provider="coinbase_sandbox",
            requested_strategy="auto",
            resolved_strategy="single_venue",
            window_hours=24,
        )
    )
    assert out.total_attempts == 1
    assert out.by_requested_strategy == {"auto": 1}
    assert out.by_resolved_strategy == {"single_venue": 1}
    assert out.avg_estimated_cost_bps == 8.0
    assert out.route_feasible_count == 1
    assert out.route_feasible_rate == 1.0


def test_gateway_live_execution_place_strategy_analytics_filters_by_shortfall_and_coverage(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        created_at = _Col()
        mode = _Col()
        symbol = _Col()
        provider = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        def __init__(
            self,
            *,
            requested_strategy: str,
            resolved_strategy: str,
            coverage_ratio: float,
            shortfall_quantity: float,
        ):
            self.id = "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
            self.created_at = "2026-03-11T08:20:00Z"
            self.mode = "live_place"
            self.provider = "coinbase_sandbox"
            self.symbol = "SOL-USD"
            self.status = "submit_blocked_live"
            self.accepted = False
            self.blockers = ["phase2_live_execution_path_disabled"]
            if shortfall_quantity > 0:
                self.blockers.append("allocation_quantity_shortfall")
            self.request_payload = {"strategy": requested_strategy}
            self.response_payload = {
                "strategy": resolved_strategy,
                "requested_strategy": requested_strategy,
                "resolved_strategy": resolved_strategy,
                "strategy_resolution_reason": "feasible_route_with_lowest_blockers",
                "feasible_route": shortfall_quantity <= 0,
                "provider_venue_compatible": True,
                "total_estimated_cost_bps": 8.0,
                "recommended_slices": [],
                "rejected_venues": (
                    [{"reason": "quantity_shortfall"}]
                    if shortfall_quantity > 0
                    else []
                ),
                "allocation_coverage_ratio": coverage_ratio,
                "allocation_shortfall_quantity": shortfall_quantity,
            }

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [
                _Row(
                    requested_strategy="auto",
                    resolved_strategy="single_venue",
                    coverage_ratio=1.0,
                    shortfall_quantity=0.0,
                ),
                _Row(
                    requested_strategy="multi_venue",
                    resolved_strategy="multi_venue",
                    coverage_ratio=0.6,
                    shortfall_quantity=0.4,
                ),
            ]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    shortfall_out = asyncio.run(
        live_routes.execution_place_strategy_analytics(
            symbol="SOL-USD",
            provider="coinbase_sandbox",
            has_shortfall=True,
            window_hours=24,
        )
    )
    assert shortfall_out.total_attempts == 1
    assert shortfall_out.by_requested_strategy == {"multi_venue": 1}
    assert shortfall_out.allocation_shortfall_attempt_count == 1

    coverage_out = asyncio.run(
        live_routes.execution_place_strategy_analytics(
            symbol="SOL-USD",
            provider="coinbase_sandbox",
            min_coverage_ratio=0.9,
            window_hours=24,
        )
    )
    assert coverage_out.total_attempts == 1
    assert coverage_out.by_requested_strategy == {"auto": 1}
    assert coverage_out.avg_allocation_coverage_ratio == 1.0


def test_gateway_live_execution_place_strategy_analytics_tracks_transitions_and_auto_intent_fallback(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        created_at = _Col()
        mode = _Col()
        symbol = _Col()
        provider = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        def __init__(self, *, requested_strategy: str, resolved_strategy: str):
            self.id = "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
            self.created_at = "2026-03-11T08:20:00Z"
            self.mode = "live_place"
            self.provider = "coinbase_sandbox"
            self.symbol = "SOL-USD"
            self.status = "submit_blocked_live"
            self.accepted = False
            self.blockers = ["phase2_live_execution_path_disabled"]
            self.request_payload = {"strategy": requested_strategy}
            self.response_payload = {
                "strategy": resolved_strategy,
                "requested_strategy": requested_strategy,
                "resolved_strategy": resolved_strategy,
                "strategy_resolution_reason": "feasible_route_with_lowest_blockers",
                "feasible_route": True,
                "provider_venue_compatible": True,
                "total_estimated_cost_bps": 8.0,
                "recommended_slices": [],
                "rejected_venues": [],
            }

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [
                _Row(requested_strategy="auto", resolved_strategy="intent"),
                _Row(requested_strategy="auto", resolved_strategy="single_venue"),
                _Row(requested_strategy="intent", resolved_strategy="intent"),
            ]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_strategy_analytics(
            symbol="SOL-USD",
            provider="coinbase_sandbox",
            window_hours=24,
        )
    )
    assert out.total_attempts == 3
    assert out.requested_resolved_transitions == {
        "auto->intent": 1,
        "auto->single_venue": 1,
        "intent->intent": 1,
    }
    assert out.auto_resolution_rate == 1.0
    assert out.auto_resolved_to_intent_count == 1
    assert out.auto_resolved_to_intent_rate == 0.5


def test_gateway_live_execution_submissions_bulk_sync_contract(monkeypatch):
    class _Col:
        def desc(self):
            return self

    class _Model:
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        def __init__(self, sid: str, status: str):
            self.id = sid
            self.status = status

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [
                _Row("8c2192ca-9bf3-4c27-a366-6f9ad3008901", "submitted_sandbox"),
                _Row("8c2192ca-9bf3-4c27-a366-6f9ad3008902", "submitted_sandbox"),
            ]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    class _Submission:
        def __init__(self, status: str):
            self.status = status

    class _SyncOut:
        def __init__(self, *, status: str):
            self.synced = True
            self.order_status = "open"
            self.transport = "stub"
            self.submission = _Submission(status)

    async def _fake_sync(submission_id: str):
        if submission_id.endswith("02"):
            raise HTTPException(status_code=503, detail="sync_failed")
        return _SyncOut(status="submitted_sandbox")

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "execution_submission_sync", _fake_sync)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(live_routes.execution_submissions_sync(limit=20))
    assert out.total_candidates == 2
    assert out.synced_count == 1
    assert out.failed_count == 1
    assert len(out.items) == 2
    assert out.items[0].synced is True
    assert out.items[1].synced is False
    assert out.items[1].error == "sync_failed"


def test_gateway_live_execution_submissions_retention_contract(monkeypatch):
    class _Col:
        def __lt__(self, other):
            _ = other
            return self

    class _Model:
        created_at = _Col()

    class _Query:
        def filter(self, *_args, **_kwargs):
            return self

        def delete(self, synchronize_session=False):
            _ = synchronize_session
            return 4

    class _DB:
        def query(self, model):
            _ = model
            return _Query()

        def commit(self):
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(live_routes.execution_submissions_retention({"days": 90}))
    assert out.retention_days == 90
    assert out.deleted_submissions == 4
    assert out.execution_disabled is True


def test_gateway_live_execution_submissions_retention_rejects_nonpositive_days():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.execution_submissions_retention({"days": 0}))
    assert exc.value.status_code == 400


def test_gateway_live_execution_order_status_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        venue_order_id = _Col()
        id = _Col()
        provider = _Col()
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
        created_at = "2026-03-11T08:20:00Z"
        intent_id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        mode = "sandbox_submit"
        provider = "mock"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "submitted_sandbox"
        accepted = True
        execution_disabled = False
        reason = "submitted_to_exchange_sandbox"
        venue = "coinbase"
        venue_order_id = "sbox-coinbase-livedryrun001"
        submitted_at = "2026-03-11T08:20:00Z"
        sandbox = True
        blockers = []
        request_payload = {}
        response_payload = {"transport": "stub"}

    class _Result:
        def scalar_one_or_none(self):
            return _Row()

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_order_status(
            "sbox-coinbase-livedryrun001",
            submission_id="8c2192ca-9bf3-4c27-a366-6f9ad30089dd",
        )
    )
    assert out.submission_id == "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
    assert out.provider == "mock"
    assert out.order_status == "open"
    assert out.accepted is True


def test_gateway_live_execution_order_cancel_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        venue_order_id = _Col()
        id = _Col()
        provider = _Col()
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
        created_at = "2026-03-11T08:20:00Z"
        intent_id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        mode = "sandbox_submit"
        provider = "mock"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "submitted_sandbox"
        accepted = True
        execution_disabled = False
        reason = "submitted_to_exchange_sandbox"
        venue = "coinbase"
        venue_order_id = "sbox-coinbase-livedryrun001"
        submitted_at = "2026-03-11T08:20:00Z"
        sandbox = True
        blockers = []
        request_payload = {}
        response_payload = {"transport": "stub"}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveExecutionSubmission", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_execution_sandbox_transport_enabled", False)

    out = asyncio.run(
        live_routes.execution_order_cancel(
            "sbox-coinbase-livedryrun001",
            live_routes.LiveExecutionOrderCancelRequest(
                submission_id="8c2192ca-9bf3-4c27-a366-6f9ad30089dd",
                provider="mock",
                reason="operator_cancel",
            ),
        )
    )
    assert out.submission_id == "8c2192ca-9bf3-4c27-a366-6f9ad30089dd"
    assert out.cancel_requested is True
    assert out.canceled is True
    assert out.order_status == "canceled"
    assert row.status == "canceled_sandbox"


def test_gateway_live_execution_place_preflight_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        symbol = "SOL-USD"
        approved_for_live = True
        route_plan = {"selected_venue": "coinbase"}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes.settings, "execution_enabled", True)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_preflight(
            LiveExecutionPlacePreflightRequest(
                intent_id="2d8f5913-4dc3-4924-af80-574147f38b56",
                provider="coinbase_sandbox",
                venue="coinbase",
            )
        )
    )
    assert out.intent_id == "2d8f5913-4dc3-4924-af80-574147f38b56"
    assert out.ready_for_live_placement is False
    assert "phase2_safety_block" in out.blockers
    check_ids = {item["id"] for item in out.checks}
    assert "phase2_safety_block" in check_ids
    assert out.execution_disabled is True


def test_gateway_live_execution_place_preflight_rejects_invalid_intent_id(monkeypatch):
    class _Model:
        pass

    class _Session:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            live_routes.execution_place_preflight(
                LiveExecutionPlacePreflightRequest(intent_id="bad-intent-id")
            )
        )
    assert exc.value.status_code == 400


def test_gateway_live_execution_place_preview_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.5
        order_type = "market"
        limit_price = None
        client_order_id = "live-dryrun-001"
        approved_for_live = True

    class _Result:
        def scalar_one_or_none(self):
            return _Row()

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "live_execution_sandbox_enabled", True)

    out = asyncio.run(
        live_routes.execution_place_preview(
            LiveExecutionPlacePreviewRequest(
                intent_id="2d8f5913-4dc3-4924-af80-574147f38b56",
                provider="mock",
                venue="coinbase",
                mode="sandbox_submit",
            )
        )
    )
    assert out.intent_id == "2d8f5913-4dc3-4924-af80-574147f38b56"
    assert out.provider == "mock"
    assert out.mode == "sandbox_submit"
    assert out.can_submit is True
    assert out.transport == "stub"
    assert out.payload["symbol"] == "SOL-USD"
    assert out.blockers == []


def test_gateway_live_execution_place_preview_rejects_invalid_intent_id(monkeypatch):
    class _Model:
        pass

    class _Session:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            live_routes.execution_place_preview(
                LiveExecutionPlacePreviewRequest(intent_id="bad-intent-id")
            )
        )
    assert exc.value.status_code == 400


def test_gateway_live_execution_place_route_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 2.0
        order_type = "market"
        approved_for_live = True

    class _Result:
        def scalar_one_or_none(self):
            return _Row()

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_route_plan(req):
        assert req.symbol == "SOL-USD"
        return live_routes.LiveRoutePlanResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=2.0,
            order_type="market",
            candidates=[
                {
                    "venue": "coinbase",
                    "score": 10.0,
                    "estimated_cost_bps": 8.0,
                    "route_eligible": True,
                }
            ],
            rejected_venues=[],
            selected_venue="coinbase",
            selected_reason="lowest_estimated_cost",
            routing_policy={"max_spread_bps": 20.0},
            route_eligible=True,
            execution_disabled=True,
        )

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "route_plan", _fake_route_plan)
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_route(
            LiveExecutionPlaceRouteRequest(
                intent_id="2d8f5913-4dc3-4924-af80-574147f38b56",
                provider="coinbase_sandbox",
                strategy="single_venue",
            )
        )
    )
    assert out.intent_id == "2d8f5913-4dc3-4924-af80-574147f38b56"
    assert out.provider == "coinbase_sandbox"
    assert out.selected_venue == "coinbase"
    assert out.route_eligible is True
    assert out.feasible_route is True
    assert out.provider_supported_venues == ["coinbase"]
    assert out.provider_venue_compatible is True
    assert out.custody_ready is True
    assert out.risk_gate == "ALLOW"
    assert "phase2_live_execution_path_disabled" in out.blockers
    assert out.execution_disabled is True


def test_gateway_live_execution_place_route_multi_venue_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "4f4dfaa5-7c22-46e0-8a1c-8c220f9d6db1"
        symbol = "SOL-USD"
        side = "sell"
        quantity = 3.0
        order_type = "market"
        approved_for_live = True

    class _Result:
        def scalar_one_or_none(self):
            return _Row()

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_allocation(req):
        assert req.symbol == "SOL-USD"
        assert req.side == "sell"
        return live_routes.LiveRouteAllocationResponse(
            symbol="SOL-USD",
            side="sell",
            quantity=3.0,
            order_type="market",
            feasible_route=True,
            recommended_slices=[
                {"venue": "kraken", "quantity": 1.8, "weight": 0.6},
                {"venue": "coinbase", "quantity": 1.2, "weight": 0.4},
            ],
            rejected_venues=[],
            routing_policy={"max_estimated_cost_bps": 30.0},
            total_estimated_cost_bps=11.2,
            execution_disabled=True,
        )

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "router_allocation", _fake_allocation)
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_route(
            LiveExecutionPlaceRouteRequest(
                intent_id="4f4dfaa5-7c22-46e0-8a1c-8c220f9d6db1",
                provider="coinbase_sandbox",
                strategy="multi_venue",
                max_venues=2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.intent_id == "4f4dfaa5-7c22-46e0-8a1c-8c220f9d6db1"
    assert out.strategy == "multi_venue"
    assert out.selected_venue == "coinbase"
    assert out.selected_reason == "allocation_top_slice_provider_compatible"
    assert out.route_eligible is True
    assert out.feasible_route is False
    assert len(out.recommended_slices) == 1
    assert out.recommended_slices[0]["venue"] == "coinbase"
    assert out.requested_quantity == 3.0
    assert out.allocated_quantity == 1.2
    assert out.allocation_coverage_ratio == 0.4
    assert out.allocation_shortfall_quantity == 1.8
    assert out.total_estimated_cost_bps == 11.2
    assert any(item.get("reason") == "provider_venue_not_supported" for item in out.rejected_venues)
    assert any(item.get("reason") == "quantity_shortfall" for item in out.rejected_venues)
    assert out.provider_supported_venues == ["coinbase"]
    assert out.provider_venue_compatible is True
    assert out.candidates == []
    assert "allocation_quantity_shortfall" in out.blockers
    assert "route_not_feasible" in out.blockers
    assert "phase2_live_execution_path_disabled" in out.blockers


def test_gateway_live_execution_place_route_multi_venue_surfaces_allocation_rejection_blockers(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "e5fdb57c-62ce-4d2f-8d4f-4f8f09f57c1a"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 0.5
        order_type = "market"
        approved_for_live = True

    class _Result:
        def scalar_one_or_none(self):
            return _Row()

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_allocation(req):
        assert req.symbol == "SOL-USD"
        assert req.side == "buy"
        return live_routes.LiveRouteAllocationResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=0.5,
            order_type="market",
            feasible_route=False,
            recommended_slices=[],
            rejected_venues=[
                {"venue": "coinbase", "reason": "min_slice_quantity_not_met"},
                {"reason": "min_slice_quantity_unachievable"},
            ],
            routing_policy={"max_estimated_cost_bps": 30.0},
            total_estimated_cost_bps=None,
            execution_disabled=True,
        )

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "router_allocation", _fake_allocation)
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_route(
            LiveExecutionPlaceRouteRequest(
                intent_id="e5fdb57c-62ce-4d2f-8d4f-4f8f09f57c1a",
                provider="coinbase_sandbox",
                strategy="multi_venue",
                max_venues=2,
                min_venues=1,
                max_venue_ratio=0.7,
                min_slice_quantity=0.3,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.feasible_route is False
    assert out.recommended_slices == []
    assert "allocation_min_slice_quantity_not_met" in out.blockers
    assert "allocation_min_slice_quantity_unachievable" in out.blockers
    assert "route_not_feasible" in out.blockers
    assert "phase2_live_execution_path_disabled" in out.blockers


def test_gateway_live_execution_place_route_intent_strategy_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "84f216c5-d7fb-4f5f-a150-8ca5f33aa918"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.2
        order_type = "market"
        venue_preference = "binance"
        route_plan = {"selected_venue": "coinbase"}
        approved_for_live = True

    class _Result:
        def scalar_one_or_none(self):
            return _Row()

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_route(
            LiveExecutionPlaceRouteRequest(
                intent_id="84f216c5-d7fb-4f5f-a150-8ca5f33aa918",
                provider="coinbase_sandbox",
                strategy="intent",
            )
        )
    )
    assert out.intent_id == "84f216c5-d7fb-4f5f-a150-8ca5f33aa918"
    assert out.strategy == "intent"
    assert out.selected_venue == "binance"
    assert out.route_eligible is True
    assert out.feasible_route is False
    assert out.selected_reason == "intent_route_plan"
    assert out.recommended_slices[0]["venue"] == "binance"
    assert out.provider_supported_venues == ["coinbase"]
    assert out.provider_venue_compatible is False
    assert "provider_venue_mismatch" in out.blockers
    assert "route_not_feasible" in out.blockers
    assert "phase2_live_execution_path_disabled" in out.blockers


def test_gateway_live_execution_place_route_compare_contract(monkeypatch):
    async def _fake_route(req):
        base = {
            "as_of": datetime.now(timezone.utc),
            "intent_id": req.intent_id,
            "symbol": "SOL-USD",
            "provider": "coinbase_sandbox",
            "execution_disabled": True,
        }
        if req.strategy == "intent":
            return live_routes.LiveExecutionPlaceRouteResponse(
                **base,
                strategy="intent",
                selected_venue="coinbase",
                selected_reason="intent_route_plan",
                route_eligible=True,
                feasible_route=True,
                blockers=["phase2_live_execution_path_disabled"],
                requested_quantity=3.0,
                allocated_quantity=3.0,
                allocation_coverage_ratio=1.0,
                allocation_shortfall_quantity=0.0,
                total_estimated_cost_bps=9.6,
                recommended_slices=[{"venue": "coinbase", "quantity": 1.0, "weight": 1.0}],
            )
        if req.strategy == "single_venue":
            return live_routes.LiveExecutionPlaceRouteResponse(
                **base,
                strategy="single_venue",
                selected_venue="coinbase",
                selected_reason="lowest_estimated_cost",
                route_eligible=True,
                feasible_route=False,
                blockers=["phase2_live_execution_path_disabled", "route_not_feasible"],
                requested_quantity=3.0,
                allocated_quantity=3.0,
                allocation_coverage_ratio=1.0,
                allocation_shortfall_quantity=0.0,
                candidates=[{"venue": "coinbase", "estimated_cost_bps": 8.0}],
                total_estimated_cost_bps=8.0,
            )
        return live_routes.LiveExecutionPlaceRouteResponse(
            **base,
            strategy="multi_venue",
            selected_venue="kraken",
            selected_reason="allocation_top_slice",
            route_eligible=True,
            feasible_route=True,
            blockers=["phase2_live_execution_path_disabled"],
            requested_quantity=3.0,
            allocated_quantity=3.0,
            allocation_coverage_ratio=1.0,
            allocation_shortfall_quantity=0.0,
            total_estimated_cost_bps=7.4,
            recommended_slices=[
                {"venue": "kraken", "quantity": 1.8, "weight": 0.6},
                {"venue": "coinbase", "quantity": 1.2, "weight": 0.4},
            ],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "execution_place_route", _fake_route)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_route_compare(
            LiveExecutionPlaceRouteCompareRequest(
                intent_id="84f216c5-d7fb-4f5f-a150-8ca5f33aa918",
                provider="coinbase_sandbox",
                strategies=["intent", "single_venue", "multi_venue"],
                max_venues=2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.intent_id == "84f216c5-d7fb-4f5f-a150-8ca5f33aa918"
    assert out.symbol == "SOL-USD"
    assert len(out.options) == 3
    assert out.recommended_strategy == "multi_venue"
    assert out.recommended_reason == "feasible_route_with_lowest_blockers_lowest_estimated_cost"
    assert out.recommended_estimated_cost_bps == 7.4
    assert out.recommended_allocation_coverage_ratio == 1.0
    assert out.recommended_allocation_shortfall_quantity == 0.0
    assert out.recommended_sort_rank == 1
    assert out.recommended_tie_break_reason == "lowest_estimated_cost_bps"
    assert {item.sort_rank for item in out.options} == {1, 2, 3}
    assert [item.strategy for item in out.options if item.recommended] == ["multi_venue"]
    assert out.options[0].allocation_coverage_ratio == 1.0
    assert out.options[0].sort_key["blocker_count"] == 1
    assert out.options[0].total_estimated_cost_bps == 9.6
    assert out.execution_disabled is True


def test_gateway_live_execution_place_route_compare_prefers_lower_cost_over_strategy_priority(monkeypatch):
    async def _fake_route(req):
        base = {
            "as_of": datetime.now(timezone.utc),
            "intent_id": req.intent_id,
            "symbol": "SOL-USD",
            "provider": "coinbase_sandbox",
            "execution_disabled": True,
            "blockers": ["phase2_live_execution_path_disabled"],
            "route_eligible": True,
            "feasible_route": True,
            "selected_venue": "coinbase",
        }
        if req.strategy == "multi_venue":
            return live_routes.LiveExecutionPlaceRouteResponse(
                **base,
                strategy="multi_venue",
                selected_reason="allocation_top_slice",
                total_estimated_cost_bps=11.0,
                recommended_slices=[{"venue": "coinbase", "quantity": 1.0, "weight": 1.0}],
            )
        return live_routes.LiveExecutionPlaceRouteResponse(
            **base,
            strategy="intent",
            selected_reason="intent_route_plan",
            total_estimated_cost_bps=6.2,
            recommended_slices=[{"venue": "coinbase", "quantity": 1.0, "weight": 1.0}],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "execution_place_route", _fake_route)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_route_compare(
            LiveExecutionPlaceRouteCompareRequest(
                intent_id="84f216c5-d7fb-4f5f-a150-8ca5f33aa918",
                provider="coinbase_sandbox",
                strategies=["intent", "multi_venue"],
                max_venues=2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.recommended_strategy == "intent"
    assert out.recommended_reason == "feasible_route_with_lowest_blockers_lowest_estimated_cost"
    assert out.recommended_estimated_cost_bps == 6.2
    assert out.recommended_tie_break_reason == "lowest_estimated_cost_bps"


def test_gateway_live_execution_place_route_compare_marks_constraint_failure_when_no_feasible_route(monkeypatch):
    async def _fake_route(req):
        base = {
            "as_of": datetime.now(timezone.utc),
            "intent_id": req.intent_id,
            "symbol": "SOL-USD",
            "provider": "coinbase_sandbox",
            "execution_disabled": True,
            "route_eligible": False,
            "feasible_route": False,
            "selected_venue": None,
        }
        if req.strategy == "multi_venue":
            return live_routes.LiveExecutionPlaceRouteResponse(
                **base,
                strategy="multi_venue",
                selected_reason="no_feasible_allocation",
                blockers=[
                    "phase2_live_execution_path_disabled",
                    "allocation_min_slice_quantity_unachievable",
                ],
                total_estimated_cost_bps=6.5,
            )
        return live_routes.LiveExecutionPlaceRouteResponse(
            **base,
            strategy="intent",
            selected_reason="intent_route_missing_selected_venue",
            blockers=["phase2_live_execution_path_disabled", "route_not_feasible"],
            total_estimated_cost_bps=9.1,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "execution_place_route", _fake_route)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_route_compare(
            LiveExecutionPlaceRouteCompareRequest(
                intent_id="84f216c5-d7fb-4f5f-a150-8ca5f33aa918",
                provider="coinbase_sandbox",
                strategies=["intent", "multi_venue"],
                max_venues=2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.recommended_strategy == "multi_venue"
    assert out.recommended_reason == "no_feasible_route_constraint_failure_lowest_blockers_lowest_estimated_cost"
    assert out.recommended_estimated_cost_bps == 6.5


def test_gateway_live_execution_place_route_compare_uses_coverage_tie_break_when_cost_equal(monkeypatch):
    async def _fake_route(req):
        base = {
            "as_of": datetime.now(timezone.utc),
            "intent_id": req.intent_id,
            "symbol": "SOL-USD",
            "provider": "coinbase_sandbox",
            "execution_disabled": True,
            "route_eligible": True,
            "feasible_route": True,
            "selected_venue": "coinbase",
            "blockers": ["phase2_live_execution_path_disabled"],
            "total_estimated_cost_bps": 8.0,
        }
        if req.strategy == "multi_venue":
            return live_routes.LiveExecutionPlaceRouteResponse(
                **base,
                strategy="multi_venue",
                selected_reason="allocation_top_slice",
                requested_quantity=3.0,
                allocated_quantity=3.0,
                allocation_coverage_ratio=1.0,
                allocation_shortfall_quantity=0.0,
                recommended_slices=[{"venue": "coinbase", "quantity": 3.0, "weight": 1.0}],
            )
        return live_routes.LiveExecutionPlaceRouteResponse(
            **base,
            strategy="intent",
            selected_reason="intent_route_plan",
            requested_quantity=3.0,
            allocated_quantity=1.8,
            allocation_coverage_ratio=0.6,
            allocation_shortfall_quantity=1.2,
            recommended_slices=[{"venue": "coinbase", "quantity": 1.8, "weight": 1.0}],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "execution_place_route", _fake_route)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_route_compare(
            LiveExecutionPlaceRouteCompareRequest(
                intent_id="84f216c5-d7fb-4f5f-a150-8ca5f33aa918",
                provider="coinbase_sandbox",
                strategies=["intent", "multi_venue"],
                max_venues=2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.recommended_strategy == "multi_venue"
    assert out.recommended_reason == "feasible_route_with_lowest_blockers"
    assert out.recommended_tie_break_reason == "highest_allocation_coverage_ratio"
    assert out.recommended_allocation_coverage_ratio == 1.0


def test_gateway_live_execution_place_route_compare_marks_capacity_shortfall_when_no_feasible_route(monkeypatch):
    async def _fake_route(req):
        base = {
            "as_of": datetime.now(timezone.utc),
            "intent_id": req.intent_id,
            "symbol": "SOL-USD",
            "provider": "coinbase_sandbox",
            "execution_disabled": True,
            "route_eligible": False,
            "feasible_route": False,
            "selected_venue": None,
        }
        if req.strategy == "multi_venue":
            return live_routes.LiveExecutionPlaceRouteResponse(
                **base,
                strategy="multi_venue",
                selected_reason="no_provider_compatible_slice",
                blockers=[
                    "phase2_live_execution_path_disabled",
                    "allocation_quantity_shortfall",
                ],
                requested_quantity=3.0,
                allocated_quantity=1.2,
                allocation_coverage_ratio=0.4,
                allocation_shortfall_quantity=1.8,
                total_estimated_cost_bps=6.5,
            )
        return live_routes.LiveExecutionPlaceRouteResponse(
            **base,
            strategy="intent",
            selected_reason="intent_route_missing_selected_venue",
            blockers=["phase2_live_execution_path_disabled", "route_not_feasible"],
            requested_quantity=3.0,
            allocated_quantity=3.0,
            allocation_coverage_ratio=1.0,
            allocation_shortfall_quantity=0.0,
            total_estimated_cost_bps=9.1,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "execution_place_route", _fake_route)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_place_route_compare(
            LiveExecutionPlaceRouteCompareRequest(
                intent_id="84f216c5-d7fb-4f5f-a150-8ca5f33aa918",
                provider="coinbase_sandbox",
                strategies=["intent", "multi_venue"],
                max_venues=2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.recommended_strategy == "multi_venue"
    assert out.recommended_reason == "no_feasible_route_capacity_shortfall_lowest_blockers_lowest_estimated_cost"
    assert out.recommended_estimated_cost_bps == 6.5
    assert out.recommended_allocation_coverage_ratio == 0.4
    assert out.recommended_allocation_shortfall_quantity == 1.8


def test_gateway_live_execution_place_route_compare_rejects_unsupported_strategy():
    with pytest.raises(ValidationError):
        LiveExecutionPlaceRouteCompareRequest(
            intent_id="84f216c5-d7fb-4f5f-a150-8ca5f33aa918",
            strategies=["intent", "unsupported_strategy"],
        )


def test_gateway_live_execution_place_route_compare_rejects_invalid_intent_id():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            live_routes.execution_place_route_compare(
                LiveExecutionPlaceRouteCompareRequest(
                    intent_id="bad-intent-id",
                    strategies=["intent"],
                )
            )
        )
    assert exc.value.status_code == 400


def test_gateway_live_execution_place_route_compare_rejects_min_venues_gt_max_venues():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            live_routes.execution_place_route_compare(
                LiveExecutionPlaceRouteCompareRequest(
                    intent_id="84f216c5-d7fb-4f5f-a150-8ca5f33aa918",
                    strategies=["intent"],
                    max_venues=1,
                    min_venues=2,
                )
            )
        )
    assert exc.value.status_code == 400


def test_gateway_live_execution_place_route_rejects_invalid_intent_id(monkeypatch):
    class _Model:
        pass

    class _Session:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            live_routes.execution_place_route(
                LiveExecutionPlaceRouteRequest(intent_id="bad-intent-id")
            )
        )
    assert exc.value.status_code == 400


def test_gateway_live_execution_place_route_rejects_min_venues_gt_max_venues():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            live_routes.execution_place_route(
                LiveExecutionPlaceRouteRequest(
                    intent_id="84f216c5-d7fb-4f5f-a150-8ca5f33aa918",
                    max_venues=1,
                    min_venues=2,
                )
            )
        )
    assert exc.value.status_code == 400


def test_gateway_live_execution_place_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "approved_dry_run"
        gate = "ALLOW"
        reason = "approved_for_live_no_execution"
        execution_disabled = True
        approved_for_live = True
        approved_at = "2026-03-11T03:10:00Z"
        route_plan = {"selected_venue": "coinbase"}
        risk_snapshot = {"gate": "ALLOW"}
        custody_snapshot = {"custody_ready": True}
        response_payload = {}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "_persist_live_execution_submission", lambda **_kwargs: "place-sub-1")
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "execution_enabled", True)

    out = asyncio.run(
        live_routes.execution_place(
            LiveExecutionPlaceRequest(
                intent_id="2d8f5913-4dc3-4924-af80-574147f38b56",
                provider="coinbase_sandbox",
                venue="coinbase",
            )
        )
    )
    assert out.accepted is False
    assert out.execution_mode == "live_place"
    assert out.provider == "coinbase_sandbox"
    assert out.venue == "coinbase"
    assert out.requested_strategy == "intent"
    assert out.resolved_strategy == "intent"
    assert out.submission_id == "place-sub-1"
    assert "phase2_live_execution_path_disabled" in out.blockers
    assert row.status == "submit_blocked_live"


def test_gateway_live_execution_place_requested_venue_not_supported_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2fbac666-f6fe-4eb4-af78-8334f98fd36f"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-009"
        status = "approved_dry_run"
        gate = "ALLOW"
        reason = "approved_for_live_no_execution"
        execution_disabled = True
        approved_for_live = True
        approved_at = "2026-03-11T03:10:00Z"
        route_plan = {"selected_venue": "coinbase"}
        risk_snapshot = {"gate": "ALLOW"}
        custody_snapshot = {"custody_ready": True}
        response_payload = {}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "_persist_live_execution_submission", lambda **_kwargs: "place-sub-9")
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "execution_enabled", True)

    out = asyncio.run(
        live_routes.execution_place(
            LiveExecutionPlaceRequest(
                intent_id="2fbac666-f6fe-4eb4-af78-8334f98fd36f",
                provider="coinbase_sandbox",
                venue="kraken",
                strategy="intent",
            )
        )
    )
    assert out.accepted is False
    assert out.execution_mode == "live_place"
    assert out.venue == "kraken"
    assert out.selected_venue == "coinbase"
    assert out.requested_strategy == "intent"
    assert out.resolved_strategy == "intent"
    assert out.route_eligible is True
    assert out.feasible_route is False
    assert out.provider_supported_venues == ["coinbase"]
    assert out.provider_venue_compatible is False
    assert "requested_venue_not_supported_by_provider" in out.blockers
    assert "provider_venue_mismatch" in out.blockers
    assert "requested_venue_mismatch_route_selection" in out.blockers
    assert "route_not_feasible" in out.blockers
    assert out.submission_id == "place-sub-9"
    assert row.status == "submit_blocked_live"


def test_gateway_live_execution_place_auto_strategy_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "8ff6de80-c2be-4e0d-bf89-b0e06440898a"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-010"
        status = "approved_dry_run"
        gate = "ALLOW"
        reason = "approved_for_live_no_execution"
        execution_disabled = True
        approved_for_live = True
        approved_at = "2026-03-11T03:10:00Z"
        route_plan = {"selected_venue": "coinbase"}
        risk_snapshot = {"gate": "ALLOW"}
        custody_snapshot = {"custody_ready": True}
        response_payload = {}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_compare(req):
        assert req.intent_id == "8ff6de80-c2be-4e0d-bf89-b0e06440898a"
        assert req.provider == "coinbase_sandbox"
        assert req.strategies == ["intent", "single_venue", "multi_venue"]
        assert req.min_venues == 1
        assert req.max_venue_ratio == 1.0
        assert req.min_slice_quantity == 0.0
        return live_routes.LiveExecutionPlaceRouteCompareResponse(
            as_of=datetime.now(timezone.utc),
            intent_id=req.intent_id,
            symbol="SOL-USD",
            provider="coinbase_sandbox",
            options=[],
            recommended_strategy="single_venue",
            recommended_reason="feasible_route_with_lowest_blockers",
            recommended_tie_break_reason="lowest_estimated_cost_bps",
            execution_disabled=True,
        )

    async def _fake_route(req):
        assert req.intent_id == "8ff6de80-c2be-4e0d-bf89-b0e06440898a"
        assert req.provider == "coinbase_sandbox"
        assert req.strategy == "single_venue"
        assert req.min_venues == 1
        assert req.max_venue_ratio == 1.0
        assert req.min_slice_quantity == 0.0
        return live_routes.LiveExecutionPlaceRouteResponse(
            as_of=datetime.now(timezone.utc),
            intent_id=req.intent_id,
            symbol="SOL-USD",
            provider="coinbase_sandbox",
            strategy="single_venue",
            selected_venue="coinbase",
            selected_reason="lowest_estimated_cost",
            route_eligible=True,
            feasible_route=True,
            candidates=[{"venue": "coinbase", "estimated_cost_bps": 8.0}],
            recommended_slices=[{"venue": "coinbase", "quantity": 1.0, "weight": 1.0}],
            rejected_venues=[{"venue": "binance", "reason": "provider_venue_not_supported"}],
            total_estimated_cost_bps=8.0,
            provider_supported_venues=["coinbase"],
            provider_venue_compatible=True,
            deployment_armed=True,
            custody_ready=True,
            risk_gate="ALLOW",
            blockers=["phase2_live_execution_path_disabled"],
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(live_routes, "execution_place_route_compare", _fake_compare)
    monkeypatch.setattr(live_routes, "execution_place_route", _fake_route)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "_persist_live_execution_submission", lambda **_kwargs: "place-sub-10")
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "execution_enabled", True)

    out = asyncio.run(
        live_routes.execution_place(
            LiveExecutionPlaceRequest(
                intent_id="8ff6de80-c2be-4e0d-bf89-b0e06440898a",
                provider="coinbase_sandbox",
                strategy="auto",
                max_venues=2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.accepted is False
    assert out.execution_mode == "live_place"
    assert out.requested_strategy == "auto"
    assert out.resolved_strategy == "single_venue"
    assert out.strategy == "single_venue"
    assert out.strategy_resolution_reason == "feasible_route_with_lowest_blockers"
    assert out.strategy_resolution_tie_break_reason == "lowest_estimated_cost_bps"
    assert out.selected_venue == "coinbase"
    assert out.feasible_route is True
    assert out.rejected_venues[0]["reason"] == "provider_venue_not_supported"
    assert out.total_estimated_cost_bps == 8.0
    assert out.provider_venue_compatible is True
    assert out.submission_id == "place-sub-10"
    assert row.status == "submit_blocked_live"


def test_gateway_live_execution_place_rejects_min_venues_gt_max_venues():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            live_routes.execution_place(
                LiveExecutionPlaceRequest(
                    intent_id="8ff6de80-c2be-4e0d-bf89-b0e06440898a",
                    max_venues=1,
                    min_venues=2,
                )
            )
        )
    assert exc.value.status_code == 400


def test_gateway_live_execution_place_multi_venue_strategy_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "7d60b90d-380e-40e1-a19d-16f5b4f7a8be"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "sell"
        quantity = 3.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-002"
        status = "approved_dry_run"
        gate = "ALLOW"
        reason = "approved_for_live_no_execution"
        execution_disabled = True
        approved_for_live = True
        approved_at = "2026-03-11T03:10:00Z"
        route_plan = {"selected_venue": "coinbase"}
        risk_snapshot = {"gate": "ALLOW"}
        custody_snapshot = {"custody_ready": True}
        response_payload = {}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_allocation(req):
        assert req.symbol == "SOL-USD"
        assert req.side == "sell"
        return live_routes.LiveRouteAllocationResponse(
            symbol="SOL-USD",
            side="sell",
            quantity=3.0,
            order_type="market",
            feasible_route=True,
            recommended_slices=[
                {"venue": "kraken", "quantity": 1.8, "weight": 0.6},
                {"venue": "coinbase", "quantity": 1.2, "weight": 0.4},
            ],
            rejected_venues=[],
            routing_policy={"max_estimated_cost_bps": 30.0},
            total_estimated_cost_bps=11.2,
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(live_routes, "router_allocation", _fake_allocation)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "_persist_live_execution_submission", lambda **_kwargs: "place-sub-2")
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(live_routes.settings, "execution_enabled", True)

    out = asyncio.run(
        live_routes.execution_place(
            LiveExecutionPlaceRequest(
                intent_id="7d60b90d-380e-40e1-a19d-16f5b4f7a8be",
                provider="coinbase_sandbox",
                strategy="multi_venue",
                max_venues=2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.accepted is False
    assert out.execution_mode == "live_place"
    assert out.strategy == "multi_venue"
    assert out.requested_strategy == "multi_venue"
    assert out.resolved_strategy == "multi_venue"
    assert out.selected_venue == "coinbase"
    assert out.venue == "coinbase"
    assert out.route_eligible is True
    assert out.feasible_route is False
    assert len(out.recommended_slices) == 1
    assert out.recommended_slices[0]["venue"] == "coinbase"
    assert out.requested_quantity == 3.0
    assert out.allocated_quantity == 1.2
    assert out.allocation_coverage_ratio == 0.4
    assert out.allocation_shortfall_quantity == 1.8
    assert any(item.get("reason") == "quantity_shortfall" for item in out.rejected_venues)
    assert out.provider_supported_venues == ["coinbase"]
    assert out.provider_venue_compatible is True
    assert out.submission_id == "place-sub-2"
    assert "allocation_quantity_shortfall" in out.blockers
    assert "route_not_feasible" in out.blockers
    assert "phase2_live_execution_path_disabled" in out.blockers
    assert row.status == "submit_blocked_live"


def test_gateway_live_execution_place_rejects_invalid_intent_id(monkeypatch):
    class _Model:
        pass

    class _Session:
        def __enter__(self):
            return object()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    with pytest.raises(HTTPException) as exc:
        asyncio.run(live_routes.execution_place(LiveExecutionPlaceRequest(intent_id="bad-intent-id")))
    assert exc.value.status_code == 400


def test_gateway_live_deployment_checklist_contract(monkeypatch):
    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=False,
            paper_trading_enabled=True,
            custody_ready=False,
            min_requirements_met=False,
            blockers=["execution_disabled_flag"],
            paper_readiness={"phase3_live_eligible": False},
            risk_snapshot={"gate": "FULL_STOP"},
            notes=[],
        )

    async def _fake_custody():
        return live_routes.LiveCustodyStatusResponse(
            provider="coinbase",
            ready=False,
            key_present=False,
            secret_present=False,
            blockers=["missing_coinbase_api_key", "missing_coinbase_api_secret"],
        )

    async def _fake_route(req):
        _ = req
        return live_routes.LiveRoutePlanResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=1.0,
            order_type="market",
            candidates=[{"venue": "coinbase", "score": 50}],
            selected_venue=None,
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(live_routes, "custody_status", _fake_custody)
    monkeypatch.setattr(live_routes, "route_plan", _fake_route)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(live_routes.deployment_checklist("SOL-USD"))
    assert out.ready_for_real_capital is False
    assert "execution_flag" in out.blockers
    assert len(out.checks) >= 5


def test_gateway_live_deployment_state_arm_disarm_contract(monkeypatch):
    state_snapshot = dict(live_routes._DEPLOY_STATE)

    async def _fake_checklist(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveDeploymentChecklistResponse(
            as_of=datetime.now(timezone.utc),
            ready_for_real_capital=False,
            blockers=["execution_flag", "paper_readiness_window"],
            checks=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "_build_deployment_checklist", _fake_checklist)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    try:
        live_routes._reset_deploy_state()
        out_state = asyncio.run(live_routes.deployment_state())
        assert out_state.armed is False

        out_arm = asyncio.run(
            live_routes.deployment_arm(
                LiveDeploymentArmRequest(operator="ops-oncall", symbol="SOL-USD", note="dry-run arm", force=True)
            )
        )
        assert out_arm.armed is True
        assert out_arm.armed_by == "ops-oncall"
        assert out_arm.force is True
        assert "execution_flag" in out_arm.blockers_at_arm

        out_disarm = asyncio.run(
            live_routes.deployment_disarm(
                LiveDeploymentArmRequest(operator="ops-oncall", symbol="SOL-USD", note="done", force=False)
            )
        )
        assert out_disarm.armed is False
        assert out_disarm.armed_by == "ops-oncall"
        assert out_disarm.note == "done"
    finally:
        live_routes._DEPLOY_STATE.clear()
        live_routes._DEPLOY_STATE.update(state_snapshot)


def test_gateway_live_deployment_arm_rejects_without_force(monkeypatch):
    async def _fake_checklist(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveDeploymentChecklistResponse(
            as_of=datetime.now(timezone.utc),
            ready_for_real_capital=False,
            blockers=["risk_gate_allow"],
            checks=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "_build_deployment_checklist", _fake_checklist)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            live_routes.deployment_arm(
                LiveDeploymentArmRequest(operator="ops-oncall", symbol="SOL-USD", note="attempt", force=False)
            )
        )
    assert exc.value.status_code == 409
    assert isinstance(exc.value.detail, dict)
    assert exc.value.detail["reason"] == "deployment_checklist_blockers"


def test_gateway_live_symbol_mapping_helpers():
    assert live_routes._to_binance_symbol("SOL-USD") == "SOLUSDT"
    assert live_routes._to_kraken_pair("SOL-USD") == "SOLUSD"


def test_gateway_live_order_intent_contract(monkeypatch):
    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=False,
            paper_trading_enabled=True,
            custody_ready=False,
            min_requirements_met=False,
            blockers=["execution_disabled_flag"],
            paper_readiness={},
            risk_snapshot={"gate": "FULL_STOP"},
            notes=[],
        )

    async def _fake_route(req):
        _ = req
        return live_routes.LiveRoutePlanResponse(
            symbol="SOL-USD",
            side="buy",
            quantity=1.0,
            order_type="market",
            candidates=[{"venue": "coinbase"}],
            selected_venue=None,
            execution_disabled=True,
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(live_routes, "route_plan", _fake_route)
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(
        live_routes.order_intent(
            LiveOrderIntentRequest(symbol="SOL-USD", side="buy", quantity=1.0, order_type="market")
        )
    )
    assert out.accepted is False
    assert out.execution_disabled is True
    assert out.gate == "FULL_STOP"


def test_gateway_live_order_intents_list_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

        def desc(self):
            return self

    class _Model:
        symbol = _Col()
        status = _Col()
        created_at = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

        def order_by(self, *_args, **_kwargs):
            return self

        def limit(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "blocked"
        gate = "FULL_STOP"
        reason = "execution_disabled_flag"
        execution_disabled = True
        approved_for_live = False
        approved_at = None
        route_plan = {}
        risk_snapshot = {}
        custody_snapshot = {}

    class _Result:
        def scalars(self):
            return self

        def all(self):
            return [_Row()]

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "and_", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    out = asyncio.run(live_routes.list_order_intents(symbol="SOL-USD", status="blocked", limit=20))
    assert len(out.intents) == 1
    assert out.intents[0].symbol == "SOL-USD"
    assert out.intents[0].status == "blocked"


def test_gateway_live_order_intent_approve_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "blocked"
        gate = "FULL_STOP"
        reason = "execution_disabled_flag"
        execution_disabled = True
        approved_for_live = False
        approved_at = None
        route_plan = {}
        risk_snapshot = {}
        custody_snapshot = {}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(live_routes.approve_order_intent("2d8f5913-4dc3-4924-af80-574147f38b56"))
    assert out.approved_for_live is True
    assert out.execution_disabled is True
    assert out.status == "approved_dry_run"


def test_gateway_live_execution_submit_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "approved_dry_run"
        gate = "ALLOW"
        reason = "approved_for_live_no_execution"
        execution_disabled = True
        approved_for_live = True
        approved_at = "2026-03-11T03:10:00Z"
        route_plan = {}
        risk_snapshot = {"gate": "ALLOW"}
        custody_snapshot = {"custody_ready": True}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=False,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=False,
            blockers=["execution_disabled_flag"],
            paper_readiness={"phase3_live_eligible": False},
            risk_snapshot={"gate": "FULL_STOP"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_submit(
            LiveExecutionSubmitRequest(intent_id="2d8f5913-4dc3-4924-af80-574147f38b56")
        )
    )
    assert out.accepted is False
    assert out.execution_disabled is True
    assert "execution_disabled_flag" in out.reason
    assert out.provider is None
    assert out.intent["status"] == "submit_blocked_dry_run"


def test_gateway_live_execution_submit_live_place_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        symbol = "SOL-USD"
        status = "approved_dry_run"
        approved_for_live = True
        execution_disabled = True
        reason = "approved_for_live_no_execution"
        route_plan = {"selected_venue": "coinbase"}
        response_payload = {}

    class _Result:
        def scalar_one_or_none(self):
            return _Row()

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_place(req):
        assert req.intent_id == "2d8f5913-4dc3-4924-af80-574147f38b56"
        assert req.provider == "coinbase_sandbox"
        assert req.venue == "coinbase"
        assert req.strategy == "multi_venue"
        assert req.max_venues == 2
        assert req.min_venues == 1
        assert req.max_venue_ratio == 1.0
        assert req.min_slice_quantity == 0.0
        assert req.max_slippage_bps == 25.0
        return live_routes.LiveExecutionPlaceResponse(
            accepted=False,
            execution_disabled=True,
            reason="phase2_live_execution_path_disabled",
            execution_mode="live_place",
            submission_id="place-sub-1",
            provider="coinbase_sandbox",
            venue="coinbase",
            strategy="multi_venue",
            selected_venue="coinbase",
            route_eligible=True,
            feasible_route=True,
            recommended_slices=[{"venue": "coinbase", "quantity": 1.0, "weight": 1.0}],
            blockers=["phase2_live_execution_path_disabled"],
            intent={"id": req.intent_id, "status": "submit_blocked_live"},
        )

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "execution_place", _fake_place)

    out = asyncio.run(
        live_routes.execution_submit(
            LiveExecutionSubmitRequest(
                intent_id="2d8f5913-4dc3-4924-af80-574147f38b56",
                mode="live_place",
                provider="coinbase_sandbox",
                venue="coinbase",
                strategy="multi_venue",
                max_venues=2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.execution_mode == "live_place"
    assert out.accepted is False
    assert out.execution_disabled is True
    assert out.provider == "coinbase_sandbox"
    assert out.venue == "coinbase"
    assert out.submission_id == "place-sub-1"
    assert out.intent["status"] == "submit_blocked_live"


def test_gateway_live_execution_submit_live_place_auto_strategy_contract(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "29f97bd4-f9dd-4de3-972e-c5749f6481f7"
        symbol = "SOL-USD"
        status = "approved_dry_run"
        approved_for_live = True
        execution_disabled = True
        reason = "approved_for_live_no_execution"
        route_plan = {"selected_venue": "coinbase"}
        response_payload = {}

    class _Result:
        def scalar_one_or_none(self):
            return _Row()

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_place(req):
        assert req.intent_id == "29f97bd4-f9dd-4de3-972e-c5749f6481f7"
        assert req.provider == "coinbase_sandbox"
        assert req.venue is None
        assert req.strategy == "auto"
        assert req.max_venues == 2
        assert req.min_venues == 1
        assert req.max_venue_ratio == 1.0
        assert req.min_slice_quantity == 0.0
        assert req.max_slippage_bps == 25.0
        return live_routes.LiveExecutionPlaceResponse(
            accepted=False,
            execution_disabled=True,
            reason="phase2_live_execution_path_disabled",
            execution_mode="live_place",
            submission_id="place-sub-auto-1",
            provider="coinbase_sandbox",
            venue="coinbase",
            strategy="single_venue",
            requested_strategy="auto",
            resolved_strategy="single_venue",
            strategy_resolution_reason="feasible_route_with_lowest_blockers",
            selected_venue="coinbase",
            route_eligible=True,
            feasible_route=True,
            provider_supported_venues=["coinbase"],
            provider_venue_compatible=True,
            recommended_slices=[{"venue": "coinbase", "quantity": 1.0, "weight": 1.0}],
            blockers=["phase2_live_execution_path_disabled"],
            intent={"id": req.intent_id, "status": "submit_blocked_live"},
        )

    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "execution_place", _fake_place)

    out = asyncio.run(
        live_routes.execution_submit(
            LiveExecutionSubmitRequest(
                intent_id="29f97bd4-f9dd-4de3-972e-c5749f6481f7",
                mode="live_place",
                provider="coinbase_sandbox",
                strategy="auto",
                max_venues=2,
                max_slippage_bps=25.0,
            )
        )
    )
    assert out.execution_mode == "live_place"
    assert out.accepted is False
    assert out.execution_disabled is True
    assert out.provider == "coinbase_sandbox"
    assert out.venue == "coinbase"
    assert out.submission_id == "place-sub-auto-1"
    assert out.intent["status"] == "submit_blocked_live"


def test_gateway_live_execution_submit_sandbox_blocked_when_disabled(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "approved_dry_run"
        gate = "ALLOW"
        reason = "approved_for_live_no_execution"
        execution_disabled = True
        approved_for_live = True
        approved_at = "2026-03-11T03:10:00Z"
        route_plan = {"selected_venue": "coinbase"}
        risk_snapshot = {"gate": "ALLOW"}
        custody_snapshot = {"custody_ready": True}
        response_payload = {}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=False,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=False,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes.settings, "live_execution_sandbox_enabled", False)
    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_submit(
            LiveExecutionSubmitRequest(
                intent_id="2d8f5913-4dc3-4924-af80-574147f38b56",
                mode="sandbox_submit",
            )
        )
    )
    assert out.accepted is False
    assert out.execution_mode == "sandbox_submit"
    assert out.provider == "mock"
    assert out.sandbox is True
    assert "sandbox_execution_disabled_flag" in out.reason
    assert out.intent["status"] == "submit_blocked_sandbox"


def test_gateway_live_execution_submit_sandbox_blocked_for_unsupported_provider(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "approved_dry_run"
        gate = "ALLOW"
        reason = "approved_for_live_no_execution"
        execution_disabled = True
        approved_for_live = True
        approved_at = "2026-03-11T03:10:00Z"
        route_plan = {"selected_venue": "coinbase"}
        risk_snapshot = {"gate": "ALLOW"}
        custody_snapshot = {"custody_ready": True}
        response_payload = {}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes.settings, "live_execution_sandbox_enabled", True)
    monkeypatch.setattr(live_routes.settings, "live_execution_provider", "unknown_provider")
    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_submit(
            LiveExecutionSubmitRequest(
                intent_id="2d8f5913-4dc3-4924-af80-574147f38b56",
                mode="sandbox_submit",
            )
        )
    )
    assert out.accepted is False
    assert out.execution_mode == "sandbox_submit"
    assert out.provider == "unknown_provider"
    assert "sandbox_provider_not_supported" in out.reason
    assert out.intent["status"] == "submit_blocked_sandbox"


def test_gateway_live_execution_submit_sandbox_coinbase_requires_credentials(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "approved_dry_run"
        gate = "ALLOW"
        reason = "approved_for_live_no_execution"
        execution_disabled = True
        approved_for_live = True
        approved_at = "2026-03-11T03:10:00Z"
        route_plan = {"selected_venue": "coinbase"}
        risk_snapshot = {"gate": "ALLOW"}
        custody_snapshot = {"custody_ready": False}
        response_payload = {}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=False,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes.settings, "live_execution_sandbox_enabled", True)
    monkeypatch.setattr(live_routes.settings, "live_execution_provider", "coinbase_sandbox")
    monkeypatch.setattr(live_routes.settings, "coinbase_use_sandbox", True)
    monkeypatch.setattr(live_routes.settings, "coinbase_api_key", "")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_secret", "")
    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_submit(
            LiveExecutionSubmitRequest(
                intent_id="2d8f5913-4dc3-4924-af80-574147f38b56",
                mode="sandbox_submit",
            )
        )
    )
    assert out.accepted is False
    assert out.provider == "coinbase_sandbox"
    assert "missing_coinbase_api_credentials" in out.reason
    assert out.intent["status"] == "submit_blocked_sandbox"


def test_gateway_live_execution_submit_sandbox_coinbase_transport_requires_passphrase(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "approved_dry_run"
        gate = "ALLOW"
        reason = "approved_for_live_no_execution"
        execution_disabled = True
        approved_for_live = True
        approved_at = "2026-03-11T03:10:00Z"
        route_plan = {"selected_venue": "coinbase"}
        risk_snapshot = {"gate": "ALLOW"}
        custody_snapshot = {"custody_ready": True}
        response_payload = {}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes.settings, "live_execution_sandbox_enabled", True)
    monkeypatch.setattr(live_routes.settings, "live_execution_provider", "coinbase_sandbox")
    monkeypatch.setattr(live_routes.settings, "live_execution_sandbox_transport_enabled", True)
    monkeypatch.setattr(live_routes.settings, "coinbase_use_sandbox", True)
    monkeypatch.setattr(live_routes.settings, "coinbase_api_key", "abc123")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_secret", "xyz789")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_passphrase", "")
    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_submit(
            LiveExecutionSubmitRequest(
                intent_id="2d8f5913-4dc3-4924-af80-574147f38b56",
                mode="sandbox_submit",
            )
        )
    )
    assert out.accepted is False
    assert out.provider == "coinbase_sandbox"
    assert "missing_coinbase_api_passphrase" in out.reason
    assert out.intent["status"] == "submit_blocked_sandbox"


def test_gateway_live_execution_submit_sandbox_coinbase_accepts_with_credentials(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "approved_dry_run"
        gate = "ALLOW"
        reason = "approved_for_live_no_execution"
        execution_disabled = True
        approved_for_live = True
        approved_at = "2026-03-11T03:10:00Z"
        route_plan = {"selected_venue": "coinbase"}
        risk_snapshot = {"gate": "ALLOW"}
        custody_snapshot = {"custody_ready": True}
        response_payload = {}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes.settings, "live_execution_sandbox_enabled", True)
    monkeypatch.setattr(live_routes.settings, "live_execution_provider", "coinbase_sandbox")
    monkeypatch.setattr(live_routes.settings, "coinbase_use_sandbox", True)
    monkeypatch.setattr(live_routes.settings, "coinbase_api_key", "abc123")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_secret", "xyz789")
    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_submit(
            LiveExecutionSubmitRequest(
                intent_id="2d8f5913-4dc3-4924-af80-574147f38b56",
                mode="sandbox_submit",
            )
        )
    )
    assert out.accepted is True
    assert out.execution_mode == "sandbox_submit"
    assert out.provider == "coinbase_sandbox"
    assert out.venue == "coinbase"
    assert isinstance(out.venue_order_id, str)
    assert out.venue_order_id.startswith("csbox-")
    assert out.intent["status"] == "submitted_sandbox"


def test_gateway_live_execution_submit_sandbox_coinbase_transport_accepts(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "approved_dry_run"
        gate = "ALLOW"
        reason = "approved_for_live_no_execution"
        execution_disabled = True
        approved_for_live = True
        approved_at = "2026-03-11T03:10:00Z"
        route_plan = {"selected_venue": "coinbase"}
        risk_snapshot = {"gate": "ALLOW"}
        custody_snapshot = {"custody_ready": True}
        response_payload = {}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    def _fake_transport_submit(*, row, payload):
        assert payload["product_id"] == "SOL-USD"
        _ = row
        return {
            "provider": "coinbase_sandbox",
            "venue": "coinbase",
            "venue_order_id": "cb-order-123",
            "submitted_at": "2026-03-11T09:00:00Z",
            "sandbox": True,
            "simulated_submission": False,
            "transport": "http",
            "api_base": "https://api-public.sandbox.exchange.coinbase.com",
            "request": {"symbol": "SOL-USD"},
            "exchange_response": {"id": "cb-order-123", "status": "pending"},
        }

    monkeypatch.setattr(live_routes.settings, "live_execution_sandbox_enabled", True)
    monkeypatch.setattr(live_routes.settings, "live_execution_provider", "coinbase_sandbox")
    monkeypatch.setattr(live_routes.settings, "live_execution_sandbox_transport_enabled", True)
    monkeypatch.setattr(live_routes.settings, "coinbase_use_sandbox", True)
    monkeypatch.setattr(live_routes.settings, "coinbase_api_key", "abc123")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_secret", "eHl6Nzg5")
    monkeypatch.setattr(live_routes.settings, "coinbase_api_passphrase", "pass123")
    monkeypatch.setattr(live_routes, "_coinbase_sandbox_transport_submit", _fake_transport_submit)
    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_submit(
            LiveExecutionSubmitRequest(
                intent_id="2d8f5913-4dc3-4924-af80-574147f38b56",
                mode="sandbox_submit",
            )
        )
    )
    assert out.accepted is True
    assert out.provider == "coinbase_sandbox"
    assert out.venue_order_id == "cb-order-123"
    assert out.intent["status"] == "submitted_sandbox"


def test_gateway_live_execution_submit_sandbox_accepts_when_enabled(monkeypatch):
    class _Col:
        def __eq__(self, other):
            _ = other
            return self

    class _Model:
        id = _Col()

    class _Stmt:
        def where(self, *_args, **_kwargs):
            return self

    class _Row:
        id = "2d8f5913-4dc3-4924-af80-574147f38b56"
        created_at = "2026-03-11T03:00:00Z"
        updated_at = "2026-03-11T03:00:00Z"
        symbol = "SOL-USD"
        side = "buy"
        quantity = 1.0
        order_type = "market"
        limit_price = None
        venue_preference = None
        client_order_id = "live-dryrun-001"
        status = "approved_dry_run"
        gate = "ALLOW"
        reason = "approved_for_live_no_execution"
        execution_disabled = True
        approved_for_live = True
        approved_at = "2026-03-11T03:10:00Z"
        route_plan = {"selected_venue": "coinbase"}
        risk_snapshot = {"gate": "ALLOW"}
        custody_snapshot = {"custody_ready": True}
        response_payload = {}

    row = _Row()

    class _Result:
        def scalar_one_or_none(self):
            return row

    class _DB:
        def execute(self, stmt):
            _ = stmt
            return _Result()

        def add(self, item):
            _ = item

        def commit(self):
            return None

        def refresh(self, item):
            _ = item
            return None

    class _Session:
        def __enter__(self):
            return _DB()

        def __exit__(self, exc_type, exc, tb):
            return False

    async def _fake_status(symbol):
        assert symbol == "SOL-USD"
        return live_routes.LiveStatusResponse(
            execution_enabled=True,
            paper_trading_enabled=True,
            custody_ready=True,
            min_requirements_met=True,
            blockers=[],
            paper_readiness={"phase3_live_eligible": True},
            risk_snapshot={"gate": "ALLOW"},
            notes=[],
        )

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(live_routes.settings, "live_execution_sandbox_enabled", True)
    monkeypatch.setattr(live_routes.settings, "live_execution_provider", "mock")
    monkeypatch.setattr(live_routes, "LiveOrderIntent", _Model)
    monkeypatch.setattr(live_routes, "select", lambda *_args, **_kwargs: _Stmt())
    monkeypatch.setattr(live_routes, "SessionLocal", lambda: _Session())
    monkeypatch.setattr(live_routes, "_compute_live_status", _fake_status)
    monkeypatch.setattr(
        live_routes,
        "_deployment_state_out",
        lambda: live_routes.LiveDeploymentStateResponse(
            as_of=datetime.now(timezone.utc),
            armed=True,
            armed_at=datetime.now(timezone.utc),
            armed_by="ops-oncall",
            note="armed",
            force=True,
            blockers_at_arm=[],
        ),
    )
    monkeypatch.setattr(live_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        live_routes.execution_submit(
            LiveExecutionSubmitRequest(
                intent_id="2d8f5913-4dc3-4924-af80-574147f38b56",
                mode="sandbox_submit",
            )
        )
    )
    assert out.accepted is True
    assert out.execution_disabled is False
    assert out.execution_mode == "sandbox_submit"
    assert out.provider == "mock"
    assert out.sandbox is True
    assert out.venue == "coinbase"
    assert out.venue_order_id is not None
    assert out.intent["status"] == "submitted_sandbox"


def test_gateway_query_why_moving_builds_question(monkeypatch):
    observed = {}

    async def _fake_orchestrator(payload):
        observed["payload"] = payload
        return {
            "asset": payload["asset"],
            "question": payload["question"],
            "current_cause": "Current cause text.",
            "past_precedent": "Past precedent text.",
            "future_catalyst": "Future catalyst text.",
            "confidence": 0.61,
            "evidence": [],
            "execution_disabled": True,
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(query_routes, "_call_orchestrator", _fake_orchestrator)
    monkeypatch.setattr(query_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(query_routes.why_moving({"asset": "ETH"}))
    assert out.asset == "ETH"
    assert out.question == "Why is ETH moving?"
    assert observed["payload"]["question"] == "Why is ETH moving?"


def test_gateway_query_propose_trade_contract(monkeypatch):
    async def _fake_orchestrator(payload):
        assert payload["asset"] == "SOL"
        return {
            "asset": "SOL",
            "question": "Should we open a SOL paper position now?",
            "side": "buy",
            "order_type": "market",
            "suggested_quantity": 1.2,
            "estimated_price": 145.0,
            "estimated_notional_usd": 174.0,
            "rationale": "Momentum setup with supporting context.",
            "confidence": 0.8,
            "risk": {"gate": "ALLOW", "paper_approved": True},
            "execution_disabled": True,
            "requires_user_approval": True,
            "paper_submit_path": "/paper/orders",
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(query_routes, "_call_orchestrator_propose", _fake_orchestrator)
    monkeypatch.setattr(query_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(
        query_routes.propose_trade(
            TradeProposalRequest(asset="SOL", question="Should we open a SOL paper position now?")
        )
    )
    assert out.asset == "SOL"
    assert out.side == "buy"
    assert out.execution_disabled is True


def test_gateway_documents_search_contract(monkeypatch):
    async def _fake_memory(payload):
        assert payload["asset"] == "SOL"
        return {
            "results": [
                {
                    "id": "doc-1",
                    "source": "newsapi",
                    "title": "SOL validator growth update",
                    "url": "https://example.org/sol-update",
                    "timeline": "present",
                    "confidence": 0.84,
                    "published_at": "2026-03-10T20:45:00Z",
                    "snippet": "Validator count climbed while liquidity improved.",
                }
            ]
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(query_routes, "_call_memory", _fake_memory)
    monkeypatch.setattr(query_routes, "emit_audit_event", _fake_audit)

    req = DocumentSearchRequest(
        query="SOL roadmap unlock validator growth",
        asset="SOL",
        timeline=["past", "present", "future"],
        limit=10,
    )
    out = asyncio.run(query_routes.documents_search(req))
    assert len(out.results) == 1
    assert out.results[0].timeline == "present"


def test_gateway_market_snapshot_proxy_contract(monkeypatch):
    async def _fake_market(symbol):
        assert symbol == "BTC-USD"
        return {
            "symbol": "BTC-USD",
            "exchange": "coinbase",
            "last_price": "84250.12",
            "bid": "84249.90",
            "ask": "84250.20",
            "spread": "0.30",
            "timestamp": "2026-03-10T21:45:00Z",
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(query_routes, "_call_market_snapshot", _fake_market)
    monkeypatch.setattr(query_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(query_routes.market_snapshot("BTC-USD"))
    assert out["symbol"] == "BTC-USD"
    assert out["exchange"] == "coinbase"


def test_gateway_query_explain_returns_503_when_orchestrator_unavailable(monkeypatch):
    async def _fake_orchestrator(payload):
        _ = payload
        raise RuntimeError("orchestrator_down")

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(query_routes, "_call_orchestrator", _fake_orchestrator)
    monkeypatch.setattr(query_routes, "emit_audit_event", _fake_audit)

    with pytest.raises(HTTPException) as err:
        asyncio.run(query_routes.explain(ExplainRequest(asset="SOL", question="Why is SOL moving?")))
    assert err.value.status_code == 503
    assert err.value.detail == "orchestrator unavailable"


def test_gateway_documents_search_returns_503_when_memory_unavailable(monkeypatch):
    async def _fake_memory(payload):
        _ = payload
        raise RuntimeError("memory_down")

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(query_routes, "_call_memory", _fake_memory)
    monkeypatch.setattr(query_routes, "emit_audit_event", _fake_audit)

    req = DocumentSearchRequest(
        query="SOL roadmap unlock validator growth",
        asset="SOL",
        timeline=["past", "present", "future"],
        limit=10,
    )
    with pytest.raises(HTTPException) as err:
        asyncio.run(query_routes.documents_search(req))
    assert err.value.status_code == 503
    assert err.value.detail == "memory unavailable"


def test_gateway_market_snapshot_returns_503_when_market_unavailable(monkeypatch):
    async def _fake_market(symbol):
        _ = symbol
        raise RuntimeError("market_down")

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(query_routes, "_call_market_snapshot", _fake_market)
    monkeypatch.setattr(query_routes, "emit_audit_event", _fake_audit)

    with pytest.raises(HTTPException) as err:
        asyncio.run(query_routes.market_snapshot("SOL-USD"))
    assert err.value.status_code == 503
    assert err.value.detail == "market_data unavailable"


def test_gateway_paper_submit_order_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, retries=2):
        _ = (retries, json_payload)
        assert method == "POST"
        assert path == "/paper/orders"
        return {
            "id": "d5955f0d-2455-404a-8cf5-e1468e407963",
            "client_order_id": "paper-abc123",
            "symbol": "SOL-USD",
            "side": "buy",
            "order_type": "market",
            "status": "filled",
            "quantity": 1.25,
            "limit_price": None,
            "filled_quantity": 1.25,
            "average_fill_price": 145.2,
            "risk_gate": "ALLOW",
            "execution_disabled": True,
            "paper_mode": True,
            "created_at": "2026-03-10T21:00:00Z",
            "updated_at": "2026-03-10T21:00:00Z",
            "canceled_at": None,
            "metadata": {},
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    monkeypatch.setattr(paper_routes, "emit_audit_event", _fake_audit)
    monkeypatch.setattr(paper_routes.settings, "paper_order_require_approval", False)

    out = asyncio.run(
        paper_routes.submit_order(
            PaperOrderCreateRequest(symbol="SOL-USD", side="buy", order_type="market", quantity=1.25)
        )
    )
    assert out.symbol == "SOL-USD"
    assert out.execution_disabled is True
    assert out.paper_mode is True
    assert out.status == "filled"


def test_gateway_paper_submit_order_requires_approval_when_enabled(monkeypatch):
    monkeypatch.setattr(paper_routes.settings, "paper_order_require_approval", True)
    with pytest.raises(HTTPException) as err:
        asyncio.run(
            paper_routes.submit_order(
                PaperOrderCreateRequest(symbol="SOL-USD", side="buy", order_type="market", quantity=1.25)
            )
        )
    assert err.value.status_code == 403
    assert err.value.detail == "paper order requires user approval"


def test_gateway_paper_list_orders_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, params=None, retries=2):
        _ = (json_payload, retries)
        assert method == "GET"
        assert path == "/paper/orders"
        assert params == {"limit": 20, "sort": "desc", "symbol": "SOL-USD", "status": "filled"}
        return {
            "orders": [
                {
                    "id": "d5955f0d-2455-404a-8cf5-e1468e407963",
                    "client_order_id": "paper-abc123",
                    "symbol": "SOL-USD",
                    "side": "buy",
                    "order_type": "market",
                    "status": "filled",
                    "quantity": 1.25,
                    "limit_price": None,
                    "filled_quantity": 1.25,
                    "average_fill_price": 145.2,
                    "risk_gate": "ALLOW",
                    "execution_disabled": True,
                    "paper_mode": True,
                    "created_at": "2026-03-10T21:00:00Z",
                    "updated_at": "2026-03-10T21:00:00Z",
                    "canceled_at": None,
                    "metadata": {},
                }
            ],
            "next_cursor": None,
            "has_more": False,
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    monkeypatch.setattr(paper_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(paper_routes.list_orders(symbol="SOL-USD", status="filled", limit=20, since=None))
    assert len(out.orders) == 1
    assert out.orders[0].status == "filled"
    assert out.has_more is False


def test_gateway_paper_equity_snapshot_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, params=None, retries=2):
        _ = (params, retries)
        assert method == "POST"
        assert path == "/paper/equity/snapshot"
        assert json_payload == {"note": "manual"}
        return {
            "ts": "2026-03-10T21:00:00Z",
            "equity": 100120.55,
            "cash": 99800.25,
            "unrealized_pnl": 320.30,
            "realized_pnl": 45.10,
            "note": "manual",
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    monkeypatch.setattr(paper_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(paper_routes.snapshot_equity({"note": "manual"}))
    assert out.equity == 100120.55
    assert out.note == "manual"


def test_gateway_paper_equity_series_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, params=None, retries=2):
        _ = (json_payload, retries)
        assert method == "GET"
        assert path == "/paper/equity"
        assert params == {"limit": 50, "sort": "asc", "since": "2026-03-10T00:00:00Z"}
        return {
            "points": [
                {
                    "ts": "2026-03-10T21:00:00Z",
                    "equity": 100120.55,
                    "cash": 99800.25,
                    "unrealized_pnl": 320.30,
                    "realized_pnl": 45.10,
                    "note": "manual",
                }
            ]
        }

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    out = asyncio.run(paper_routes.equity(since="2026-03-10T00:00:00Z", limit=50, sort="asc"))
    assert len(out.points) == 1
    assert out.points[0].equity == 100120.55


def test_gateway_paper_fills_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, params=None, retries=2):
        _ = (json_payload, retries)
        assert method == "GET"
        assert path == "/paper/fills"
        assert params == {
            "limit": 25,
            "sort": "desc",
            "symbol": "SOL-USD",
            "order_id": "d5955f0d-2455-404a-8cf5-e1468e407963",
        }
        return {
            "fills": [
                {
                    "id": "930f6d38-07ca-4ced-8447-d6b0293adb2f",
                    "order_id": "d5955f0d-2455-404a-8cf5-e1468e407963",
                    "symbol": "SOL-USD",
                    "side": "buy",
                    "price": 145.2,
                    "quantity": 1.25,
                    "fee": 0.12,
                    "liquidity": "taker",
                    "created_at": "2026-03-10T21:00:01Z",
                }
            ],
            "next_cursor": None,
            "has_more": False,
        }

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    out = asyncio.run(
        paper_routes.fills(
            symbol="SOL-USD",
            order_id="d5955f0d-2455-404a-8cf5-e1468e407963",
            since=None,
            cursor=None,
            limit=25,
            sort="desc",
        )
    )
    assert len(out.fills) == 1
    assert out.fills[0].fee == 0.12


def test_gateway_paper_summary_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, params=None, retries=2):
        _ = (json_payload, params, retries)
        assert method == "GET"
        assert path == "/paper/summary"
        return {
            "as_of": "2026-03-10T21:10:00Z",
            "cash": 99800.25,
            "realized_pnl": 45.10,
            "unrealized_pnl": 320.30,
            "equity": 100120.55,
            "gross_exposure_usd": 181.50,
            "positions": [
                {
                    "symbol": "SOL-USD",
                    "quantity": 1.25,
                    "avg_entry_price": 145.2,
                    "mark_price": 145.2,
                    "notional_usd": 181.5,
                    "unrealized_pnl": 0.0,
                }
            ],
        }

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    out = asyncio.run(paper_routes.summary())
    assert out.equity == 100120.55
    assert len(out.positions) == 1


def test_gateway_paper_performance_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, params=None, retries=2):
        _ = (json_payload, retries)
        assert method == "GET"
        assert path == "/paper/performance"
        assert params == {"limit": 1000, "since": "2026-03-10T00:00:00Z"}
        return {
            "as_of": "2026-03-10T21:15:00Z",
            "points": 12,
            "period_start": "2026-03-10T00:00:00Z",
            "start_equity": 100000.0,
            "end_equity": 100120.55,
            "return_pct": 0.12055,
            "high_watermark": 100200.0,
            "low_equity": 99950.0,
            "max_drawdown_usd": 250.0,
            "max_drawdown_pct": 0.2495,
            "benchmark_name": "BTC_ETH_50_50",
            "benchmark_return_pct": 0.09,
            "excess_return_pct": 0.03,
        }

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    out = asyncio.run(paper_routes.performance(since="2026-03-10T00:00:00Z", limit=1000))
    assert out.points == 12
    assert out.max_drawdown_usd == 250.0
    assert out.benchmark_name == "BTC_ETH_50_50"
    assert out.excess_return_pct == 0.03


def test_gateway_paper_readiness_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, params=None, retries=2):
        _ = (json_payload, params, retries)
        assert method == "GET"
        assert path == "/paper/readiness"
        return {
            "as_of": "2026-03-11T02:15:00Z",
            "phase3_live_eligible": False,
            "reason": "insufficient_paper_days",
            "min_days_required": 7,
            "min_points_required": 24,
            "observed_days": 2.1,
            "observed_points": 31,
            "return_pct": 1.2,
            "max_drawdown_pct": 3.1,
            "sharpe_proxy": 0.55,
        }

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    out = asyncio.run(paper_routes.readiness())
    assert out.phase3_live_eligible is False
    assert out.reason == "insufficient_paper_days"


def test_gateway_paper_retention_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, params=None, retries=2):
        _ = (params, retries)
        assert method == "POST"
        assert path == "/paper/maintenance/retention"
        assert json_payload == {"days": 30}
        return {
            "as_of": "2026-03-11T02:20:00Z",
            "retention_days": 30,
            "deleted_fills": 100,
            "deleted_orders": 100,
            "deleted_equity_points": 240,
            "deleted_rollups": 14,
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    monkeypatch.setattr(paper_routes, "emit_audit_event", _fake_audit)
    out = asyncio.run(paper_routes.retention({"days": 30}))
    assert out.retention_days == 30
    assert out.deleted_fills == 100


def test_gateway_paper_replay_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, params=None, retries=2):
        _ = (params, retries)
        assert method == "POST"
        assert path == "/paper/replay/run"
        assert json_payload["symbol"] == "SOL-USD"
        return {
            "symbol": "SOL-USD",
            "strategy": "momentum_v1",
            "start": "2026-03-01T00:00:00Z",
            "end": "2026-03-10T00:00:00Z",
            "points": 1200,
            "trades": 45,
            "gross_return_pct": 6.4,
            "max_drawdown_pct": 2.2,
            "status": "ok",
        }

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    out = asyncio.run(
        paper_routes.replay(PaperReplayRequest(symbol="SOL-USD", hold_steps=1, entry_bps=10.0))
    )
    assert out.strategy == "momentum_v1"
    assert out.trades == 45


def test_gateway_paper_shadow_compare_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, params=None, retries=2):
        _ = (params, retries)
        assert method == "POST"
        assert path == "/paper/shadow/compare"
        assert json_payload["symbol"] == "SOL-USD"
        return {
            "symbol": "SOL-USD",
            "start": "2026-03-01T00:00:00Z",
            "end": "2026-03-10T00:00:00Z",
            "points": 1200,
            "champion_return_pct": 4.2,
            "challenger_return_pct": 5.1,
            "delta_return_pct": 0.9,
            "champion_trades": 41,
            "challenger_trades": 50,
            "winner": "challenger",
            "status": "ok",
        }

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    out = asyncio.run(
        paper_routes.shadow_compare(
            PaperShadowCompareRequest(symbol="SOL-USD", champion_entry_bps=10.0, challenger_entry_bps=5.0)
        )
    )
    assert out.winner == "challenger"
    assert out.delta_return_pct == 0.9


def test_gateway_paper_rollups_list_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, params=None, retries=2):
        _ = (json_payload, retries)
        assert method == "GET"
        assert path == "/paper/performance/rollups"
        assert params == {"interval": "hourly", "limit": 48, "sort": "asc", "since": "2026-03-10T00:00:00Z"}
        return {
            "rollups": [
                {
                    "interval": "hourly",
                    "bucket_start": "2026-03-10T21:00:00Z",
                    "bucket_end": "2026-03-10T21:44:00Z",
                    "points": 5,
                    "start_equity": 100000.0,
                    "end_equity": 100120.0,
                    "return_pct": 0.12,
                    "high_watermark": 100130.0,
                    "low_equity": 99995.0,
                    "max_drawdown_usd": 35.0,
                    "max_drawdown_pct": 0.0349,
                    "benchmark_name": "BTC_ETH_50_50",
                    "benchmark_return_pct": 0.08,
                    "excess_return_pct": 0.04,
                }
            ]
        }

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    out = asyncio.run(
        paper_routes.list_performance_rollups(
            interval="hourly",
            since="2026-03-10T00:00:00Z",
            limit=48,
            sort="asc",
        )
    )
    assert len(out.rollups) == 1
    assert out.rollups[0].interval == "hourly"
    assert out.rollups[0].benchmark_name == "BTC_ETH_50_50"


def test_gateway_paper_rollups_refresh_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, params=None, retries=2):
        _ = (params, retries)
        assert method == "POST"
        assert path == "/paper/performance/rollups/refresh"
        assert json_payload == {"interval": "daily", "since": "2026-03-01T00:00:00Z"}
        return {"interval": "daily", "refreshed": 8}

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    out = asyncio.run(
        paper_routes.refresh_performance_rollups(
            {"interval": "daily", "since": "2026-03-01T00:00:00Z"}
        )
    )
    assert out.interval == "daily"
    assert out.refreshed == 8


def test_gateway_paper_submit_order_returns_503_when_service_unavailable(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, retries=2):
        _ = (method, path, json_payload, retries)
        raise RuntimeError("execution_sim_down")

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    monkeypatch.setattr(paper_routes, "_extract_detail", lambda exc: (503, "execution_sim unavailable"))
    monkeypatch.setattr(paper_routes, "emit_audit_event", _fake_audit)

    with pytest.raises(HTTPException) as err:
        asyncio.run(
            paper_routes.submit_order(
                PaperOrderCreateRequest(symbol="SOL-USD", side="buy", order_type="market", quantity=1.25)
            )
        )
    assert err.value.status_code == 503
    assert err.value.detail == "execution_sim unavailable"


def test_gateway_paper_cancel_contract(monkeypatch):
    async def _fake_exec(*, method, path, json_payload=None, retries=2):
        _ = (json_payload, retries)
        assert method == "POST"
        assert path == "/paper/orders/d5955f0d-2455-404a-8cf5-e1468e407963/cancel"
        return {
            "canceled": True,
            "order": {
                "id": "d5955f0d-2455-404a-8cf5-e1468e407963",
                "client_order_id": "paper-abc123",
                "symbol": "SOL-USD",
                "side": "buy",
                "order_type": "limit",
                "status": "canceled",
                "quantity": 1.25,
                "limit_price": 140.0,
                "filled_quantity": 0.0,
                "average_fill_price": None,
                "risk_gate": "ALLOW",
                "execution_disabled": True,
                "paper_mode": True,
                "created_at": "2026-03-10T21:00:00Z",
                "updated_at": "2026-03-10T21:05:00Z",
                "canceled_at": "2026-03-10T21:05:00Z",
                "metadata": {},
            },
        }

    async def _fake_audit(*args, **kwargs):
        _ = (args, kwargs)
        return None

    monkeypatch.setattr(paper_routes, "_call_execution_sim", _fake_exec)
    monkeypatch.setattr(paper_routes, "emit_audit_event", _fake_audit)

    out = asyncio.run(paper_routes.cancel_order("d5955f0d-2455-404a-8cf5-e1468e407963"))
    assert out.canceled is True
    assert out.order.status == "canceled"
