from __future__ import annotations

from pathlib import Path

import yaml

from services.strategies.strategy_registry import SUPPORTED


CONFIG_ROOT = Path("configs/strategies")

EXPECTED_CONFIGS = {
    "ema_cross_default.yaml": "ema_cross",
    "breakout_donchian_default.yaml": "breakout_donchian",
    "pullback_recovery_default.yaml": "pullback_recovery",
}

EXPECTATION_KEYS = {
    "source",
    "tolerance_pct",
    "metric_basis",
    "win_rate",
    "avg_win_return_pct",
    "avg_loss_return_pct",
}


def _load_config(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text())
    assert isinstance(payload, dict)
    return payload


def test_challenger_governance_configs_are_inactive_and_registry_backed():
    for filename, strategy_name in EXPECTED_CONFIGS.items():
        payload = _load_config(CONFIG_ROOT / filename)
        activation = payload["activation"]
        strategy = payload["strategy"]

        assert activation["status"] == "governance_only"
        assert activation["campaign_enabled"] is False
        assert activation["promotion_candidate"] is False
        assert strategy["trade_enabled"] is False
        assert strategy["name"] == strategy_name
        assert strategy["name"] in SUPPORTED


def test_challenger_governance_configs_define_manual_review_contracts():
    for filename in EXPECTED_CONFIGS:
        payload = _load_config(CONFIG_ROOT / filename)
        expectations = payload["promotion"]["paper"]["backtest_expectations"]
        checklist = set(payload["manual_review"]["checklist"])
        no_trade_filters = payload["strategy"]["no_trade_filters"]

        assert set(expectations) == EXPECTATION_KEYS
        assert expectations["source"] is None
        assert expectations["metric_basis"] == "net_return_pct"
        assert payload["manual_review"]["required"] is True
        assert "backtest_expectations_populated_from_archive" in checklist
        assert "net_fee_expectancy_positive" in checklist
        assert "no_trade_filters_enabled_or_explicitly_waived" in checklist
        assert isinstance(no_trade_filters, dict)
        assert no_trade_filters
