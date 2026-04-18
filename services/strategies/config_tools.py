from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Tuple

from services.strategies.presets import apply_preset
from services.strategies.validation import validate_strategy_config


_SUPPORTED = {
    "ema_cross",
    "mean_reversion_rsi",
    "breakout_donchian",
    "momentum",
    "pullback_recovery",
    "volatility_reversal",
    "gap_fill",
    "breakout_volume",
    "funding_extreme",
    "open_interest_shift",
    "sma_200_trend",
}

_INT_FIELDS = {
    "ema_cross": ("ema_fast", "ema_slow", "filter_window"),
    "momentum": ("min_change_pct", "max_rsi_entry", "rsi_exit", "sma_period", "rsi_period"),
    "volatility_reversal": ("rsi_len", "rsi_oversold", "rsi_exit", "sma_len", "min_dump_bars", "min_dump_pct"),
    "gap_fill": ("rsi_len", "rsi_buy", "rsi_sell", "sma_len", "min_gap_pct", "gap_fill_target_pct"),
    "breakout_volume": ("donchian_len", "sma_len", "min_volume_ratio", "breakout_buffer_pct", "min_channel_width_pct"),
    "mean_reversion_rsi": ("rsi_len", "sma_len", "filter_window"),
    "breakout_donchian": ("donchian_len", "filter_window"),
    "sma_200_trend": ("sma_period", "atr_period"),
}

_FLOAT_FIELDS = {
    "ema_cross": ("min_volatility_pct", "min_volume_ratio", "min_trend_efficiency", "min_cross_gap_pct"),
    "mean_reversion_rsi": ("rsi_buy", "rsi_sell", "max_volatility_pct", "min_volume_ratio", "max_trend_efficiency", "max_sma_distance_pct"),
    "breakout_donchian": ("min_volatility_pct", "min_volume_ratio", "min_trend_efficiency", "min_channel_width_pct", "breakout_buffer_pct"),
    "sma_200_trend": ("atr_stop_multiplier", "capital_at_risk_per_trade_pct", "max_position_notional_pct", "daily_loss_halt_pct", "max_drawdown_pct", "regime_trending_floor", "regime_chop_ceiling", "regime_high_vol_ceiling"),
}

_BOOL_FIELDS = {
    "ema_cross": (),
    "momentum": (),
    "volatility_reversal": ("require_volume_spike",),
    "gap_fill": (),
    "breakout_volume": ("require_close_above",),
    "mean_reversion_rsi": ("require_reversal_confirmation",),
    "breakout_donchian": ("require_directional_confirmation",),
    "sma_200_trend": (),
}


def _name(name: str) -> str:
    return str(name or "").strip()


def supported_strategies() -> list[str]:
    return sorted(_SUPPORTED)


def build_strategy_block(
    *,
    name: str,
    trade_enabled: bool = True,
    params: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    n = _name(name)
    if n not in _SUPPORTED:
        raise ValueError(f"unsupported_strategy:{n}")
    p = dict(params or {})
    out: Dict[str, Any] = {"name": n, "trade_enabled": bool(trade_enabled)}

    for k in _INT_FIELDS.get(n, ()):
        if k in p and p.get(k) is not None:
            out[k] = int(p[k])
    for k in _FLOAT_FIELDS.get(n, ()):
        if k in p and p.get(k) is not None:
            out[k] = float(p[k])
    for k in _BOOL_FIELDS.get(n, ()):
        if k in p and p.get(k) is not None:
            out[k] = bool(p[k])
    return out


def apply_strategy_block(cfg: Dict[str, Any], strategy_block: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(dict(cfg or {}))
    out["strategy"] = deepcopy(dict(strategy_block or {}))
    return out


def validate_cfg(cfg: Dict[str, Any]) -> Dict[str, Any]:
    return validate_strategy_config(dict(cfg or {}))


def apply_preset_and_validate(cfg: Dict[str, Any], preset_name: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    out = apply_preset(dict(cfg or {}), str(preset_name))
    vr = validate_cfg(out)
    return out, vr
