import pytest
import yaml
from pathlib import Path

from services.execution import strategy_runner as runner


KEYS = ("stop_loss_pct", "take_profit_pct", "trailing_stop_pct", "max_bars_hold")


def resolve(monkeypatch, local, selected="sma_200_trend"):
    monkeypatch.setenv("CBP_STRATEGY_NAME", selected)
    monkeypatch.delenv("CBP_STRATEGY_PRESET", raising=False)
    monkeypatch.setattr(runner, "load_user_yaml", lambda **kw: {"strategy_runner": local})
    return runner._cfg()


def test_es_preset_matches_declared_exit_policy(monkeypatch):
    cfg = resolve(monkeypatch, {"strategy": {"name": "momentum"},
                                "risk": {k: 99 for k in KEYS}})
    declared = yaml.safe_load(Path("configs/strategies/es_daily_trend_v1.yaml").read_text())["risk"]
    assert {k: cfg[k] for k in KEYS} == {k: declared[k] for k in KEYS}
    assert "risk" not in cfg  # Unrelated preset limits are not imported.


def test_same_identity_override_and_top_level_precedence(monkeypatch):
    cfg = resolve(monkeypatch, {"strategy": {"name": "sma_200_trend"},
                                "risk": {"trailing_stop_pct": .04},
                                "trailing_stop_pct": .01})
    assert cfg["trailing_stop_pct"] == .01


def test_unnamed_managed_local_cannot_override(monkeypatch):
    cfg = resolve(monkeypatch, {"risk": {"trailing_stop_pct": .04}})
    assert cfg["trailing_stop_pct"] == 0


def test_other_preset_keeps_absent_defaults(monkeypatch):
    cfg = resolve(monkeypatch, {"strategy": {"name": "ema_cross"}}, "ema_cross")
    assert not set(KEYS).intersection(cfg)


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("value", [None, "garbage", float("nan"), float("inf"), -1, True])
def test_invalid_owned_value_fails_closed(monkeypatch, key, value):
    with pytest.raises(ValueError, match="invalid_exit_control"):
        resolve(monkeypatch, {"strategy": {"name": "sma_200_trend"}, "risk": {key: value}})


def test_fractional_bar_limit_rejected(monkeypatch):
    with pytest.raises(ValueError, match="invalid_exit_control:max_bars_hold"):
        resolve(monkeypatch, {"strategy": {"name": "sma_200_trend"}, "max_bars_hold": 1.5})
