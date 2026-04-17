from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

STORE_FILE = Path(".cbp_state/runtime/outcomes/strategy_outcomes.jsonl")


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def load_outcomes(
    limit: int = 1000,
    *,
    require_selected_strategy: bool = False,
    require_regime: bool = False,
) -> list[dict[str, Any]]:
    if not STORE_FILE.exists():
        return []
    rows: list[dict[str, Any]] = []
    with STORE_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception as _err:
                continue
    rows = rows[-limit:]
    if require_selected_strategy:
        rows = [r for r in rows if r.get("selected_strategy")]
    if require_regime:
        rows = [r for r in rows if r.get("regime")]
    return rows


def _avg(vals: list[float]) -> float:
    return round(sum(vals) / len(vals), 4) if vals else 0.0


def summarize_outcomes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_strategy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_regime: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        strategy = str(row.get("selected_strategy") or row.get("intent_strategy_id") or "unknown").strip() or "unknown"
        regime = str(row.get("regime") or "unknown").strip() or "unknown"
        by_strategy[strategy].append(row)
        by_regime[regime].append(row)
        by_pair[(strategy, regime)].append(row)

    strategy_rows = []
    for strategy, items in by_strategy.items():
        strategy_rows.append({
            "selected_strategy": strategy,
            "count": len(items),
            "avg_fill_vs_plan_pct": _avg([_safe_float(x.get("fill_vs_plan_pct"), 0.0) for x in items]),
            "avg_delta_alloc_pct": _avg([_safe_float(x.get("delta_alloc_pct"), 0.0) for x in items]),
            "avg_new_exposure_pct": _avg([_safe_float(x.get("new_exposure_pct"), 0.0) for x in items]),
        })
    strategy_rows.sort(key=lambda r: (r["count"], r["avg_fill_vs_plan_pct"]), reverse=True)

    regime_rows = []
    for regime, items in by_regime.items():
        regime_rows.append({
            "regime": regime,
            "count": len(items),
            "avg_fill_vs_plan_pct": _avg([_safe_float(x.get("fill_vs_plan_pct"), 0.0) for x in items]),
            "avg_delta_alloc_pct": _avg([_safe_float(x.get("delta_alloc_pct"), 0.0) for x in items]),
        })
    regime_rows.sort(key=lambda r: (r["count"], r["avg_fill_vs_plan_pct"]), reverse=True)

    pair_rows = []
    for (strategy, regime), items in by_pair.items():
        pair_rows.append({
            "selected_strategy": strategy,
            "regime": regime,
            "count": len(items),
            "avg_fill_vs_plan_pct": _avg([_safe_float(x.get("fill_vs_plan_pct"), 0.0) for x in items]),
            "avg_delta_alloc_pct": _avg([_safe_float(x.get("delta_alloc_pct"), 0.0) for x in items]),
        })
    pair_rows.sort(key=lambda r: (r["count"], r["avg_fill_vs_plan_pct"]), reverse=True)

    by_reason: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        reason = str(row.get("selected_strategy_reason") or "unknown").strip() or "unknown"
        by_reason[reason].append(row)

    reason_rows = []
    for reason, items in by_reason.items():
        reason_rows.append({
            "selected_strategy_reason": reason,
            "count": len(items),
            "avg_fill_vs_plan_pct": _avg([_safe_float(x.get("fill_vs_plan_pct"), 0.0) for x in items]),
            "avg_delta_alloc_pct": _avg([_safe_float(x.get("delta_alloc_pct"), 0.0) for x in items]),
        })
    reason_rows.sort(key=lambda r: (r["count"], r["avg_fill_vs_plan_pct"]), reverse=True)

    return {
        "count": len(rows),
        "by_strategy": strategy_rows,
        "by_regime": regime_rows,
        "by_strategy_regime": pair_rows,
        "by_reason": reason_rows,
    }


