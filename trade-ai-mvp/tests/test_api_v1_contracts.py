from __future__ import annotations

import asyncio

import services.gateway.routes.api_v1 as api_v1_routes
from domain.policy.reason_codes import KILL_SWITCH_ACTIVE, MODE_BLOCKED, ROLE_NOT_ALLOWED, UNKNOWN_COMMAND
from shared.schemas.api import (
    ApiStatus,
    ApprovalStatus,
    ConnectionStatus,
    Mode,
    RecommendationSide,
    RiskStatus,
    Timeline,
)
from shared.schemas.documents import DocumentOut, DocumentSearchResponse
from shared.schemas.explain import ExplainResponse
from shared.schemas.trade import TradeProposalResponse


class _DummyRequest:
    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers or {}


def test_api_v1_enums_values():
    assert [m.value for m in Mode] == ["research_only", "paper", "live_approval", "live_auto"]
    assert [s.value for s in RiskStatus] == ["safe", "warning", "restricted", "paused", "blocked"]
    assert [s.value for s in ConnectionStatus] == ["connected", "degraded", "failed", "disabled"]
    assert [t.value for t in Timeline] == ["past", "present", "future"]
    assert [s.value for s in ApprovalStatus] == ["pending", "approved", "rejected", "expired"]
    assert [s.value for s in RecommendationSide] == ["buy", "sell", "hold"]


def test_api_v1_health_envelope_and_request_id_passthrough():
    payload = asyncio.run(api_v1_routes.api_v1_health(_DummyRequest({"X-Request-Id": "req-health-1"}))).model_dump()
    assert payload["request_id"] == "req-health-1"
    assert payload["status"] == ApiStatus.SUCCESS.value
    assert payload["error"] is None
    assert payload["data"]["service"] == "gateway"
    assert payload["data"]["status"] == "ok"


def test_api_v1_enums_envelope():
    payload = asyncio.run(api_v1_routes.api_v1_enums(_DummyRequest())).model_dump()
    assert payload["status"] == ApiStatus.SUCCESS.value
    assert payload["error"] is None
    assert payload["meta"]["schema_version"] == "v1"
    data = payload["data"]
    assert data["mode"] == [m.value for m in Mode]
    assert data["risk_status"] == [s.value for s in RiskStatus]
    assert data["connection_status"] == [s.value for s in ConnectionStatus]
    assert data["timeline"] == [t.value for t in Timeline]
    assert data["approval_status"] == [s.value for s in ApprovalStatus]
    assert data["recommendation_side"] == [s.value for s in RecommendationSide]


def test_api_v1_dashboard_summary_contract_shape():
    payload = asyncio.run(api_v1_routes.api_v1_dashboard_summary(_DummyRequest())).model_dump(mode="json")
    assert payload["status"] == ApiStatus.SUCCESS.value
    assert payload["error"] is None

    data = payload["data"]
    assert data["mode"] in [m.value for m in Mode]
    assert isinstance(data["execution_enabled"], bool)
    assert isinstance(data["approval_required"], bool)
    assert data["risk_status"] in [s.value for s in RiskStatus]
    assert isinstance(data["kill_switch"], bool)
    assert set(data["portfolio"].keys()) == {
        "total_value",
        "cash",
        "unrealized_pnl",
        "realized_pnl_24h",
        "exposure_used_pct",
        "leverage",
    }
    assert set(data["connections"].keys()) == {
        "connected_exchanges",
        "connected_providers",
        "failed",
        "last_sync",
    }
    assert isinstance(data["watchlist"], list)
    assert isinstance(data["recent_explanations"], list)
    assert isinstance(data["recommendations"], list)
    assert isinstance(data["upcoming_catalysts"], list)


