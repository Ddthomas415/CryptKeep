
from __future__ import annotations

from typing import Any

from services.market_data.rotation_engine import build_rotation_candidates
from services.backtest.forward_returns import compute_forward_return_pct_from_ohlcv


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _attach_forward_returns(
    *,
    rows: list[dict[str, Any]],
    venue: str,
    timeframe: str,
    forward_bars: int,
) -> list[dict[str, Any]]:
    out = []
    for row in list(rows or []):
        sym = str(row.get("symbol") or "").strip()
        if not sym:
            out.append(dict(row))
            continue
        fr = compute_forward_return_pct_from_ohlcv(
            venue=venue,
            symbol=sym,
            timeframe=timeframe,
            forward_bars=forward_bars,
        )
        out.append({
            **row,
            "forward_return_pct": _safe_float(fr.get("return_pct"), 0.0),
            "forward_return_ok": bool(fr.get("ok")),
            "forward_entry_price": fr.get("entry_price"),
            "forward_exit_price": fr.get("exit_price"),
            "forward_bars": forward_bars,
            "forward_timeframe": timeframe,
        })
    return out


def _future_return_pct(row: dict[str, Any]) -> float:
    return _safe_float(row.get("forward_return_pct"), 0.0)


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "count": 0,
            "avg_return_pct": 0.0,
            "hit_rate": 0.0,
            "total_return_pct": 0.0,
            "max_drawdown_proxy_pct": 0.0,
        }

    rets = [_future_return_pct(r) for r in rows]
    hits = [r for r in rets if r > 0]
    cum = 0.0
    peak = 0.0
    max_dd = 0.0
    for r in rets:
        cum += r
        peak = max(peak, cum)
        dd = peak - cum
        max_dd = max(max_dd, dd)

    return {
        "count": len(rows),
        "avg_return_pct": round(sum(rets) / len(rets), 4),
        "hit_rate": round(len(hits) / len(rets), 4),
        "total_return_pct": round(sum(rets), 4),
        "max_drawdown_proxy_pct": round(max_dd, 4),
    }


def _compare_window(
    *,
    venue: str,
    baseline_rows: list[dict[str, Any]],
    composite_rows: list[dict[str, Any]],
    timeframe: str,
    forward_bars: int,
) -> dict[str, Any]:
    composite_eval = _attach_forward_returns(
        rows=composite_rows,
        venue=venue,
        timeframe=timeframe,
        forward_bars=forward_bars,
    )
    baseline_eval = _attach_forward_returns(
        rows=baseline_rows,
        venue=venue,
        timeframe=timeframe,
        forward_bars=forward_bars,
    )

    composite_summary = _summarize(composite_eval)
    baseline_summary = _summarize(baseline_eval)

    return {
        "timeframe": timeframe,
        "forward_bars": forward_bars,
        "baseline_summary": baseline_summary,
        "composite_summary": composite_summary,
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
        "baseline_rows": baseline_eval,
        "composite_rows": composite_eval,
    }


def backtest_selector_comparison(
    *,
    venue: str = "coinbase",
    top_n: int = 10,
    max_abs_corr: float = 0.85,
    ranking_config: dict[str, Any] | None = None,
    timeframe: str = "1h",
    forward_bars: int = 1,
    multi_windows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    composite = build_rotation_candidates(
        venue=venue,
        top_n=top_n,
        diversify=True,
        max_abs_corr=max_abs_corr,
        ranking_config=ranking_config,
    )

    baseline = build_rotation_candidates(
        venue=venue,
        top_n=top_n,
        diversify=False,
        max_abs_corr=1.0,
        ranking_config={
            "momentum_mult": 0.0,
            "volume_z_mult": 0.0,
            "order_book_mult": 0.0,
            "funding_bonus_shorts": 0.0,
            "funding_penalty_longs": 0.0,
            "funding_penalty_elevated_longs": 0.0,
            "oi_bonus_trend_confirm": 0.0,
            "oi_penalty_trend_diverge": 0.0,
            "oi_penalty_unwind": 0.0,
            "rsi_bonus_healthy": 0.0,
            "rsi_penalty_overbought": 0.0,
            "rsi_penalty_oversold": 0.0,
            "volatility_penalty_high": 0.0,
            "volatility_bonus_mid": 0.0,
            "hot_mult": 1.0,
        },
    )

    composite_rows = list(composite.get("selected_rows") or [])
    baseline_rows = list(baseline.get("rows") or [])[:top_n]

    primary = _compare_window(
        venue=venue,
        baseline_rows=baseline_rows,
        composite_rows=composite_rows,
        timeframe=timeframe,
        forward_bars=forward_bars,
    )

    windows = list(multi_windows or [
        {"timeframe": "1h", "forward_bars": 1},
        {"timeframe": "1h", "forward_bars": 4},
        {"timeframe": "1h", "forward_bars": 24},
    ])

    multi_window = [
        _compare_window(
            venue=venue,
            baseline_rows=baseline_rows,
            composite_rows=composite_rows,
            timeframe=str(w.get("timeframe") or "1h"),
            forward_bars=int(w.get("forward_bars") or 1),
        )
        for w in windows
    ]

    return {
        "ok": True,
        "venue": venue,
        "top_n": top_n,
        "timeframe": timeframe,
        "forward_bars": forward_bars,
        "baseline": {
            "name": "hot_score_baseline",
            "symbols": [str(r.get("symbol") or "") for r in baseline_rows],
            "summary": primary["baseline_summary"],
            "rows": primary["baseline_rows"],
        },
        "composite": {
            "name": "composite_ranker",
            "symbols": [str(r.get("symbol") or "") for r in composite_rows],
            "summary": primary["composite_summary"],
            "rows": primary["composite_rows"],
        },
        "delta": primary["delta"],
        "multi_window": multi_window,
    }
