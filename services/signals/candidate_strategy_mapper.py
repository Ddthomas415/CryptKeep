from __future__ import annotations

from typing import Any


def map_candidate_to_strategy(candidate: dict[str, Any]) -> dict[str, Any]:
    trade_type = str(candidate.get("trade_type") or "pass")
    scores = dict(candidate.get("scores") or {})

    pullback = float(scores.get("pullback_recovery_score") or 0.0)
    momentum = float(scores.get("momentum_score") or 0.0)
    rel = float(scores.get("relative_strength_score") or 0.0)
    volume = float(scores.get("volume_surge_score") or 0.0)

    if trade_type == "pass":
        return {
            "preferred_strategy": None,
            "reason": "no_trade_type",
        }

    if trade_type == "swing_trade":
        if pullback >= 75.0:
            return {
                "preferred_strategy": "pullback_recovery",
                "reason": "swing_trade_pullback_profile",
            }
        return {
            "preferred_strategy": "mean_reversion_rsi",
            "reason": "swing_trade_mean_reversion_profile",
        }

    if trade_type == "quick_flip":
        if momentum >= 55.0 and rel >= 70.0 and volume >= 20.0:
            return {
                "preferred_strategy": "momentum",
                "reason": "quick_flip_momentum_profile",
            }
        return {
            "preferred_strategy": "momentum",
            "reason": "quick_flip_default",
        }

    return {
        "preferred_strategy": None,
        "reason": "unmapped_trade_type",
    }