def test_api_v1_research_explain_envelope(monkeypatch):
    async def _fake_explain(_req):
        return ExplainResponse(
            asset="SOL",
            question="Why is SOL moving?",
            current_cause="Volume and headline expansion.",
            past_precedent="Prior roadmap reaction.",
            future_catalyst="Upcoming governance vote.",
            confidence=0.78,
            evidence=[{"type": "market", "source": "coinbase"}],
            execution_disabled=True,
        )

    monkeypatch.setattr(api_v1_routes.query_routes, "explain", _fake_explain)
    req = api_v1_routes.ResearchExplainRequest(question="Why is SOL moving?", asset="SOL")
    payload = asyncio.run(api_v1_routes.api_v1_research_explain(_DummyRequest(), req)).model_dump(mode="json")

    assert payload["status"] == ApiStatus.SUCCESS.value
    assert payload["error"] is None
    assert payload["data"]["asset"] == "SOL"
    assert payload["data"]["execution_disabled"] is True
    assert isinstance(payload["data"]["evidence"], list)


def test_api_v1_research_search_envelope(monkeypatch):
    async def _fake_documents_search(_req):
        return DocumentSearchResponse(
            results=[
                DocumentOut(
                    id="doc-1",
                    source="newsapi",
                    title="SOL network update",
                    timeline="present",
                    confidence=0.73,
                    snippet="Validator activity increased.",
                )
            ]
        )

    monkeypatch.setattr(api_v1_routes.query_routes, "documents_search", _fake_documents_search)
    req = api_v1_routes.ResearchSearchRequest(query="SOL update", asset="SOL", page=1, page_size=10)
    payload = asyncio.run(api_v1_routes.api_v1_research_search(_DummyRequest(), req)).model_dump(mode="json")

    assert payload["status"] == ApiStatus.SUCCESS.value
    assert payload["error"] is None
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["page_size"] == 10
    assert payload["meta"]["total"] == 1
    assert payload["data"]["items"][0]["source"] == "newsapi"
    assert payload["data"]["items"][0]["timeline"] == Timeline.PRESENT.value


def test_api_v1_research_history_error_envelope_when_db_unavailable():
    payload = asyncio.run(
        api_v1_routes.api_v1_research_history(_DummyRequest(), asset="SOL", page=1, page_size=5)
    ).model_dump(mode="json")

    assert payload["status"] == ApiStatus.ERROR.value
    assert payload["data"] is None
    assert payload["error"]["code"] == "SOURCE_UNAVAILABLE"
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["page_size"] == 5


def test_api_v1_market_snapshot_envelope(monkeypatch):
    async def _fake_snapshot(symbol):
        assert symbol == "SOL-USD"
        return {
            "symbol": "SOL-USD",
            "exchange": "coinbase",
            "last_price": "187.42",
            "bid": "187.40",
            "ask": "187.45",
            "spread": "0.05",
            "timestamp": "2026-03-11T12:55:00Z",
            "raw": {"volume_24h": "1823400.22"},
        }

    monkeypatch.setattr(api_v1_routes.query_routes, "market_snapshot", _fake_snapshot)
    payload = asyncio.run(
        api_v1_routes.api_v1_market_snapshot(_DummyRequest(), asset="sol", exchange="coinbase")
    ).model_dump(mode="json")

    assert payload["status"] == ApiStatus.SUCCESS.value
    assert payload["error"] is None
    assert payload["data"]["asset"] == "SOL"
    assert payload["data"]["last_price"] == 187.42
    assert payload["data"]["volume_24h"] == 1823400.22


def test_api_v1_market_candles_returns_degraded_success_without_db():
    payload = asyncio.run(
        api_v1_routes.api_v1_market_candles(
            _DummyRequest(),
            asset="btc",
            interval="1h",
            limit=5,
            exchange="coinbase",
        )
    ).model_dump(mode="json")

    assert payload["status"] in [ApiStatus.SUCCESS.value, ApiStatus.ERROR.value]
    if payload["status"] == ApiStatus.SUCCESS.value:
        assert payload["data"]["asset"] == "BTC"
        assert payload["data"]["interval"] == "1h"
        assert isinstance(payload["data"]["candles"], list)