def recent_strategy_regime_score(
    strategy: str,
    regime: str,
    *,
    limit: int = 200,
    min_count: int = 3,
) -> dict[str, Any]:
    rows = load_outcomes(limit=limit)
    strategy = str(strategy or "").strip()
    regime = str(regime or "").strip()

    matched = [
        r for r in rows
        if str(r.get("selected_strategy") or r.get("intent_strategy_id") or "").strip() == strategy
        and str(r.get("regime") or "").strip() == regime
    ]

    count = len(matched)
    if count < min_count:
        return {
            "count": count,
            "avg_fill_vs_plan_pct": 0.0,
            "avg_delta_alloc_pct": 0.0,
            "score": 0.0,
            "enough_data": False,
        }

    avg_fill = _avg([_safe_float(x.get("fill_vs_plan_pct"), 0.0) for x in matched])
    avg_delta = _avg([_safe_float(x.get("delta_alloc_pct"), 0.0) for x in matched])

    score = avg_fill
    if avg_delta > 0:
        score += min(avg_delta * 0.1, 1.5)

    if score > 3.0:
        score = 3.0
    elif score < -3.0:
        score = -3.0

    return {
        "count": count,
        "avg_fill_vs_plan_pct": avg_fill,
        "avg_delta_alloc_pct": avg_delta,
        "score": round(score, 4),
        "enough_data": True,
    }


def summarize_closed_trade_outcomes(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows = sorted(rows, key=lambda r: str(r.get("ts") or r.get("journal_ts") or ""))
    closed = []
    prev_realized = None

    for r in rows:
        try:
            pos_qty = float(r.get("pos_qty") or 0.0)
        except Exception:
            pos_qty = 0.0

        if abs(pos_qty) > 1e-12:
            try:
                prev_realized = float(r.get("realized_pnl_total")) if r.get("realized_pnl_total") is not None else prev_realized
            except Exception as _err:
                pass  # suppressed: outcome_summary.py
            continue

        try:
            realized = float(r.get("realized_pnl_total")) if r.get("realized_pnl_total") is not None else None
        except Exception:
            realized = None

        realized_delta = 0.0
        if realized is not None and prev_realized is not None:
            realized_delta = realized - prev_realized

        closed.append({
            "ts": r.get("ts") or r.get("journal_ts"),
            "symbol": r.get("symbol"),
            "selected_strategy": r.get("selected_strategy") or r.get("intent_strategy_id") or "unknown",
            "regime": r.get("regime") or "unknown",
            "side": r.get("side"),
            "signal_reason": r.get("signal_reason"),
            "realized_pnl_delta": round(realized_delta, 6),
            "realized_pnl_total": round(realized, 6) if realized is not None else None,
        })

        if realized is not None:
            prev_realized = realized

    by_strategy: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_pair: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for r in closed:
        strategy = str(r.get("selected_strategy") or "unknown")
        regime = str(r.get("regime") or "unknown")
        by_strategy[strategy].append(r)
        by_pair[(strategy, regime)].append(r)

    strategy_rows = []
    for strategy, items in by_strategy.items():
        strategy_rows.append({
            "selected_strategy": strategy,
            "count": len(items),
            "avg_realized_pnl_delta": _avg([_safe_float(x.get("realized_pnl_delta"), 0.0) for x in items]),
            "sum_realized_pnl_delta": round(sum(_safe_float(x.get("realized_pnl_delta"), 0.0) for x in items), 6),
        })
    strategy_rows.sort(key=lambda r: (r["sum_realized_pnl_delta"], r["count"]), reverse=True)

    pair_rows = []
    for (strategy, regime), items in by_pair.items():
        pair_rows.append({
            "selected_strategy": strategy,
            "regime": regime,
            "count": len(items),
            "avg_realized_pnl_delta": _avg([_safe_float(x.get("realized_pnl_delta"), 0.0) for x in items]),
            "sum_realized_pnl_delta": round(sum(_safe_float(x.get("realized_pnl_delta"), 0.0) for x in items), 6),
        })
    pair_rows.sort(key=lambda r: (r["sum_realized_pnl_delta"], r["count"]), reverse=True)

    return {
        "count": len(closed),
        "closed_rows": closed,
        "by_strategy": strategy_rows,
        "by_strategy_regime": pair_rows,
    }
