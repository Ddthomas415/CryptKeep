# HS2: Preset library + apply helper (Phase 228)
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


PRESETS: Dict[str, Dict[str, Any]] = {
    "ema_cross_default": {
        "strategy": {
            "name": "ema_cross",
            "trade_enabled": True,
            "ema_fast": 12,
            "ema_slow": 26,
            "filter_window": 8,
            "min_volatility_pct": 0.20,
            "min_volume_ratio": 0.95,
            "min_trend_efficiency": 0.15,
            "min_cross_gap_pct": 0.02,
        },
    },
    "mean_reversion_default": {
        "strategy": {
            "name": "mean_reversion_rsi",
            "trade_enabled": True,
            "rsi_len": 14,
            "rsi_buy": 30.0,
            "rsi_sell": 70.0,
            "sma_len": 50,
            "filter_window": 8,
            "max_volatility_pct": 1.50,
            "min_volume_ratio": 0.90,
            "max_trend_efficiency": 0.98,
            "max_sma_distance_pct": 6.00,
            "require_reversal_confirmation": True,
        },
    },
    "breakout_default": {
        "strategy": {
            "name": "breakout_donchian",
            "trade_enabled": True,
            "donchian_len": 20,
            "filter_window": 8,
            "min_volatility_pct": 0.20,
            "min_volume_ratio": 0.95,
            "min_trend_efficiency": 0.10,
            "min_channel_width_pct": 0.25,
            "breakout_buffer_pct": 0.05,
            "require_directional_confirmation": True,
        },
    },
    "momentum_default": {
        "strategy": {
            "name": "momentum",
            "min_change_pct": 2.0,
            "max_rsi_entry": 75.0,
            "rsi_exit": 80.0,
            "sma_period": 20,
            "rsi_period": 14,
            "stop_below_sma": True,
        },
    },

    "volatility_reversal_default": {
        "strategy": {
            "name": "volatility_reversal",
            "rsi_len": 14,
            "rsi_oversold": 28.0,
            "rsi_exit": 50.0,
            "sma_len": 20,
            "min_dump_bars": 3,
            "min_dump_pct": 8.0,
            "require_volume_spike": True,
        },
    },
    "gap_fill_default": {
        "strategy": {
            "name": "gap_fill",
            "rsi_len": 14,
            "rsi_buy": 40.0,
            "rsi_sell": 60.0,
            "sma_len": 20,
            "min_gap_pct": 3.0,
            "gap_fill_target_pct": 0.618,
        },
    },
    "breakout_volume_default": {
        "strategy": {
            "name": "breakout_volume",
            "donchian_len": 20,
            "sma_len": 50,
            "min_volume_ratio": 2.0,
            "breakout_buffer_pct": 0.1,
            "min_channel_width_pct": 1.0,
            "require_close_above": True,
        },
    },

}


def _deep_merge(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(dict(base or {}))
    for k, v in (overlay or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = deepcopy(v)
    return out


def list_presets() -> list[str]:
    return sorted(PRESETS.keys())


def get_preset(name: str) -> Dict[str, Any] | None:
    p = PRESETS.get(str(name))
    return deepcopy(p) if p is not None else None


def apply_preset(cfg: Dict[str, Any], name: str, *, overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    p = get_preset(name)
    if p is None:
        raise KeyError(f"unknown_preset:{name}")
    out = _deep_merge(dict(cfg or {}), p)
    if isinstance(overrides, dict) and overrides:
        out = _deep_merge(out, overrides)
    return out