def test_api_v1_trading_recommendations_and_approvals_flow(monkeypatch):
    async def _fake_propose_trade(_req):
        return TradeProposalResponse(
            asset="SOL",
            question="Should we open a SOL paper position now?",
            side="buy",
            suggested_quantity=1.2,
            estimated_price=145.0,
            estimated_notional_usd=174.0,
            rationale="Momentum setup.",
            confidence=0.74,
            execution_disabled=True,
            requires_user_approval=True,
        )

    monkeypatch.setattr(api_v1_routes.query_routes, "propose_trade", _fake_propose_trade)
    api_v1_routes._APPROVALS.clear()

    recs = asyncio.run(
        api_v1_routes.api_v1_trading_recommendations(_DummyRequest(), asset="SOL")
    ).model_dump(mode="json")
    assert recs["status"] == ApiStatus.SUCCESS.value
    assert len(recs["data"]["items"]) == 1
    rec = recs["data"]["items"][0]
    assert rec["id"] == "rec_SOL"
    assert rec["approval_required"] is True
    assert rec["execution_disabled"] is True

    detail = asyncio.run(
        api_v1_routes.api_v1_trading_recommendation_detail(_DummyRequest(), recommendation_id="rec_SOL")
    ).model_dump(mode="json")
    assert detail["status"] == ApiStatus.SUCCESS.value
    assert detail["data"]["recommendation"]["asset"] == "SOL"
    assert detail["data"]["recommendation"]["approval_id"] == "appr_rec_SOL"

    approvals = asyncio.run(api_v1_routes.api_v1_approvals(_DummyRequest())).model_dump(mode="json")
    assert approvals["status"] == ApiStatus.SUCCESS.value
    assert len(approvals["data"]["items"]) >= 1
    assert approvals["data"]["items"][0]["status"] == ApprovalStatus.PENDING.value

    approved = asyncio.run(
        api_v1_routes.api_v1_approval_approve(
            _DummyRequest(),
            approval_id="appr_rec_SOL",
            payload=api_v1_routes.ApprovalDecisionRequest(notes="ok"),
        )
    ).model_dump(mode="json")
    assert approved["status"] == ApiStatus.SUCCESS.value
    assert approved["data"]["status"] == ApprovalStatus.APPROVED.value


def test_api_v1_trading_recommendation_approve_and_reject_contract(monkeypatch):
    async def _fake_propose_trade(_req):
        return TradeProposalResponse(
            asset="BTC",
            question="Should we open a BTC paper position now?",
            side="buy",
            suggested_quantity=0.1,
            estimated_price=80000.0,
            estimated_notional_usd=8000.0,
            rationale="Trend follow setup.",
            confidence=0.8,
            execution_disabled=True,
            requires_user_approval=True,
        )

    monkeypatch.setattr(api_v1_routes.query_routes, "propose_trade", _fake_propose_trade)
    api_v1_routes._APPROVALS.clear()
    api_v1_routes._KILL_SWITCH.update({"enabled": False, "reason": "", "changed_at": None, "changed_by": None})
    api_v1_routes._RISK_STATE["risk_status"] = RiskStatus.SAFE.value

    approved = asyncio.run(
        api_v1_routes.api_v1_trading_recommendation_approve(
            _DummyRequest(),
            recommendation_id="rec_BTC",
            payload=api_v1_routes.RecommendationApproveRequest(mode=Mode.PAPER, notes="approved"),
        )
    ).model_dump(mode="json")
    assert approved["status"] == ApiStatus.SUCCESS.value
    assert approved["data"]["approval_status"] == ApprovalStatus.APPROVED.value
    assert approved["data"]["execution_mode"] == Mode.PAPER.value
    assert approved["data"]["execution_disabled"] is True

    rejected = asyncio.run(
        api_v1_routes.api_v1_trading_recommendation_reject(
            _DummyRequest(),
            recommendation_id="rec_BTC",
            payload=api_v1_routes.RecommendationRejectRequest(reason="not now"),
        )
    ).model_dump(mode="json")
    assert rejected["status"] == ApiStatus.SUCCESS.value
    assert rejected["data"]["approval_status"] == ApprovalStatus.REJECTED.value


