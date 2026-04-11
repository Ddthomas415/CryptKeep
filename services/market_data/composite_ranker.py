from __future__ import annotations

from typing import Any


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def score_row(
    *,
    row: dict[str, Any],
    funding_row: dict[str, Any] | None = None,
    oi_row: dict[str, Any] | None = None,
    order_book_row: dict[str, Any] | None = None,
    regime: str | None = None,
) -> dict[str, Any]:
    change_pct = _safe_float(row.get("change_pct"), 0.0)
    hot_score = _safe_float(row.get("hot_score"), 0.0)
    volume_z = _safe_float(row.get("volume_z"), 0.0)
    volatility_pct = _safe_float(row.get("volatility_pct"), 0.0)
    rsi = _safe_float(row.get("rsi"), 50.0)

    funding_rate = _safe_float((funding_row or {}).get("rate_pct"), 0.0)
    oi_change_pct = _safe_float((oi_row or {}).get("oi_change_pct"), 0.0)
    price_change_pct = _safe_float((oi_row or {}).get("price_change_pct"), change_pct)
    imbalance = _safe_float((order_book_row or {}).get("imbalance"), 0.0)

    score_momentum = _clamp(change_pct * 2.0, -20.0, 25.0)
    score_hot = _clamp(hot_score * 0.5, 0.0, 25.0)
    score_volume = _clamp(volume_z * 4.0, 0.0, 20.0)

    score_regime = 0.0
    rg = str(regime or row.get("regime") or "unknown")
    if rg in {"trending_up", "greed"}:
        score_regime = 8.0
    elif rg in {"ranging", "neutral"}:
        score_regime = 2.0
    elif rg in {"trending_down", "extreme_greed"}:
        score_regime = -5.0

    score_funding = 0.0
    if funding_rate <= -0.01:
        score_funding = 8.0
    elif funding_rate >= 0.05:
        score_funding = -8.0
    elif funding_rate >= 0.02:
        score_funding = -3.0

    score_oi = 0.0
    if oi_change_pct >= 5.0 and price_change_pct > 0:
        score_oi = 8.0
    elif oi_change_pct >= 5.0 and price_change_pct < 0:
        score_oi = -8.0
    elif oi_change_pct <= -5.0:
        score_oi = -2.0

    score_order_book = _clamp(imbalance * 40.0, -10.0, 10.0)

    score_rsi = 0.0
    if 45.0 <= rsi <= 70.0:
        score_rsi = 5.0
    elif rsi > 80.0:
        score_rsi = -8.0
    elif rsi < 25.0:
        score_rsi = -2.0

    score_volatility = 0.0
    if volatility_pct >= 10.0:
        score_volatility = -4.0
    elif 2.0 <= volatility_pct <= 8.0:
        score_volatility = 3.0

    total = (
        score_momentum
        + score_hot
        + score_volume
        + score_regime
        + score_funding
        + score_oi
        + score_order_book
        + score_rsi
        + score_volatility
    )

    breakdown = {
        "momentum": round(score_momentum, 4),
        "hot": round(score_hot, 4),
        "volume": round(score_volume, 4),
        "regime": round(score_regime, 4),
        "funding": round(score_funding, 4),
        "open_interest": round(score_oi, 4),
        "order_book": round(score_order_book, 4),
        "rsi": round(score_rsi, 4),
        "volatility": round(score_volatility, 4),
    }

    return {
        **row,
        "composite_score": round(total, 4),
        "score_breakdown": breakdown,
        "funding_rate_pct": funding_rate,
        "oi_change_pct": oi_change_pct,
        "order_book_imbalance": round(imbalance, 4),
    }


def apply_correlation_penalty(
    *,
    ranked_rows: list[dict[str, Any]],
    corr_matrix: dict[str, dict[str, float]] | None = None,
    penalty_threshold: float = 0.85,
    penalty_value: float = 8.0,
) -> list[dict[str, Any]]:
    rows = [dict(r) for r in list(ranked_rows or [])]
    corr_matrix = dict(corr_matrix or {})
    selected: list[str] = []

    for row in rows:
        sym = str(row.get("symbol") or "").strip()
        penalty = 0.0
        for chosen in selected:
            corr = abs(_safe_float((corr_matrix.get(sym) or {}).get(chosen), 0.0))
            if corr >= penalty_threshold:
                penalty = max(penalty, penalty_value)
        row["correlation_penalty"] = round(penalty, 4)
        row["composite_score_penalized"] = round(_safe_float(row.get("composite_score"), 0.0) - penalty, 4)
        selected.append(sym)

    rows.sort(key=lambda r: _safe_float(r.get("composite_score_penalized"), 0.0), reverse=True)
    return rows
