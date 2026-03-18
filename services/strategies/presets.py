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
            "min_cross_gap_pct": 0.03,
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
