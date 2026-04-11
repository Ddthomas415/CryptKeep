from __future__ import annotations

from typing import Any

from dashboard.services.view_data import _load_local_ohlcv
from services.market_data.composite_ranker import build_ranker_config


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _closes(rows: list[list[Any]]) -> list[float]:
    return [_safe_float(r[4], 0.0) for r in rows if isinstance(r, (list, tuple)) and len(r) >= 5]


def _window_return_pct(closes: list[float], entry_idx: int, forward_bars: int) -> float:
    if entry_idx < 0 or entry_idx + forward_bars >= len(closes):
        return 0.0
    entry = _safe_float(closes[entry_idx], 0.0)
    exit_ = _safe_float(closes[entry_idx + forward_bars], 0.0)
    if entry <= 0 or exit_ <= 0:
        return 0.0
    return ((exit_ - entry) / entry) * 100.0


def _score_from_history(
    *,
    closes: list[float],
    anchor_idx: int,
    ranking_config: dict[str, Any],
) -> float:
    cfg = build_ranker_config({"ranking": dict(ranking_config or {})})

    if anchor_idx < 24:
        return -999.0

    now = closes[anchor_idx]
    prev_1 = closes[anchor_idx - 1]
    prev_4 = closes[anchor_idx - 4]
    prev_24 = closes[anchor_idx - 24]

    if min(now, prev_1, prev_4, prev_24) <= 0:
        return -999.0

    ret_1 = ((now - prev_1) / prev_1) * 100.0
    ret_4 = ((now - prev_4) / prev_4) * 100.0
    ret_24 = ((now - prev_24) / prev_24) * 100.0

    momentum_score = max(cfg["momentum_min"], min(cfg["momentum_max"], ret_4 * cfg["momentum_mult"]))
    hot_score = max(cfg["hot_min"], min(cfg["hot_max"], ret_24 * cfg["hot_mult"]))
    volume_score = 0.0  # no historical volume features in this first pass

    return round(momentum_score + hot_score + volume_score, 4)


def backtest_historical_selector(
    *,
    venue: str = "coinbase",
    symbols: list[str] | None = None,
    timeframe: str = "1h",
    top_n: int = 5,
    lookback_limit: int = 300,
    anchor_stride: int = 12,
    min_history_bars: int = 48,
    forward_bars: int = 4,
    ranking_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target = symbols or ["BTC/USD", "ETH/USD", "SOL/USD", "AVAX/USD", "LINK/USD", "DOGE/USD"]
    series: dict[str, list[float]] = {}

    for sym in target:
        rows = _load_local_ohlcv(venue, sym, timeframe=timeframe, limit=lookback_limit) or []
        closes = _closes(rows)
        if len(closes) >= (min_history_bars + forward_bars + 1):
            series[sym] = closes

    if not series:
        return {"ok": False, "reason": "no_series"}

    max_len = min(len(v) for v in series.values())
    start_idx = min_history_bars
    end_idx = max_len - forward_bars - 1

    baseline_anchor_returns: list[float] = []
    composite_anchor_returns: list[float] = []
    anchors: list[dict[str, Any]] = []

    for anchor_idx in range(start_idx, end_idx + 1, anchor_stride):
        baseline_ranked = []
        composite_ranked = []

        for sym, closes in series.items():
            r24 = _window_return_pct(closes, anchor_idx - 24, 24) if anchor_idx >= 24 else -999.0
            baseline_ranked.append({"symbol": sym, "score": r24})

            comp = _score_from_history(
                closes=closes,
                anchor_idx=anchor_idx,
                ranking_config=ranking_config or {},
            )
            composite_ranked.append({"symbol": sym, "score": comp})

        baseline_ranked.sort(key=lambda r: r["score"], reverse=True)
        composite_ranked.sort(key=lambda r: r["score"], reverse=True)

        baseline_selected = baseline_ranked[:top_n]
        composite_selected = composite_ranked[:top_n]

        baseline_returns = [
            _window_return_pct(series[row["symbol"]], anchor_idx, forward_bars)
            for row in baseline_selected
        ]
        composite_returns = [
            _window_return_pct(series[row["symbol"]], anchor_idx, forward_bars)
            for row in composite_selected
        ]

        baseline_avg = sum(baseline_returns) / len(baseline_returns) if baseline_returns else 0.0
        composite_avg = sum(composite_returns) / len(composite_returns) if composite_returns else 0.0

        baseline_anchor_returns.append(baseline_avg)
        composite_anchor_returns.append(composite_avg)

        anchors.append({
            "anchor_idx": anchor_idx,
            "baseline_symbols": [r["symbol"] for r in baseline_selected],
            "composite_symbols": [r["symbol"] for r in composite_selected],
            "baseline_avg_return_pct": round(baseline_avg, 4),
            "composite_avg_return_pct": round(composite_avg, 4),
            "delta_avg_return_pct": round(composite_avg - baseline_avg, 4),
        })

    def _summary(vals: list[float]) -> dict[str, Any]:
        if not vals:
            return {"count": 0, "avg_return_pct": 0.0, "hit_rate": 0.0, "total_return_pct": 0.0}
        hits = sum(1 for v in vals if v > 0)
        return {
            "count": len(vals),
            "avg_return_pct": round(sum(vals) / len(vals), 4),
            "hit_rate": round(hits / len(vals), 4),
            "total_return_pct": round(sum(vals), 4),
        }

    baseline_summary = _summary(baseline_anchor_returns)
    composite_summary = _summary(composite_anchor_returns)

    return {
        "ok": True,
        "venue": venue,
        "timeframe": timeframe,
        "forward_bars": forward_bars,
        "top_n": top_n,
        "anchors_tested": len(anchors),
        "baseline": baseline_summary,
        "composite": composite_summary,
        "delta": {
            "avg_return_pct": round(
                _safe_float(composite_summary.get("avg_return_pct")) - _safe_float(baseline_summary.get("avg_return_pct")),
                4,
            ),
            "hit_rate": round(
                _safe_float(composite_summary.get("hit_rate")) - _safe_float(baseline_summary.get("hit_rate")),
                4,
            ),
            "total_return_pct": round(
                _safe_float(composite_summary.get("total_return_pct")) - _safe_float(baseline_summary.get("total_return_pct")),
                4,
            ),
        },
        "anchors": anchors,
    }
