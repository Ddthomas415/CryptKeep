from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from services.strategies import breakout_donchian, ema_cross, mean_reversion_rsi
from services.strategies import strategy_registry as registry
from services.strategies.config_tools import build_strategy_block
from services.strategies.presets import PRESETS, get_preset


BEFORE = Path(__file__).resolve().parents[1] / "docs/review_artifacts/exit_unblocked_variants_20261114/before"
CASES = {
    "breakout_donchian": (breakout_donchian, "breakout_default", "breakout_exit_unblocked", {"donchian_len": 3}),
    "ema_cross": (ema_cross, "ema_cross_default", "ema_cross_exit_unblocked", {"ema_fast": 2, "ema_slow": 3}),
    "mean_reversion_rsi": (
        mean_reversion_rsi, "mean_reversion_default", "mean_reversion_exit_unblocked", {"rsi_len": 3, "sma_len": 3}
    ),
}
FILTERS = [
    ("breakout_donchian", "min_volatility_pct", 10000, "low_volatility_filter"),
    ("breakout_donchian", "min_volume_ratio", 10000, "low_volume_filter"),
    ("breakout_donchian", "min_trend_efficiency", 2, "chop_filter"),
    ("breakout_donchian", "min_channel_width_pct", 10000, "narrow_channel_filter"),
    ("breakout_donchian", "require_directional_confirmation", True, "breakout_not_confirmed"),
    ("ema_cross", "min_volatility_pct", 10000, "low_volatility_filter"),
    ("ema_cross", "min_volume_ratio", 10000, "low_volume_filter"),
    ("ema_cross", "min_trend_efficiency", 2, "chop_filter"),
    ("ema_cross", "min_cross_gap_pct", 10000, "cross_gap_filter"),
    ("mean_reversion_rsi", "max_volatility_pct", 0, "high_volatility_filter"),
    ("mean_reversion_rsi", "min_volume_ratio", 10000, "low_volume_filter"),
    ("mean_reversion_rsi", "max_trend_efficiency", 0, "one_way_trend_filter"),
    ("mean_reversion_rsi", "max_sma_distance_pct", 0, "reversion_invalidation"),
    ("mean_reversion_rsi", "require_reversal_confirmation", True, "reversal_not_confirmed"),
]
DEFAULT_HASHES = {
    "ema_cross_default": "ed214dc9eab94d9d66f48edee097e07d48ec33e64d828c1667a20e3cb1714263",
    "mean_reversion_default": "89c7ba9b460e9cb68214d8c8acafc095b71b9df84e9f5664fdba93fa866a6c5a",
    "breakout_default": "e0f294a488f8dda3c7fba1a71a67929eb0d0a5f26ef024654b620daae3d06ac2",
}


def rows(closes):
    return [[i * 3600000, c, c + 0.1, c - 0.1, c, 10.0] for i, c in enumerate(closes)]


def signal_rows(name, action):
    if name == "ema_cross":
        closes = [100, 101, 102, 103, 104, 95]
        if action == "buy":
            closes = [200 - c for c in closes]
    else:
        increasing = action == ("sell" if name == "mean_reversion_rsi" else "buy")
        closes = [100 + (i if increasing else -i) for i in range(7)]
    return rows(closes)


