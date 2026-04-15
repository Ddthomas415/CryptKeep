# HS2: Preset library + apply helper (Phase 228)
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict


PRESETS: Dict[str, Dict[str, Any]] = {
    "ema_cross_default": {
        "risk": {
            "max_concurrent_positions": 5,
            "max_symbol_exposure_pct": 20.0,
            "max_total_exposure_pct": 80.0,
            "max_strategy_exposure_pct": 50.0,
            "max_open_intents_per_symbol": 1,
            "max_consecutive_risk_blocks_per_symbol": 5,
            "kill_cooldown_loops": 20,
            "enable_position_scaling": True,
            "max_adds_per_symbol": 2,
            "min_profit_to_add_pct": 1.5,
            "scale_in_size_multiplier": 0.5,
            "max_consecutive_losing_exits": 3,
            "max_strategy_drawdown_pct": 10.0,
            "performance_kill_cooldown_loops": 50,
            "target_total_deployment_pct": 60.0,
            "max_symbol_allocation_pct": 20.0,
            "min_symbol_allocation_pct": 5.0,
            "max_abs_correlation": 0.85,
        },
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
        "risk": {
            "max_concurrent_positions": 5,
            "max_symbol_exposure_pct": 20.0,
            "max_total_exposure_pct": 80.0,
            "max_strategy_exposure_pct": 50.0,
            "max_open_intents_per_symbol": 1,
            "max_consecutive_risk_blocks_per_symbol": 5,
            "kill_cooldown_loops": 20,
            "enable_position_scaling": True,
            "max_adds_per_symbol": 2,
            "min_profit_to_add_pct": 1.5,
            "scale_in_size_multiplier": 0.5,
            "max_consecutive_losing_exits": 3,
            "max_strategy_drawdown_pct": 10.0,
            "performance_kill_cooldown_loops": 50,
            "target_total_deployment_pct": 60.0,
            "max_symbol_allocation_pct": 20.0,
            "min_symbol_allocation_pct": 5.0,
            "max_abs_correlation": 0.85,
        },
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
        "risk": {
            "max_concurrent_positions": 5,
            "max_symbol_exposure_pct": 20.0,
            "max_total_exposure_pct": 80.0,
            "max_strategy_exposure_pct": 50.0,
            "max_open_intents_per_symbol": 1,
            "max_consecutive_risk_blocks_per_symbol": 5,
            "kill_cooldown_loops": 20,
            "enable_position_scaling": True,
            "max_adds_per_symbol": 2,
            "min_profit_to_add_pct": 1.5,
            "scale_in_size_multiplier": 0.5,
            "max_consecutive_losing_exits": 3,
            "max_strategy_drawdown_pct": 10.0,
            "performance_kill_cooldown_loops": 50,
            "target_total_deployment_pct": 60.0,
            "max_symbol_allocation_pct": 20.0,
            "min_symbol_allocation_pct": 5.0,
            "max_abs_correlation": 0.85,
        },
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
        "risk": {
            "max_concurrent_positions": 5,
            "max_symbol_exposure_pct": 20.0,
            "max_total_exposure_pct": 80.0,
            "max_strategy_exposure_pct": 50.0,
            "max_open_intents_per_symbol": 1,
            "max_consecutive_risk_blocks_per_symbol": 5,
            "kill_cooldown_loops": 20,
            "enable_position_scaling": True,
            "max_adds_per_symbol": 2,
            "min_profit_to_add_pct": 1.5,
            "scale_in_size_multiplier": 0.5,
            "max_consecutive_losing_exits": 3,
            "max_strategy_drawdown_pct": 10.0,
            "performance_kill_cooldown_loops": 50,
            "target_total_deployment_pct": 60.0,
            "max_symbol_allocation_pct": 20.0,
            "min_symbol_allocation_pct": 5.0,
            "max_abs_correlation": 0.85,
        },
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
        "risk": {
            "max_concurrent_positions": 5,
            "max_symbol_exposure_pct": 20.0,
            "max_total_exposure_pct": 80.0,
            "max_strategy_exposure_pct": 50.0,
            "max_open_intents_per_symbol": 1,
            "max_consecutive_risk_blocks_per_symbol": 5,
            "kill_cooldown_loops": 20,
            "enable_position_scaling": True,
            "max_adds_per_symbol": 2,
            "min_profit_to_add_pct": 1.5,
            "scale_in_size_multiplier": 0.5,
            "max_consecutive_losing_exits": 3,
            "max_strategy_drawdown_pct": 10.0,
            "performance_kill_cooldown_loops": 50,
            "target_total_deployment_pct": 60.0,
            "max_symbol_allocation_pct": 20.0,
            "min_symbol_allocation_pct": 5.0,
            "max_abs_correlation": 0.85,
        },
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
        "risk": {
            "max_concurrent_positions": 5,
            "max_symbol_exposure_pct": 20.0,
            "max_total_exposure_pct": 80.0,
            "max_strategy_exposure_pct": 50.0,
            "max_open_intents_per_symbol": 1,
            "max_consecutive_risk_blocks_per_symbol": 5,
            "kill_cooldown_loops": 20,
            "enable_position_scaling": True,
            "max_adds_per_symbol": 2,
            "min_profit_to_add_pct": 1.5,
            "scale_in_size_multiplier": 0.5,
            "max_consecutive_losing_exits": 3,
            "max_strategy_drawdown_pct": 10.0,
            "performance_kill_cooldown_loops": 50,
            "target_total_deployment_pct": 60.0,
            "max_symbol_allocation_pct": 20.0,
            "min_symbol_allocation_pct": 5.0,
            "max_abs_correlation": 0.85,
        },
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
        "risk": {
            "max_concurrent_positions": 5,
            "max_symbol_exposure_pct": 20.0,
            "max_total_exposure_pct": 80.0,
            "max_strategy_exposure_pct": 50.0,
            "max_open_intents_per_symbol": 1,
            "max_consecutive_risk_blocks_per_symbol": 5,
            "kill_cooldown_loops": 20,
            "enable_position_scaling": True,
            "max_adds_per_symbol": 2,
            "min_profit_to_add_pct": 1.5,
            "scale_in_size_multiplier": 0.5,
            "max_consecutive_losing_exits": 3,
            "max_strategy_drawdown_pct": 10.0,
            "performance_kill_cooldown_loops": 50,
            "target_total_deployment_pct": 60.0,
            "max_symbol_allocation_pct": 20.0,
            "min_symbol_allocation_pct": 5.0,
            "max_abs_correlation": 0.85,
        },
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

    "funding_extreme_default": {
        "risk": {
            "max_concurrent_positions": 5,
            "max_symbol_exposure_pct": 20.0,
            "max_total_exposure_pct": 80.0,
            "max_strategy_exposure_pct": 50.0,
            "max_open_intents_per_symbol": 1,
            "max_consecutive_risk_blocks_per_symbol": 5,
            "kill_cooldown_loops": 20,
            "enable_position_scaling": True,
            "max_adds_per_symbol": 2,
            "min_profit_to_add_pct": 1.5,
            "scale_in_size_multiplier": 0.5,
            "max_consecutive_losing_exits": 3,
            "max_strategy_drawdown_pct": 10.0,
            "performance_kill_cooldown_loops": 50,
            "target_total_deployment_pct": 60.0,
            "max_symbol_allocation_pct": 20.0,
            "min_symbol_allocation_pct": 5.0,
            "max_abs_correlation": 0.85,
        },
        "strategy": {
            "name": "funding_extreme",
            "long_crowded_threshold": 0.05,
            "short_crowded_threshold": -0.01,
        },
    },
    "open_interest_shift_default": {
        "risk": {
            "max_concurrent_positions": 5,
            "max_symbol_exposure_pct": 20.0,
            "max_total_exposure_pct": 80.0,
            "max_strategy_exposure_pct": 50.0,
            "max_open_intents_per_symbol": 1,
            "max_consecutive_risk_blocks_per_symbol": 5,
            "kill_cooldown_loops": 20,
            "enable_position_scaling": True,
            "max_adds_per_symbol": 2,
            "min_profit_to_add_pct": 1.5,
            "scale_in_size_multiplier": 0.5,
            "max_consecutive_losing_exits": 3,
            "max_strategy_drawdown_pct": 10.0,
            "performance_kill_cooldown_loops": 50,
            "target_total_deployment_pct": 60.0,
            "max_symbol_allocation_pct": 20.0,
            "min_symbol_allocation_pct": 5.0,
            "max_abs_correlation": 0.85,
        },
        "strategy": {
            "name": "open_interest_shift",
            "oi_rise_threshold_pct": 5.0,
            "oi_drop_threshold_pct": -5.0,
        },
    },

    "es_daily_trend_v1": {
        "risk": {
            "max_concurrent_positions": 1,
            "max_symbol_exposure_pct": 10.0,
            "max_total_exposure_pct": 10.0,
            "max_strategy_exposure_pct": 10.0,
            "max_open_intents_per_symbol": 1,
            "max_consecutive_risk_blocks_per_symbol": 3,
            "kill_cooldown_loops": 5,
            "max_abs_correlation": 1.0,
        },
        "strategy": {
            "name": "sma_200_trend",
            "trade_enabled": True,
            "sma_period": 200,
            "atr_period": 20,
            "atr_stop_multiplier": 2.0,
            "capital_at_risk_per_trade_pct": 0.50,
            "max_position_notional_pct": 10.0,
            "daily_loss_halt_pct": 1.50,
            "max_drawdown_pct": 12.0,
            "regime_trending_floor": 0.80,
            "regime_chop_ceiling": 0.60,
            "regime_high_vol_ceiling": 2.50,
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