def test_api_v1_trading_approve_blocked_by_mode_and_role(monkeypatch):
    async def _fake_propose_trade(_req):
        return TradeProposalResponse(
            asset="ETH",
            question="Should we open an ETH paper position now?",
            side="buy",
            suggested_quantity=0.5,
            estimated_price=3500.0,
            estimated_notional_usd=1750.0,
            rationale="Signal present.",
            confidence=0.81,
            execution_disabled=False,
            requires_user_approval=False,
        )

    monkeypatch.setattr(api_v1_routes.query_routes, "propose_trade", _fake_propose_trade)
    api_v1_routes._KILL_SWITCH.update({"enabled": False, "reason": "", "changed_at": None, "changed_by": None})
    api_v1_routes._RISK_STATE["risk_status"] = RiskStatus.SAFE.value

    blocked_mode = asyncio.run(
        api_v1_routes.api_v1_trading_recommendation_approve(
            _DummyRequest({"X-User-Role": "trader"}),
            recommendation_id="rec_ETH",
            payload=api_v1_routes.RecommendationApproveRequest(mode=Mode.RESEARCH_ONLY),
        )
    ).model_dump(mode="json")
    assert blocked_mode["status"] == ApiStatus.ERROR.value
    assert blocked_mode["error"]["code"] == MODE_BLOCKED

    blocked_role = asyncio.run(
        api_v1_routes.api_v1_trading_recommendation_approve(
            _DummyRequest({"X-User-Role": "analyst"}),
            recommendation_id="rec_ETH",
            payload=api_v1_routes.RecommendationApproveRequest(mode=Mode.PAPER),
        )
    ).model_dump(mode="json")
    assert blocked_role["status"] == ApiStatus.ERROR.value
    assert blocked_role["error"]["code"] == ROLE_NOT_ALLOWED


def test_api_v1_trading_reject_and_approval_reject_blocked_by_role():
    api_v1_routes._APPROVALS.clear()
    api_v1_routes._APPROVALS["appr_rec_SOL"] = {
        "id": "appr_rec_SOL",
        "trade_id": "rec_SOL",
        "asset": "SOL",
        "side": "buy",
        "size_pct": 1.0,
        "confidence": 0.7,
        "reason": "Approval required by policy",
        "status": ApprovalStatus.PENDING.value,
        "created_at": "2026-03-11T13:00:00Z",
        "decided_at": None,
        "notes": None,
    }

    denied_recommendation_reject = asyncio.run(
        api_v1_routes.api_v1_trading_recommendation_reject(
            _DummyRequest({"X-User-Role": "analyst"}),
            recommendation_id="rec_SOL",
            payload=api_v1_routes.RecommendationRejectRequest(reason="no"),
        )
    ).model_dump(mode="json")
    assert denied_recommendation_reject["status"] == ApiStatus.ERROR.value
    assert denied_recommendation_reject["error"]["code"] == ROLE_NOT_ALLOWED

    denied_approval_reject = asyncio.run(
        api_v1_routes.api_v1_approval_reject(
            _DummyRequest({"X-User-Role": "viewer"}),
            approval_id="appr_rec_SOL",
            payload=api_v1_routes.ApprovalDecisionRequest(notes="blocked"),
        )
    ).model_dump(mode="json")
    assert denied_approval_reject["status"] == ApiStatus.ERROR.value
    assert denied_approval_reject["error"]["code"] == ROLE_NOT_ALLOWED


