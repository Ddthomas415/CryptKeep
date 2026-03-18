from __future__ import annotations

from services.strategies.hypotheses import get_strategy_hypothesis, list_strategy_hypotheses


def test_list_strategy_hypotheses_covers_supported_baselines():
    rows = list_strategy_hypotheses()

    assert [row["strategy"] for row in rows] == [
        "breakout_donchian",
        "ema_cross",
        "mean_reversion_rsi",
    ]
    for row in rows:
        assert row["market_assumption"]
        assert row["required_data"]
        assert row["entry_rules"]
        assert row["exit_rules"]
        assert row["no_trade_rules"]
        assert row["invalidation_conditions"]
        assert row["expected_failure_regimes"]


def test_get_strategy_hypothesis_returns_defensive_copy():
    item = get_strategy_hypothesis("ema_cross")
    assert item is not None
    item["notes"].append("mutated")

    fresh = get_strategy_hypothesis("ema_cross")
    assert fresh is not None
    assert "mutated" not in fresh["notes"]


def test_get_strategy_hypothesis_returns_none_for_unknown():
    assert get_strategy_hypothesis("unknown_strategy") is None
