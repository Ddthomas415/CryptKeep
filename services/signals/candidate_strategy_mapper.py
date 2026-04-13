"""
services/signals/candidate_strategy_mapper.py

Maps a scored candidate to its preferred strategy.

Mapping logic is intentionally conservative and signal-driven:
  - Use evidence from signal scores, not just trade_type labels
  - Prefer strategies with the narrowest scope for the detected setup
  - Document the reason for auditability

Calibration notes (update as attribution data accumulates):
  - pullback_recovery: best when pullback_recovery_score >= 70 AND trend_quality_score >= 50
  - mean_reversion_rsi: best for ranging + moderate RSI extremes (consolidation_score >= 50)
  - momentum: best when momentum_score >= 60 AND trend_quality >= 60 AND volume confirms
  - breakout_donchian: use when consolidation_score >= 65 AND vol_regime is favourable
"""
from __future__ import annotations

from typing import Any


def _safe(v: Any, d: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return d


def map_candidate_to_strategy(candidate: dict[str, Any]) -> dict[str, Any]:
    """Map a candidate to its preferred strategy based on its full score profile.

    Returns:
        {"preferred_strategy": str | None, "reason": str, "confidence": str}
    """
    trade_type = str(candidate.get("trade_type") or "pass")
    scores = dict(candidate.get("scores") or {})

    if trade_type == "pass":
        return {
            "preferred_strategy": None,
            "reason": "no_trade_type",
            "confidence": "none",
        }

    pullback     = _safe(scores.get("pullback_recovery_score"))
    momentum     = _safe(scores.get("momentum_score"))
    rel          = _safe(scores.get("relative_strength_score"))
    volume       = _safe(scores.get("volume_surge_score"))
    consolidate  = _safe(scores.get("consolidation_score"))
    trend_q      = _safe(scores.get("trend_quality_score"), 50.0)
    vol_regime   = _safe(scores.get("volatility_regime_score"), 50.0)
    illiq        = _safe(scores.get("illiquidity_risk_score_v2")
                         or scores.get("illiquidity_risk_score"), 50.0)

    # Hard block on high illiquidity regardless of trade type
    if illiq >= 75.0:
        return {
            "preferred_strategy": None,
            "reason": f"illiquidity_too_high:{illiq:.0f}",
            "confidence": "none",
        }

    # -----------------------------------------------------------------------
    # Swing trade mapping — rank order: pullback_recovery > mean_reversion > breakout
    # -----------------------------------------------------------------------
    if trade_type == "swing_trade":
        # Strong pullback profile + clean trend = pullback_recovery
        if pullback >= 70.0 and trend_q >= 50.0:
            confidence = "high" if pullback >= 80.0 and trend_q >= 60.0 else "medium"
            return {
                "preferred_strategy": "pullback_recovery",
                "reason": f"swing:pullback={pullback:.0f}:trend_q={trend_q:.0f}",
                "confidence": confidence,
            }

        # Tight consolidation = breakout_donchian setup
        if consolidate >= 60.0 and vol_regime >= 50.0:
            return {
                "preferred_strategy": "breakout_donchian",
                "reason": f"swing:consolidation={consolidate:.0f}:vol_regime={vol_regime:.0f}",
                "confidence": "medium",
            }

        # Default swing: mean_reversion_rsi
        return {
            "preferred_strategy": "mean_reversion_rsi",
            "reason": f"swing:default:pullback={pullback:.0f}",
            "confidence": "low",
        }

    # -----------------------------------------------------------------------
    # Quick flip mapping — momentum is primary, volume required
    # -----------------------------------------------------------------------
    if trade_type == "quick_flip":
        # Strong momentum + high relative strength + volume surge = momentum strategy
        if momentum >= 60.0 and rel >= 65.0 and volume >= 25.0 and trend_q >= 55.0:
            confidence = "high" if momentum >= 70.0 and rel >= 75.0 else "medium"
            return {
                "preferred_strategy": "momentum",
                "reason": f"quick_flip:mom={momentum:.0f}:rel={rel:.0f}:vol={volume:.0f}",
                "confidence": confidence,
            }

        # Moderate momentum but consolidation breakout potential
        if consolidate >= 55.0 and volume >= 20.0:
            return {
                "preferred_strategy": "breakout_donchian",
                "reason": f"quick_flip:breakout:consolidate={consolidate:.0f}",
                "confidence": "medium",
            }

        # Weak signal — default momentum but flag as low confidence
        return {
            "preferred_strategy": "momentum",
            "reason": f"quick_flip:default:mom={momentum:.0f}",
            "confidence": "low",
        }

    return {
        "preferred_strategy": None,
        "reason": f"unmapped_trade_type:{trade_type}",
        "confidence": "none",
    }
