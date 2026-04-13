from __future__ import annotations

from typing import Any


def _safe(v: Any, d: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return d


def classify_trade_type(*, scores: dict[str, float]) -> dict[str, Any]:
    momentum = _safe(scores.get("momentum_score"))
    rel = _safe(scores.get("relative_strength_score"))
    volume = _safe(scores.get("volume_surge_score"))
    pullback = _safe(scores.get("pullback_recovery_score"))
    illiq_risk = _safe(scores.get("illiquidity_risk_score"))

    if illiq_risk >= 85.0:
        return {
            "trade_type": "pass",
            "reason": "illiquidity_too_high",
        }

    if pullback >= 70.0 and rel >= 50.0 and momentum >= 40.0:
        return {
            "trade_type": "swing_trade",
            "reason": "pullback_recovery_profile",
        }

    if momentum >= 55.0 and rel >= 70.0 and volume >= 20.0:
        return {
            "trade_type": "quick_flip",
            "reason": "momentum_continuation_profile",
        }

    return {
        "trade_type": "pass",
        "reason": "no_clear_trade_type",
    }
