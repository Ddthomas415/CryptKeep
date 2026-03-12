from __future__ import annotations

import asyncio

import pytest

import services.gateway.routes.api_v1 as api_v1_routes
from domain.policy.reason_codes import KILL_SWITCH_ACTIVE, MODE_BLOCKED, ROLE_NOT_ALLOWED
from shared.schemas.api import ApiStatus, Mode, RiskStatus
from shared.schemas.explain import ExplainResponse
from shared.schemas.trade import TradeProposalResponse


class _DummyRequest:
    def __init__(self, headers: dict[str, str] | None = None):
        self.headers = headers or {}


@pytest.fixture(autouse=True)
def _reset_api_v1_state():
    def _apply_defaults() -> None:
        api_v1_routes._APPROVALS.clear()
        api_v1_routes._TERMINAL_CONFIRMATIONS.clear()
        api_v1_routes._KILL_SWITCH.update({"enabled": False, "reason": "", "changed_at": None, "changed_by": None})
        api_v1_routes._RISK_STATE.update(
            {
                "risk_status": RiskStatus.SAFE.value,
                "exposure_used_pct": 0.0,
                "drawdown_today_pct": 0.0,
                "drawdown_week_pct": 0.0,
                "leverage": 1.0,
                "blocked_trades_count": 0,
                "active_warnings": [],
            }
        )

    _apply_defaults()
    yield
    _apply_defaults()


def test_workflow_connect_exchange_happy_and_blocked():
    api_v1_routes._EXCHANGE_CONNECTIONS.clear()

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

    created = asyncio.run(
        api_v1_routes.api_v1_connections_exchanges_create(
            _DummyRequest({"X-User-Role": "trader"}),
            payload=api_v1_routes.ExchangeConnectionCreateRequest(
                provider="kraken",
                label="Ops Kraken",
                environment="live",
                credentials={"api_key": "x", "api_secret": "y"},
                permissions={"read_only": True, "allow_live_trading": False},
            ),
        )
    ).model_dump(mode="json")
    assert created["status"] == ApiStatus.SUCCESS.value

    denied = asyncio.run(
        api_v1_routes.api_v1_connections_exchanges_create(
            _DummyRequest({"X-User-Role": "viewer"}),
            payload=api_v1_routes.ExchangeConnectionCreateRequest(
                provider="binance",
                label="Blocked",
                environment="live",
            ),
        )
    ).model_dump(mode="json")
    assert denied["status"] == ApiStatus.ERROR.value
    assert denied["error"]["code"] == ROLE_NOT_ALLOWED


def test_workflow_research_query_happy(monkeypatch):
    async def _fake_explain(_req):
        return ExplainResponse(
            asset="SOL",
            question="Why is SOL moving?",
            current_cause="Market and news expansion.",
            past_precedent="Prior roadmap cycle.",
            future_catalyst="Upcoming governance event.",
            confidence=0.77,
            evidence=[{"type": "market", "source": "coinbase"}],
            execution_disabled=True,
        )

    monkeypatch.setattr(api_v1_routes.query_routes, "explain", _fake_explain)
    out = asyncio.run(
        api_v1_routes.api_v1_research_explain(
            _DummyRequest({"X-User-Role": "viewer"}),
            api_v1_routes.ResearchExplainRequest(question="Why is SOL moving?", asset="SOL"),
        )
    ).model_dump(mode="json")
    assert out["status"] == ApiStatus.SUCCESS.value
    assert out["data"]["asset"] == "SOL"


def test_workflow_approve_paper_happy_and_mode_block(monkeypatch):
    async def _fake_propose_trade(_req):
        return TradeProposalResponse(
            asset="SOL",
            question="Should we open a SOL paper position now?",
            side="buy",
            suggested_quantity=1.0,
            estimated_price=150.0,
            estimated_notional_usd=150.0,
            rationale="Momentum setup",
            confidence=0.72,
            execution_disabled=True,
            requires_user_approval=True,
        )

    monkeypatch.setattr(api_v1_routes.query_routes, "propose_trade", _fake_propose_trade)
    api_v1_routes._KILL_SWITCH.update({"enabled": False, "reason": "", "changed_at": None, "changed_by": None})
    api_v1_routes._RISK_STATE["risk_status"] = RiskStatus.SAFE.value

    approved = asyncio.run(
        api_v1_routes.api_v1_trading_recommendation_approve(
            _DummyRequest({"X-User-Role": "trader"}),
            recommendation_id="rec_SOL",
            payload=api_v1_routes.RecommendationApproveRequest(mode=Mode.PAPER),
        )
    ).model_dump(mode="json")
    assert approved["status"] == ApiStatus.SUCCESS.value

    blocked_mode = asyncio.run(
        api_v1_routes.api_v1_trading_recommendation_approve(
            _DummyRequest({"X-User-Role": "trader"}),
            recommendation_id="rec_SOL",
            payload=api_v1_routes.RecommendationApproveRequest(mode=Mode.RESEARCH_ONLY),
        )
    ).model_dump(mode="json")
    assert blocked_mode["status"] == ApiStatus.ERROR.value
    assert blocked_mode["error"]["code"] == MODE_BLOCKED