@pytest.mark.parametrize("name,key,value,reason", FILTERS)
@pytest.mark.parametrize("action", ["sell", "buy"])
def test_each_filter_bypassed_for_sells_only(monkeypatch, name, key, value, reason, action):
    module, _, _, params = CASES[name]
    data = signal_rows(name, action)
    raw = module.signal_from_ohlcv(ohlcv=data, **params)
    assert raw["action"] == action
    if key == "require_directional_confirmation":
        # Isolate the confirmation branch; a valid Donchian break already confirms direction.
        context = module.market_context

        def unconfirmed(**kwargs):
            result = context(**kwargs)
            result["prev_close"] = data[-1][4] + (1 if action == "buy" else -1)
            return result

        monkeypatch.setattr(module, "market_context", unconfirmed)
    options = {**params, key: value}
    events = []
    implicit = module.signal_from_ohlcv(ohlcv=data, observer=events.append, **options)
    explicit = module.signal_from_ohlcv(ohlcv=data, filters_apply_to_sell=True, **options)
    variant = module.signal_from_ohlcv(ohlcv=data, filters_apply_to_sell=False, **options)
    assert implicit == explicit
    assert implicit["action"] == "hold"
    assert implicit["reason"] == reason
    assert events == [{"raw_action": action, "raw_reason": raw["reason"]}]
    assert variant["ind"] == implicit["ind"]
    if action == "sell":
        assert variant["action"] == "sell"
        assert variant["reason"] == raw["reason"]
        assert variant["ok"] is True
    else:
        assert variant == implicit


@pytest.mark.parametrize("name", CASES)
def test_observer_and_insufficient_history_unchanged(name):
    module, _, _, params = CASES[name]
    assert module.signal_from_ohlcv(ohlcv=[], **params) == module.signal_from_ohlcv(
        ohlcv=[], filters_apply_to_sell=False, **params
    )
    events = []
    baseline = module.signal_from_ohlcv(ohlcv=signal_rows(name, "sell"), observer=events.append, **params)
    variant_events = []
    variant = module.signal_from_ohlcv(
        ohlcv=signal_rows(name, "sell"), filters_apply_to_sell=False, observer=variant_events.append, **params
    )
    assert variant == baseline
    assert variant_events == events
    holds = rows([100] * 60)
    hold_params = {**params, "rsi_buy": -1, "rsi_sell": 101} if name == "mean_reversion_rsi" else params
    baseline = module.signal_from_ohlcv(ohlcv=holds, **hold_params)
    assert baseline["action"] == "hold"
    assert module.signal_from_ohlcv(ohlcv=holds, filters_apply_to_sell=False, **hold_params) == baseline


@pytest.mark.parametrize("name", CASES)
def test_presets_are_isolated_and_defaults_identical(name):
    _, default, variant, _ = CASES[name]
    original = get_preset(default)
    assert hashlib.sha256(json.dumps(original, sort_keys=True).encode()).hexdigest() == DEFAULT_HASHES[default]
    expected = deepcopy(original)
    expected["strategy"]["filters_apply_to_sell"] = False
    assert get_preset(variant) == expected
    assert PRESETS[variant]["strategy"] is not PRESETS[default]["strategy"]
    assert PRESETS[variant]["risk"] is not PRESETS[default]["risk"]
    copy = get_preset(variant)
    copy["strategy"]["filters_apply_to_sell"] = True
    assert get_preset(variant) == expected


@pytest.mark.parametrize("name", CASES)
def test_config_and_registry_forward_flag_only_when_present(monkeypatch, name):
    seen = []

    def spy(**kwargs):
        seen.append(kwargs)
        return {"ok": True, "action": "hold"}

    monkeypatch.setitem(registry.SUPPORTED, name, spy)
    for flag in [None, True, False]:
        params = {} if flag is None else {"filters_apply_to_sell": flag}
        block = build_strategy_block(name=name, params=params)
        registry.compute_signal(cfg={"strategy": block}, symbol="SOL/USD", ohlcv=[])
        if flag is None:
            assert "filters_apply_to_sell" not in block
            assert "filters_apply_to_sell" not in seen[-1]
        else:
            assert block["filters_apply_to_sell"] is flag
            assert seen[-1]["filters_apply_to_sell"] is flag


