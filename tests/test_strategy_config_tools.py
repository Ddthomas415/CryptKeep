from __future__ import annotations

from services.strategies import config_tools as ct


def test_build_strategy_block_ema_typed_fields():
    st = ct.build_strategy_block(
        name="ema_cross",
        trade_enabled=True,
        params={"ema_fast": 9.9, "ema_slow": 21.2, "filter_window": 8.8, "min_volume_ratio": 1.1},
    )
    assert st["name"] == "ema_cross"
    assert st["trade_enabled"] is True
    assert st["ema_fast"] == 9
    assert st["ema_slow"] == 21
    assert st["filter_window"] == 8
    assert st["min_volume_ratio"] == 1.1


def test_apply_strategy_block_overwrites_strategy_mapping():
    cfg = {"risk": {"max_order_quote": 10.0}, "strategy": {"name": "ema_cross", "ema_fast": 12, "ema_slow": 26}}
    out = ct.apply_strategy_block(
        cfg,
        ct.build_strategy_block(
            name="breakout_donchian",
            trade_enabled=False,
            params={"donchian_len": 33},
        ),
    )
    assert out["risk"]["max_order_quote"] == 10.0
    assert out["strategy"]["name"] == "breakout_donchian"
    assert out["strategy"]["trade_enabled"] is False
    assert out["strategy"]["donchian_len"] == 33


def test_apply_preset_and_validate_success():
    cfg = {"strategy": {"name": "ema_cross", "ema_fast": 12, "ema_slow": 26}}
    out, vr = ct.apply_preset_and_validate(cfg, "mean_reversion_default")
    assert out["strategy"]["name"] == "mean_reversion_rsi"
    assert vr["ok"] is True
    assert vr["errors"] == []


def test_build_strategy_block_rejects_unknown_strategy():
    try:
        ct.build_strategy_block(name="unknown_strategy", trade_enabled=True, params={})
    except ValueError as e:
        assert "unsupported_strategy" in str(e)
    else:
        assert False, "expected ValueError for unsupported strategy"

def test_build_strategy_block_preserves_bool_and_ignores_unknown_params():
    st = ct.build_strategy_block(
        name="breakout_donchian",
        trade_enabled=False,
        params={"donchian_len": 30, "require_directional_confirmation": True, "unused_param": 999},
    )
    assert st["name"] == "breakout_donchian"
    assert st["trade_enabled"] is False
    assert st["donchian_len"] == 30
    assert st["require_directional_confirmation"] is True
    assert "unused_param" not in st
