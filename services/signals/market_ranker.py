from __future__ import annotations

from typing import Any

from services.signals.signal_library import compute_signal_scores, _clamp


def _safe(v: Any, d: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return d


def composite_score(scores: dict[str, float]) -> float:
    """Weighted composite of all available signal scores.

    Weights (must sum to 1.0):
      momentum            0.22  — price momentum is the primary driver
      relative_strength   0.18  — cross-universe ranking context
      volume_surge        0.10  — confirmation signal
      pullback_recovery   0.15  — swing/recovery setup quality
      liquidity_safety    0.10  — inverse of best available illiq score
      volatility_regime   0.10  — are conditions right for entry?
      trend_quality       0.08  — directional clarity
      consolidation       0.07  — breakout readiness
    """
    momentum = _safe(scores.get("momentum_score"))
    rel      = _safe(scores.get("relative_strength_score"))
    volume   = _safe(scores.get("volume_surge_score"))
    pullback = _safe(scores.get("pullback_recovery_score"))
    # Use v2 illiquidity if available, fall back to v1
    illiq_v2  = scores.get("illiquidity_risk_score_v2")
    illiq_v1  = _safe(scores.get("illiquidity_risk_score"))
    illiq_risk = _safe(illiq_v2) if illiq_v2 is not None else illiq_v1
    vol_regime = _safe(scores.get("volatility_regime_score"), 50.0)
    trend_q    = _safe(scores.get("trend_quality_score"), 50.0)
    consolidate = _safe(scores.get("consolidation_score"), 0.0)

    raw = (
        momentum    * 0.22
        + rel       * 0.18
        + volume    * 0.10
        + pullback  * 0.15
        + (100.0 - illiq_risk) * 0.10
        + vol_regime  * 0.10
        + trend_q     * 0.08
        + consolidate * 0.07
    )
    return round(_clamp(raw), 4)


def rank_market(
    *,
    symbols_data: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    returns = [_safe(item.get("symbol_return_pct")) for item in symbols_data]

    ranked = []
    for item in symbols_data:
        ohlcv = list(item.get("ohlcv") or [])
        symbol_return_pct = _safe(item.get("symbol_return_pct"))

        scores = compute_signal_scores(
            ohlcv=ohlcv,
            symbol_return_pct=symbol_return_pct,
            all_returns_pct=returns,
        )
        total = composite_score(scores)

        ranked.append({
            "symbol": item.get("symbol"),
            "composite_score": total,
            "scores": scores,
            "symbol_return_pct": round(symbol_return_pct, 4),
        })

    ranked.sort(key=lambda x: x["composite_score"], reverse=True)
    return ranked
