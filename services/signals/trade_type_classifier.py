"""
services/signals/trade_type_classifier.py

Classifies a scored candidate into an actionable trade type.

Types:
  swing_trade  — multi-bar hold, pullback or range play
  quick_flip   — short-duration momentum continuation
  pass         — conditions not met for any actionable type

Classification uses hard gates first (illiquidity, volatility spike),
then positive signal combinations. Low-confidence combinations default to pass.
"""
from __future__ import annotations

from typing import Any


def _safe(v: Any, d: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return d


def classify_trade_type(*, scores: dict[str, float]) -> dict[str, Any]:
    """Return trade type and reason given a score dict.

    Returns:
        {"trade_type": str, "reason": str}
    """
    momentum  = _safe(scores.get("momentum_score"))
    rel       = _safe(scores.get("relative_strength_score"))
    volume    = _safe(scores.get("volume_surge_score"))
    pullback  = _safe(scores.get("pullback_recovery_score"))
    trend_q   = _safe(scores.get("trend_quality_score"), 50.0)
    vol_regime = _safe(scores.get("volatility_regime_score"), 50.0)
    consolidate = _safe(scores.get("consolidation_score"), 0.0)

    # Use best available illiquidity score
    illiq_v2 = scores.get("illiquidity_risk_score_v2")
    illiq = _safe(illiq_v2) if illiq_v2 is not None else _safe(scores.get("illiquidity_risk_score"))

    # ---- Hard gates (pass regardless of other signals) --------------------
    if illiq >= 75.0:
        return {"trade_type": "pass", "reason": "illiquidity_too_high"}

    if vol_regime < 20.0:
        return {"trade_type": "pass", "reason": "volatility_regime_unfavourable"}

    # ---- Swing trade: pullback + trend coherence -------------------------
    # Classic pullback profile
    if pullback >= 65.0 and rel >= 45.0 and momentum >= 35.0:
        return {"trade_type": "swing_trade", "reason": "pullback_recovery_profile"}

    # Consolidation breakout swing
    if consolidate >= 60.0 and vol_regime >= 55.0 and volume >= 15.0:
        return {"trade_type": "swing_trade", "reason": "consolidation_breakout_profile"}

    # ---- Quick flip: momentum continuation with volume -------------------
    if momentum >= 55.0 and rel >= 65.0 and volume >= 20.0 and trend_q >= 50.0:
        return {"trade_type": "quick_flip", "reason": "momentum_continuation_profile"}

    # Strong momentum alone — less confident
    if momentum >= 65.0 and rel >= 55.0 and volume >= 15.0:
        return {"trade_type": "quick_flip", "reason": "momentum_single_factor"}

    return {"trade_type": "pass", "reason": "no_clear_trade_type"}
