from __future__ import annotations

from dashboard.components.kpi_builders import (
    build_markets_kpis,
    build_overview_kpis,
    build_signals_kpis,
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