def test_api_v1_risk_endpoints_and_kill_switch_policy_block(monkeypatch):
    async def _fake_propose_trade(_req):
        return TradeProposalResponse(
            asset="SOL",
            question="Should we open SOL now?",
            side="buy",
            suggested_quantity=1.0,
            estimated_price=145.0,
            estimated_notional_usd=145.0,
            rationale="Signal present.",
            confidence=0.75,
            execution_disabled=False,
            requires_user_approval=False,
        )

    monkeypatch.setattr(api_v1_routes.query_routes, "propose_trade", _fake_propose_trade)
    api_v1_routes._APPROVALS.clear()
    api_v1_routes._KILL_SWITCH.update({"enabled": False, "reason": "", "changed_at": None, "changed_by": None})
    api_v1_routes._RISK_STATE.update(
        {
            "risk_status": RiskStatus.SAFE.value,
            "exposure_used_pct": 18.4,
            "drawdown_today_pct": 0.8,
            "drawdown_week_pct": 1.2,
            "leverage": 1.0,
            "blocked_trades_count": 0,
            "active_warnings": [],
        }
    )

    summary = asyncio.run(api_v1_routes.api_v1_risk_summary(_DummyRequest())).model_dump(mode="json")
    assert summary["status"] == ApiStatus.SUCCESS.value
    assert summary["data"]["risk_status"] == RiskStatus.SAFE.value
    assert summary["data"]["kill_switch"] is False

    denied_limits = asyncio.run(
        api_v1_routes.api_v1_risk_limits_update(
            _DummyRequest({"X-User-Role": "trader"}),
            payload=api_v1_routes.RiskLimitsUpdateRequest(**api_v1_routes._RISK_LIMITS),
        )
    ).model_dump(mode="json")
    assert denied_limits["status"] == ApiStatus.ERROR.value
    assert denied_limits["error"]["code"] == ROLE_NOT_ALLOWED

    allowed_limits = asyncio.run(
        api_v1_routes.api_v1_risk_limits_update(
            _DummyRequest({"X-User-Role": "owner"}),
            payload=api_v1_routes.RiskLimitsUpdateRequest(**api_v1_routes._RISK_LIMITS),
        )
    ).model_dump(mode="json")
    assert allowed_limits["status"] == ApiStatus.SUCCESS.value
    assert allowed_limits["data"]["max_position_size_pct"] == api_v1_routes._RISK_LIMITS["max_position_size_pct"]

    kill_on = asyncio.run(
        api_v1_routes.api_v1_risk_kill_switch(
            _DummyRequest({"X-User-Role": "trader"}),
            payload=api_v1_routes.KillSwitchRequest(enabled=True, reason="manual"),
        )
    ).model_dump(mode="json")
    assert kill_on["status"] == ApiStatus.SUCCESS.value
    assert kill_on["data"]["kill_switch"] is True

    blocked = asyncio.run(
        api_v1_routes.api_v1_trading_recommendation_approve(
            _DummyRequest({"X-User-Role": "trader"}),
            recommendation_id="rec_SOL",
            payload=api_v1_routes.RecommendationApproveRequest(mode=Mode.LIVE_AUTO),
        )
    ).model_dump(mode="json")
    assert blocked["status"] == ApiStatus.ERROR.value
    assert blocked["error"]["code"] == KILL_SWITCH_ACTIVE


