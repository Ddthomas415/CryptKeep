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


def load_outcomes(limit: int = 1000) -> list[dict[str, Any]]:
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
            except Exception:
                continue
    return rows[-limit:]


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

    return {
        "count": len(rows),
        "by_strategy": strategy_rows,
        "by_regime": regime_rows,
        "by_strategy_regime": pair_rows,
    }
