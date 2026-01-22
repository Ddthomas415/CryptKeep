from __future__ import annotations

PRESETS = {
    "ema_crossover_fast": {
        "type": "ema_crossover",
        "params": {"fast": 8, "slow": 21},
        "filters": {"volatility": {"enabled": True, "period": 14, "min_atr_pct": 0.08, "max_atr_pct": 4.0},
                    "regime": {"enabled": True, "slow": 50, "slope_lookback": 6}},
    },
    "mean_reversion_strict": {
        "type": "mean_reversion",
        "params": {"lookback": 60, "entry_z": 2.2},
        "filters": {"volatility": {"enabled": True, "period": 14, "min_atr_pct": 0.06, "max_atr_pct": 6.0},
                    "regime": {"enabled": False}},
    },
    "breakout_trend": {
        "type": "breakout",
        "params": {"lookback": 20},
        "filters": {"volatility": {"enabled": True, "period": 14, "min_atr_pct": 0.10, "max_atr_pct": 8.0},
                    "regime": {"enabled": True, "slow": 50, "slope_lookback": 5}},
    },
}