def test_api_v1_connections_exchange_and_provider_contracts():
    api_v1_routes._EXCHANGE_CONNECTIONS.clear()
    api_v1_routes._PROVIDER_CONNECTIONS.clear()

    listed = asyncio.run(api_v1_routes.api_v1_connections_exchanges(_DummyRequest())).model_dump(mode="json")
    assert listed["status"] == ApiStatus.SUCCESS.value
    assert len(listed["data"]["items"]) >= 1

    created = asyncio.run(
        api_v1_routes.api_v1_connections_exchanges_create(
            _DummyRequest({"X-User-Role": "owner"}),
            payload=api_v1_routes.ExchangeConnectionCreateRequest(
                provider="kraken",
                label="Research Kraken",
                environment="live",
                credentials={"api_key": "x", "api_secret": "y"},
                permissions={"read_only": True, "allow_live_trading": False},
            ),
        )
    ).model_dump(mode="json")
    assert created["status"] == ApiStatus.SUCCESS.value
    assert created["data"]["provider"] == "kraken"

    tested = asyncio.run(
        api_v1_routes.api_v1_connections_exchanges_test(
            _DummyRequest({"X-User-Role": "analyst"}),
            payload=api_v1_routes.ExchangeConnectionTestRequest(
                provider="coinbase",
                environment="live",
                credentials={"api_key": "k"},
            ),
        )
    ).model_dump(mode="json")
    assert tested["status"] == ApiStatus.SUCCESS.value
    assert tested["data"]["success"] is True

    denied_delete = asyncio.run(
        api_v1_routes.api_v1_connections_exchanges_delete(
            _DummyRequest({"X-User-Role": "trader"}),
            connection_id=created["data"]["id"],
        )
    ).model_dump(mode="json")
    assert denied_delete["status"] == ApiStatus.ERROR.value
    assert denied_delete["error"]["code"] == ROLE_NOT_ALLOWED

    providers = asyncio.run(api_v1_routes.api_v1_connections_providers(_DummyRequest())).model_dump(mode="json")
    assert providers["status"] == ApiStatus.SUCCESS.value
    assert len(providers["data"]["items"]) >= 1

    provider_test = asyncio.run(
        api_v1_routes.api_v1_connections_providers_test(
            _DummyRequest({"X-User-Role": "analyst"}),
            payload=api_v1_routes.ProviderConnectionTestRequest(provider="newsapi", credentials={"api_key": "x"}),
        )
    ).model_dump(mode="json")
    assert provider_test["status"] == ApiStatus.SUCCESS.value
    assert provider_test["data"]["success"] is True

    provider_upsert_denied = asyncio.run(
        api_v1_routes.api_v1_connections_providers_upsert(
            _DummyRequest({"X-User-Role": "trader"}),
            payload=api_v1_routes.ProviderConnectionUpsertRequest(provider="messari", label="Messari"),
        )
    ).model_dump(mode="json")
    assert provider_upsert_denied["status"] == ApiStatus.ERROR.value
    assert provider_upsert_denied["error"]["code"] == ROLE_NOT_ALLOWED


def test_api_v1_settings_get_and_put_contract():
    api_v1_routes._SETTINGS_STORE.clear()

    fetched = asyncio.run(api_v1_routes.api_v1_settings(_DummyRequest())).model_dump(mode="json")
    assert fetched["status"] == ApiStatus.SUCCESS.value
    assert fetched["error"] is None
    assert fetched["data"]["general"]["default_mode"] == Mode.RESEARCH_ONLY.value
    assert fetched["data"]["ai"]["show_evidence"] is True

    denied = asyncio.run(
        api_v1_routes.api_v1_settings_update(
            _DummyRequest({"X-User-Role": "trader"}),
            payload=api_v1_routes.SettingsUpdateRequest(**fetched["data"]),
        )
    ).model_dump(mode="json")
    assert denied["status"] == ApiStatus.ERROR.value
    assert denied["error"]["code"] == ROLE_NOT_ALLOWED

    updated_payload = dict(fetched["data"])
    updated_payload["general"] = dict(updated_payload["general"])
    updated_payload["general"]["timezone"] = "UTC"
    updated_payload["notifications"] = dict(updated_payload["notifications"])
    updated_payload["notifications"]["telegram"] = False

    updated = asyncio.run(
        api_v1_routes.api_v1_settings_update(
            _DummyRequest({"X-User-Role": "owner", "X-Request-Id": "req-settings-1"}),
            payload=api_v1_routes.SettingsUpdateRequest(**updated_payload),
        )
    ).model_dump(mode="json")
    assert updated["status"] == ApiStatus.SUCCESS.value
    assert updated["error"] is None
    assert updated["data"]["general"]["timezone"] == "UTC"
    assert updated["data"]["notifications"]["telegram"] is False


