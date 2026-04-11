from __future__ import annotations

from typing import Any

from services.market_data.correlation_matrix import diversify_ranked_symbols


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def build_allocation_limits(cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = dict(cfg or {})
    rcfg = dict(cfg.get("risk") or {})
    return {
        "target_total_deployment_pct": _safe_float(rcfg.get("target_total_deployment_pct", 60.0), 60.0),
        "max_symbol_allocation_pct": _safe_float(rcfg.get("max_symbol_allocation_pct", 20.0), 20.0),
        "min_symbol_allocation_pct": _safe_float(rcfg.get("min_symbol_allocation_pct", 5.0), 5.0),
        "max_abs_correlation": _safe_float(rcfg.get("max_abs_correlation", 0.85), 0.85),
    }


def _allocate_rows(
    *,
    rows: list[dict[str, Any]],
    total_budget: float,
    max_alloc: float,
    min_alloc: float,
) -> dict[str, Any]:
    if not rows:
        return {"ok": True, "rows": [], "total_allocated_pct": 0.0}

    scores = [max(_safe_float(r.get("hot_score"), 0.0), 0.0) for r in rows]
    score_sum = sum(scores)

    out: list[dict[str, Any]] = []
    allocated = 0.0

    for row, score in zip(rows, scores):
        raw = (score / score_sum * total_budget) if score_sum > 0 else (total_budget / max(len(rows), 1))
        alloc = max(min_alloc, min(max_alloc, raw))
        allocated += alloc
        out.append({
            **row,
            "target_alloc_pct": round(alloc, 4),
        })

    if allocated > total_budget and allocated > 0:
        scale = total_budget / allocated
        allocated = 0.0
        for row in out:
            row["target_alloc_pct"] = round(_safe_float(row.get("target_alloc_pct"), 0.0) * scale, 4)
            allocated += _safe_float(row.get("target_alloc_pct"), 0.0)

    return {
        "ok": True,
        "rows": out,
        "total_allocated_pct": round(allocated, 4),
    }


def allocate_budget(
    *,
    ranked_rows: list[dict[str, Any]],
    limits: dict[str, Any],
    top_n: int = 10,
    correlation_matrix: dict[str, dict[str, float]] | None = None,
) -> dict[str, Any]:
    rows = list(ranked_rows or [])[:top_n]
    if not rows:
        return {"ok": True, "rows": [], "total_allocated_pct": 0.0, "diversified": False}

    total_budget = _safe_float(limits.get("target_total_deployment_pct", 60.0), 60.0)
    max_alloc = _safe_float(limits.get("max_symbol_allocation_pct", 20.0), 20.0)
    min_alloc = _safe_float(limits.get("min_symbol_allocation_pct", 5.0), 5.0)
    max_abs_corr = _safe_float(limits.get("max_abs_correlation", 0.85), 0.85)

    diversified = False
    selected_symbols = [str(r.get("symbol") or "").strip() for r in rows if str(r.get("symbol") or "").strip()]

    if correlation_matrix:
        diversified_symbols = diversify_ranked_symbols(
            ranked_symbols=selected_symbols,
            matrix=correlation_matrix,
            max_abs_corr=max_abs_corr,
            top_n=top_n,
        )
        if diversified_symbols and diversified_symbols != selected_symbols:
            diversified = True
        rows = [r for r in rows if str(r.get("symbol") or "").strip() in set(diversified_symbols)]

    alloc = _allocate_rows(
        rows=rows,
        total_budget=total_budget,
        max_alloc=max_alloc,
        min_alloc=min_alloc,
    )
    alloc["diversified"] = diversified
    alloc["selected_symbols"] = [str(r.get("symbol") or "").strip() for r in alloc.get("rows", [])]
    return alloc
