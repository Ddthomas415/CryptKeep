from __future__ import annotations

from dashboard.services.intelligence import build_opportunity_snapshot


def test_build_opportunity_snapshot_scores_high_quality_buy_setup() -> None:
    payload = build_opportunity_snapshot(
        signal_row={"signal": "buy", "confidence": 0.82},
        market_row={"price": 200.0, "spread": 0.2, "volume_24h": 55000000.0, "change_24h_pct": 6.5},
        reliability={"hit_rate": 0.68, "n_scored": 84, "avg_return_bps": 160.0},
        summary={"current_regime": "trend_up"},
    )

    assert payload["regime"] == "trend_up"
    assert payload["tradeability"] > 0.8
    assert payload["setup_quality"] > 0.5
    assert payload["opportunity_score"] > 0.6
    assert payload["category"] in {"top_opportunity", "watch_closely"}


def test_build_opportunity_snapshot_penalizes_risk_off_buy_setup() -> None:
    payload = build_opportunity_snapshot(
        signal_row={"signal": "buy", "confidence": 0.6},
        market_row={"price": 200.0, "spread": 3.0, "volume_24h": 2000000.0, "change_24h_pct": -4.0},
        reliability=None,
        summary={"current_regime": "risk_off"},
    )

    assert payload["regime"] == "risk_off"
    assert payload["regime_fit"] < 0.5
    assert payload["tradeability"] < 0.6
    assert payload["risk_penalty"] > 0.0
    assert payload["category"] in {"needs_confirmation", "avoid_for_now"}
