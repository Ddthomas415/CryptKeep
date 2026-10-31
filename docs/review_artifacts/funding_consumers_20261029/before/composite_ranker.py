
from __future__ import annotations

from typing import Any


DEFAULT_WEIGHTS = {
    "momentum_mult": 2.0,
    "hot_mult": 0.5,
    "volume_z_mult": 4.0,
    "regime_bonus_trending": 8.0,
    "regime_bonus_neutral": 2.0,
    "regime_penalty_bearish": -5.0,
    "funding_bonus_shorts": 8.0,
    "funding_penalty_longs": -8.0,
    "funding_penalty_elevated_longs": -3.0,
    "oi_bonus_trend_confirm": 8.0,
    "oi_penalty_trend_diverge": -8.0,
    "oi_penalty_unwind": -2.0,
    "order_book_mult": 40.0,
    "rsi_bonus_healthy": 5.0,
    "rsi_penalty_overbought": -8.0,
    "rsi_penalty_oversold": -2.0,
    "volatility_penalty_high": -4.0,
    "volatility_bonus_mid": 3.0,
    "correlation_penalty_value": 8.0,
    "correlation_penalty_threshold": 0.85,
}

DEFAULT_LIMITS = {
    "momentum_min": -20.0,
    "momentum_max": 25.0,
    "hot_min": 0.0,
    "hot_max": 25.0,
    "volume_min": 0.0,
    "volume_max": 20.0,
    "order_book_min": -10.0,
    "order_book_max": 10.0,
}


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def build_ranker_config(cfg: dict[str, Any] | None = None) -> dict[str, float]:
    base = {**DEFAULT_WEIGHTS, **DEFAULT_LIMITS}
    cfg = dict(cfg or {})
    rcfg = dict(cfg.get("ranking") or {})
    for k in list(base.keys()):
        if k in rcfg:
            base[k] = _safe_float(rcfg.get(k), base[k])
    return base


def score_row(
    *,
    row: dict[str, Any],
    funding_row: dict[str, Any] | None = None,
    oi_row: dict[str, Any] | None = None,
    order_book_row: dict[str, Any] | None = None,
    regime: str | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = build_ranker_config({"ranking": dict(config or {})})

    change_pct = _safe_float(row.get("change_pct"), 0.0)
    hot_score = _safe_float(row.get("hot_score"), 0.0)
    volume_z = _safe_float(row.get("volume_z"), 0.0)
    volatility_pct = _safe_float(row.get("volatility_pct"), 0.0)
    rsi = _safe_float(row.get("rsi"), 50.0)

    funding_rate = _safe_float((funding_row or {}).get("rate_pct"), 0.0)
    oi_change_pct = _safe_float((oi_row or {}).get("oi_change_pct"), 0.0)
    price_change_pct = _safe_float((oi_row or {}).get("price_change_pct"), change_pct)
    imbalance = _safe_float((order_book_row or {}).get("imbalance"), 0.0)

    score_momentum = _clamp(
        change_pct * cfg["momentum_mult"],
        cfg["momentum_min"],
        cfg["momentum_max"],
    )
    score_hot = _clamp(
        hot_score * cfg["hot_mult"],
        cfg["hot_min"],
        cfg["hot_max"],
    )
    score_volume = _clamp(
        volume_z * cfg["volume_z_mult"],
        cfg["volume_min"],
        cfg["volume_max"],
    )

    score_regime = 0.0
    rg = str(regime or row.get("regime") or "unknown")
    if rg in {"trending_up", "greed"}:
        score_regime = cfg["regime_bonus_trending"]
    elif rg in {"ranging", "neutral"}:
        score_regime = cfg["regime_bonus_neutral"]
    elif rg in {"trending_down", "extreme_greed"}:
        score_regime = cfg["regime_penalty_bearish"]

    score_funding = 0.0
    if funding_rate <= -0.01:
        score_funding = cfg["funding_bonus_shorts"]
    elif funding_rate >= 0.05:
        score_funding = cfg["funding_penalty_longs"]
    elif funding_rate >= 0.02:
        score_funding = cfg["funding_penalty_elevated_longs"]

    score_oi = 0.0
    if oi_change_pct >= 5.0 and price_change_pct > 0:
        score_oi = cfg["oi_bonus_trend_confirm"]
    elif oi_change_pct >= 5.0 and price_change_pct < 0:
        score_oi = cfg["oi_penalty_trend_diverge"]
    elif oi_change_pct <= -5.0:
        score_oi = cfg["oi_penalty_unwind"]

    score_order_book = _clamp(
        imbalance * cfg["order_book_mult"],
        cfg["order_book_min"],
        cfg["order_book_max"],
    )

    score_rsi = 0.0
    if 45.0 <= rsi <= 70.0:
        score_rsi = cfg["rsi_bonus_healthy"]
    elif rsi > 80.0:
        score_rsi = cfg["rsi_penalty_overbought"]
    elif rsi < 25.0:
        score_rsi = cfg["rsi_penalty_oversold"]

    score_volatility = 0.0
    if volatility_pct >= 10.0:
        score_volatility = cfg["volatility_penalty_high"]
    elif 2.0 <= volatility_pct <= 8.0:
        score_volatility = cfg["volatility_bonus_mid"]

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