@pytest.mark.parametrize("name", CASES)
def test_runner_preset_resolution_preserves_opt_in(monkeypatch, name):
    from services.execution.strategy_runner import _strategy_block_from_runner_cfg, _resolved_exit_controls

    monkeypatch.delenv("CBP_STRATEGY_NAME", raising=False)
    monkeypatch.delenv("CBP_STRATEGY_PRESET", raising=False)
    _, default, variant, params = CASES[name]
    cfg = {"strategy_name": name, "strategy_preset": variant}
    block, preset = _strategy_block_from_runner_cfg(cfg)
    assert preset == variant
    assert block["filters_apply_to_sell"] is False
    block.update(params)
    block["min_volume_ratio"] = 10000
    out = registry.compute_signal(cfg={"strategy": block}, symbol="ADA/USD", ohlcv=signal_rows(name, "sell"))
    assert out["action"] == "sell"
    default_cfg = {"strategy_name": name, "strategy_preset": default}
    default_block, _ = _strategy_block_from_runner_cfg(default_cfg)
    assert "filters_apply_to_sell" not in default_block
    assert _resolved_exit_controls(cfg, block, variant) == _resolved_exit_controls(default_cfg, default_block, default)
    override, _ = _strategy_block_from_runner_cfg({**cfg, "strategy": {"filters_apply_to_sell": True}})
    assert override["filters_apply_to_sell"] is True
    disabled = {"strategy": {**block, "trade_enabled": False}}
    assert registry.compute_signal(cfg=disabled, symbol="ADA/USD", ohlcv=signal_rows(name, "sell"))["action"] == "hold"


def before_module(filename):
    checksums = dict(line.split(maxsplit=1)[::-1] for line in (BEFORE / "SHA256SUMS").read_text().splitlines())
    path = BEFORE / (filename + ".py")
    assert hashlib.sha256(path.read_bytes()).hexdigest() == checksums[path.name]
    name = "services.strategies._exit_before_" + filename
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_all_existing_presets_unchanged():
    original = before_module("presets").PRESETS
    assert set(PRESETS) - set(original) == {case[2] for case in CASES.values()}
    assert all(PRESETS[key] == value for key, value in original.items())


@pytest.mark.parametrize("name", CASES)
@pytest.mark.parametrize("invalid", [None, 0, 0.0, "", [], {}, "false", 1])
def test_malformed_values_cannot_enable_sell_bypass(name, invalid):
    module, _, _, params = CASES[name]
    options = {**params, "min_volume_ratio": 10000}
    data = signal_rows(name, "sell")
    baseline = module.signal_from_ohlcv(ohlcv=data, **options)
    assert baseline["reason"] == "low_volume_filter"
    assert module.signal_from_ohlcv(ohlcv=data, filters_apply_to_sell=invalid, **options) == baseline
    result = registry.compute_signal(
        cfg={"strategy": {"name": name, **options, "filters_apply_to_sell": invalid}},
        symbol="SOL/USD", ohlcv=data,
    )
    assert result["action"] == "hold"
    assert result["reason"] == "low_volume_filter"
    with pytest.raises(ValueError, match="invalid_filters_apply_to_sell"):
        build_strategy_block(name=name, params={"filters_apply_to_sell": invalid})


@pytest.mark.parametrize("name", CASES)
@pytest.mark.parametrize("scale", [0.01, 0.5, 1, 10, 100])
def test_default_outputs_equal_preserved_source_on_synthetic_sequences(name, scale):
    module, default, _, _ = CASES[name]
    old = before_module(module.__name__.rsplit(".", 1)[-1])
    params = get_preset(default)["strategy"]
    params = {k: v for k, v in params.items() if k not in {"name", "trade_enabled"}}
    data = rows([scale * (100 + ((i % 24) if (i // 24) % 2 else -(i % 24))) for i in range(145)])
    for end in range(1, len(data) + 1):
        old_events, new_events = [], []
        baseline = old.signal_from_ohlcv(ohlcv=data[:end], observer=old_events.append, **params)
        current = module.signal_from_ohlcv(ohlcv=data[:end], observer=new_events.append, **params)
        explicit = module.signal_from_ohlcv(ohlcv=data[:end], filters_apply_to_sell=True, **params)
        assert current == explicit == baseline
        assert new_events == old_events