def test_api_v1_audit_events_filters_and_pagination_contract():
    api_v1_routes._AUDIT_EVENTS.clear()
    api_v1_routes._AUDIT_EVENTS.extend(
        [
            {
                "id": "audit_1",
                "timestamp": "2026-03-11T13:00:12Z",
                "service": "orchestrator",
                "action": "explain_asset",
                "result": "success",
                "request_id": "req_123",
                "details": "Generated explanation for SOL",
            },
            {
                "id": "audit_2",
                "timestamp": "2026-03-11T13:02:12Z",
                "service": "risk",
                "action": "evaluate_trade",
                "result": "blocked",
                "request_id": "req_124",
                "details": "Execution disabled in research mode",
            },
        ]
    )

    payload = asyncio.run(
        api_v1_routes.api_v1_audit_events(
            _DummyRequest(),
            service="orchestrator",
            result="success",
            page=1,
            page_size=10,
        )
    ).model_dump(mode="json")

    assert payload["status"] == ApiStatus.SUCCESS.value
    assert payload["error"] is None
    assert payload["meta"]["page"] == 1
    assert payload["meta"]["page_size"] == 10
    assert payload["meta"]["total"] == 1
    assert len(payload["data"]["items"]) == 1
    assert payload["data"]["items"][0]["service"] == "orchestrator"
    assert payload["data"]["items"][0]["result"] == "success"


def test_api_v1_terminal_execute_read_only_command_contract():
    payload = asyncio.run(
        api_v1_routes.api_v1_terminal_execute(
            _DummyRequest({"X-User-Role": "analyst"}),
            payload=api_v1_routes.TerminalExecuteRequest(command="status"),
        )
    ).model_dump(mode="json")

    assert payload["status"] == ApiStatus.SUCCESS.value
    assert payload["error"] is None
    assert payload["data"]["requires_confirmation"] is False
    assert len(payload["data"]["output"]) >= 1


def test_api_v1_terminal_execute_requires_confirmation_and_confirm_flow():
    api_v1_routes._TERMINAL_CONFIRMATIONS.clear()
    api_v1_routes._KILL_SWITCH.update({"enabled": False, "reason": "", "changed_at": None, "changed_by": None})
    api_v1_routes._RISK_STATE["risk_status"] = RiskStatus.SAFE.value

    execute = asyncio.run(
        api_v1_routes.api_v1_terminal_execute(
            _DummyRequest({"X-User-Role": "owner"}),
            payload=api_v1_routes.TerminalExecuteRequest(command="kill-switch on"),
        )
    ).model_dump(mode="json")
    assert execute["status"] == ApiStatus.SUCCESS.value
    assert execute["data"]["requires_confirmation"] is True
    token = execute["data"]["confirmation_token"]
    assert token

    confirmed = asyncio.run(
        api_v1_routes.api_v1_terminal_confirm(
            _DummyRequest({"X-User-Role": "owner"}),
            payload=api_v1_routes.TerminalConfirmRequest(confirmation_token=token),
        )
    ).model_dump(mode="json")
    assert confirmed["status"] == ApiStatus.SUCCESS.value
    assert confirmed["data"]["requires_confirmation"] is False
    assert api_v1_routes._KILL_SWITCH["enabled"] is True


def test_api_v1_terminal_execute_unknown_or_role_blocked():
    unknown = asyncio.run(
        api_v1_routes.api_v1_terminal_execute(
            _DummyRequest({"X-User-Role": "owner"}),
            payload=api_v1_routes.TerminalExecuteRequest(command="not-a-real-command"),
        )
    ).model_dump(mode="json")
    assert unknown["status"] == ApiStatus.ERROR.value
    assert unknown["error"]["code"] == UNKNOWN_COMMAND

    blocked = asyncio.run(
        api_v1_routes.api_v1_terminal_execute(
            _DummyRequest({"X-User-Role": "viewer"}),
            payload=api_v1_routes.TerminalExecuteRequest(command="kill-switch on"),
        )
    ).model_dump(mode="json")
    assert blocked["status"] == ApiStatus.ERROR.value
    assert blocked["error"]["code"] == ROLE_NOT_ALLOWED
