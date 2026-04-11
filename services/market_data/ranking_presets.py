from __future__ import annotations

from typing import Any

RANKING_PRESETS: dict[str, dict[str, Any]] = {
    "balanced": {
        "momentum_mult": 2.0,
        "volume_z_mult": 4.0,
        "hot_mult": 0.5,
        "correlation_penalty_threshold": 0.85,
    },
    "trend_heavy": {
        "momentum_mult": 3.0,
        "volume_z_mult": 5.0,
        "hot_mult": 0.75,
        "correlation_penalty_threshold": 0.80,
    },
    "mean_reversion_bias": {
        "momentum_mult": 1.0,
        "volume_z_mult": 3.0,
        "hot_mult": 0.25,
        "rsi_bonus_healthy": 7.0,
        "rsi_penalty_overbought": -10.0,
        "correlation_penalty_threshold": 0.90,
    },
}

def get_ranking_preset(name: str) -> dict[str, Any]:
    key = str(name or "balanced").strip()
    return dict(RANKING_PRESETS.get(key, RANKING_PRESETS["balanced"]))

def merge_ranking_config(preset_name: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = get_ranking_preset(preset_name)
    for k, v in dict(overrides or {}).items():
        if v is not None:
            cfg[k] = v
    return cfg