def test_workflow_approve_live_blocked_by_kill_switch(monkeypatch):
    async def _fake_propose_trade(_req):
        return TradeProposalResponse(
            asset="ETH",
            question="Should we open an ETH live position now?",
            side="buy",
            suggested_quantity=0.2,
            estimated_price=3800.0,
            estimated_notional_usd=760.0,
            rationale="Live setup",
            confidence=0.8,
            execution_disabled=False,
            requires_user_approval=False,
        )

    monkeypatch.setattr(api_v1_routes.query_routes, "propose_trade", _fake_propose_trade)
    api_v1_routes._KILL_SWITCH.update({"enabled": True, "reason": "manual", "changed_at": None, "changed_by": "owner"})
    api_v1_routes._RISK_STATE["risk_status"] = RiskStatus.BLOCKED.value

    blocked = asyncio.run(
        api_v1_routes.api_v1_trading_recommendation_approve(
            _DummyRequest({"X-User-Role": "trader"}),
            recommendation_id="rec_ETH",
            payload=api_v1_routes.RecommendationApproveRequest(mode=Mode.LIVE_APPROVAL),
        )
    ).model_dump(mode="json")
    assert blocked["status"] == ApiStatus.ERROR.value
    assert blocked["error"]["code"] == KILL_SWITCH_ACTIVE


def test_workflow_kill_switch_activate_and_release():
    api_v1_routes._KILL_SWITCH.update({"enabled": False, "reason": "", "changed_at": None, "changed_by": None})
    api_v1_routes._RISK_STATE["risk_status"] = RiskStatus.SAFE.value

    enabled = asyncio.run(
        api_v1_routes.api_v1_risk_kill_switch(
            _DummyRequest({"X-User-Role": "trader"}),
            payload=api_v1_routes.KillSwitchRequest(enabled=True, reason="manual test"),
        )
    ).model_dump(mode="json")
    assert enabled["status"] == ApiStatus.SUCCESS.value
    assert enabled["data"]["kill_switch"] is True
    assert api_v1_routes._RISK_STATE["risk_status"] == RiskStatus.BLOCKED.value

    disabled = asyncio.run(
        api_v1_routes.api_v1_risk_kill_switch(
            _DummyRequest({"X-User-Role": "owner"}),
            payload=api_v1_routes.KillSwitchRequest(enabled=False, reason="resume"),
        )
    ).model_dump(mode="json")
    assert disabled["status"] == ApiStatus.SUCCESS.value
    assert disabled["data"]["kill_switch"] is False
    assert api_v1_routes._RISK_STATE["risk_status"] == RiskStatus.SAFE.value


def test_workflow_terminal_execute_confirm_and_role_block():
    api_v1_routes._TERMINAL_CONFIRMATIONS.clear()
    api_v1_routes._KILL_SWITCH.update({"enabled": False, "reason": "", "changed_at": None, "changed_by": None})
    api_v1_routes._RISK_STATE["risk_status"] = RiskStatus.SAFE.value

    pending = asyncio.run(
        api_v1_routes.api_v1_terminal_execute(
            _DummyRequest({"X-User-Role": "owner"}),
            payload=api_v1_routes.TerminalExecuteRequest(command="kill-switch on"),
        )
    ).model_dump(mode="json")
    assert pending["status"] == ApiStatus.SUCCESS.value
    assert pending["data"]["requires_confirmation"] is True
    token = pending["data"]["confirmation_token"]
    assert token

    confirmed = asyncio.run(
        api_v1_routes.api_v1_terminal_confirm(
            _DummyRequest({"X-User-Role": "owner"}),
            payload=api_v1_routes.TerminalConfirmRequest(confirmation_token=token),
        )
    ).model_dump(mode="json")
    assert confirmed["status"] == ApiStatus.SUCCESS.value
    assert api_v1_routes._KILL_SWITCH["enabled"] is True

    blocked = asyncio.run(
        api_v1_routes.api_v1_terminal_execute(
            _DummyRequest({"X-User-Role": "viewer"}),
            payload=api_v1_routes.TerminalExecuteRequest(command="kill-switch off"),
        )
    ).model_dump(mode="json")
    assert blocked["status"] == ApiStatus.ERROR.value
    assert blocked["error"]["code"] == ROLE_NOT_ALLOWED
