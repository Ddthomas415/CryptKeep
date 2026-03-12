from __future__ import annotations

from dashboard.components.kpi_builders import (
    build_automation_kpis,
    build_markets_kpis,
    build_overview_kpis,
    build_portfolio_kpis,
    build_signals_kpis,
    build_trades_kpis,
)


def test_build_overview_kpis_formats_portfolio_and_status() -> None:
    payload = build_overview_kpis(
        portfolio={"total_value": 124850.0, "cash": 48120.0, "unrealized_pnl": 2145.0},
        signal_count=3,
        execution_enabled=False,
    )
    assert payload[0]["value"] == "$124,850.00"
    assert payload[0]["delta"] == "Cash $48,120.00"
    assert payload[2]["value"] == "3"
    assert payload[3]["value"] == "Research Only"


def test_build_markets_kpis_formats_market_detail() -> None:
    payload = build_markets_kpis(
        {
            "price": 187.42,
            "change_24h_pct": 6.9,
            "signal": "research",
            "status": "pending_review",
            "confidence": 0.78,
            "volume_trend": "high",
        }
    )
    assert payload[0]["value"] == "$187.42"
    assert payload[0]["delta"] == "24h +6.9%"
    assert payload[1]["value"] == "Research"
    assert payload[2]["value"] == "78%"
    assert payload[3]["value"] == "High"


def test_build_signals_kpis_formats_signal_detail() -> None:
    payload = build_signals_kpis(
        {
            "signal": "buy",
            "status": "pending_review",
            "confidence": 0.81,
            "change_24h_pct": 6.5,
            "price": 200.0,
            "execution_disabled": True,
            "risk_note": "Research only.",
        }
    )
    assert payload[0]["value"] == "Buy"
    assert payload[1]["value"] == "81%"
    assert payload[2]["value"] == "+6.5%"
    assert payload[2]["delta"] == "$200.00"
    assert payload[3]["value"] == "Disabled"
    assert payload[3]["delta"] == "Research only."


def test_build_portfolio_kpis_formats_portfolio_summary() -> None:
    payload = build_portfolio_kpis(
        portfolio={
            "total_value": 124850.0,
            "cash": 48120.0,
            "unrealized_pnl": 2145.0,
            "exposure_used_pct": 18.4,
            "leverage": 1.2,
        },
        positions=[
            {"asset": "BTC"},
            {"asset": "SOL"},
        ],
    )
    assert payload[0]["value"] == "$124,850.00"
    assert payload[0]["delta"] == "Cash $48,120.00"
    assert payload[1]["value"] == "$2,145.00"
    assert payload[2]["value"] == "18.4%"
    assert payload[2]["delta"] == "Leverage 1.2x"
    assert payload[3]["value"] == "2"


def test_build_trades_kpis_formats_trade_state() -> None:
    payload = build_trades_kpis(
        approval_required=True,
        pending_approvals=[
            {"asset": "SOL", "side": "buy"},
            {"asset": "BTC", "side": "sell"},
        ],
        recent_fills=[
            {"asset": "ETH", "side": "sell", "ts": "2026-03-11T11:05:00Z"},
        ],
    )
    assert payload[0]["value"] == "Approval Required"
    assert payload[1]["value"] == "2"
    assert payload[1]["delta"] == "SOL"
    assert payload[2]["value"] == "1"
    assert payload[2]["delta"] == "ETH"
    assert payload[3]["value"] == "SELL"


def test_build_automation_kpis_formats_runtime_summary() -> None:
    payload = build_automation_kpis(
        {
            "execution_enabled": True,
            "dry_run_mode": False,
            "default_mode": "live_approval",
            "executor_mode": "live",
            "schedule": "hourly",
            "executor_poll_sec": 3.0,
            "marketplace_routing": "approval gated",
            "approval_required_for_live": True,
        }
    )
    assert payload[0]["value"] == "Enabled"
    assert payload[0]["delta"] == "Live path available"
    assert payload[1]["value"] == "Live Approval"
    assert payload[1]["delta"] == "LIVE"
    assert payload[2]["value"] == "Hourly"
    assert payload[2]["delta"] == "Poll 3s"
    assert payload[3]["value"] == "Approval Gated"
    assert payload[3]["delta"] == "Approval gated"
