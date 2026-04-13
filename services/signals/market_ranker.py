from __future__ import annotations

from typing import Any

from services.signals.signal_library import compute_signal_scores, _clamp


def _safe(v: Any, d: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return d


def composite_score(scores: dict[str, float]) -> float:
    momentum = _safe(scores.get("momentum_score"))
    rel = _safe(scores.get("relative_strength_score"))
    volume = _safe(scores.get("volume_surge_score"))
    pullback = _safe(scores.get("pullback_recovery_score"))
    illiq_risk = _safe(scores.get("illiquidity_risk_score"))

    raw = (
        momentum * 0.30
        + rel * 0.25
        + volume * 0.15
        + pullback * 0.20
        + (100.0 - illiq_risk) * 0.10
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
