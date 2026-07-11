from __future__ import annotations

import copy
import itertools
from typing import Any

from services.backtest.walk_forward import run_archive_backed_walk_forward


ARTIFACT_TYPE = "archive_backed_parameter_sweep_v1"
DEFAULT_MAX_VARIANTS = 50


def _path_set(cfg: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    parts = [part.strip() for part in str(path or "").split(".") if part.strip()]
    if not parts:
        raise ValueError("grid path must not be empty")
    out = copy.deepcopy(dict(cfg or {}))
    cur: dict[str, Any] = out
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = copy.deepcopy(value)
    return out


def expand_parameter_grid(
    *,
    base_cfg: dict[str, Any],
    grid: dict[str, list[Any]],
    max_variants: int = DEFAULT_MAX_VARIANTS,
) -> list[dict[str, Any]]:
    items = [(str(path), list(values or [])) for path, values in sorted(dict(grid or {}).items())]
    for path, values in items:
        if not path.strip():
            raise ValueError("grid path must not be empty")
        if not values:
            raise ValueError(f"grid path has no values: {path}")
    if not items:
        return [{"variant_id": "variant_001", "parameters": {}, "config": copy.deepcopy(dict(base_cfg or {}))}]

    total = 1
    for _path, values in items:
        total *= len(values)
    if total > int(max_variants):
        raise ValueError(f"grid expands to {total} variants, above max_variants={int(max_variants)}")

    variants: list[dict[str, Any]] = []
    paths = [path for path, _values in items]
    for idx, values in enumerate(itertools.product(*(values for _path, values in items)), start=1):
        cfg = copy.deepcopy(dict(base_cfg or {}))
        params: dict[str, Any] = {}
        for path, value in zip(paths, values):
            cfg = _path_set(cfg, path, value)
            params[path] = copy.deepcopy(value)
        variants.append(
            {
                "variant_id": f"variant_{idx:03d}",
                "parameters": params,
                "config": cfg,
            }
        )
    return variants


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _variant_score(result: dict[str, Any]) -> dict[str, Any]:
    summary = dict(result.get("summary") or {})
    avg_return = _fnum(summary.get("avg_test_return_pct"), 0.0)
    max_dd = _fnum(summary.get("avg_test_max_drawdown_pct"), 0.0)
    non_negative = _fnum(summary.get("non_negative_test_window_ratio"), 0.0)
    closed = int(_fnum(summary.get("total_test_closed_trades"), 0.0))
    window_count = int(_fnum(summary.get("window_count"), 0.0))
    research_score = float(avg_return - max_dd)
    return {
        "research_score": research_score,
        "avg_test_return_pct": float(avg_return),
        "avg_test_max_drawdown_pct": float(max_dd),
        "non_negative_test_window_ratio": float(non_negative),
        "total_test_closed_trades": int(closed),
        "window_count": int(window_count),
    }


def _sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    score = dict(row.get("score") or {})
    return (
        not bool(row.get("ok")),
        -int(score.get("total_test_closed_trades") or 0),
        -float(score.get("non_negative_test_window_ratio") or 0.0),
        -float(score.get("avg_test_return_pct") or 0.0),
        float(score.get("avg_test_max_drawdown_pct") or 0.0),
        str(row.get("config_hash") or ""),
    )


def _dataset_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hashes = sorted({str(row.get("dataset_hash") or "") for row in rows if str(row.get("dataset_hash") or "")})
    sources = sorted({str(((row.get("dataset") or {}).get("source")) or "") for row in rows if str(((row.get("dataset") or {}).get("source")) or "")})
    return {
        "dataset_hashes": hashes,
        "source_count": int(len(sources)),
        "sources": sources,
        "unique_dataset_count": int(len(hashes)),
    }


def run_archive_parameter_sweep(
    *,
    base_cfg: dict[str, Any],
    grid: dict[str, list[Any]],
    venue: str,
    symbol: str,
    timeframe: str = "1h",
    limit: int = 500,
    since_ms: int | None = None,
    db_path: str | None = None,
    warmup_bars: int = 50,
    min_train_bars: int = 120,
    test_bars: int = 30,
    step_bars: int | None = None,
    max_windows: int = 0,
    initial_cash: float = 10_000.0,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
    max_variants: int = DEFAULT_MAX_VARIANTS,
) -> dict[str, Any]:
    """
    Research-only archive-backed parameter sweep.

    Ranking is descriptive and deterministic; it is not a promotion decision.
    """
    try:
        variants = expand_parameter_grid(base_cfg=base_cfg, grid=grid, max_variants=max_variants)
    except ValueError as exc:
        return {
            "ok": False,
            "reason": "invalid_grid",
            "detail": str(exc),
            "research_only": True,
            "artifact_type": ARTIFACT_TYPE,
            "variant_count": 0,
            "ranked_variants": [],
            "top_variant": None,
        }

    ranked: list[dict[str, Any]] = []
    for variant in variants:
        result = run_archive_backed_walk_forward(
            cfg=dict(variant.get("config") or {}),
            venue=str(venue),
            symbol=str(symbol),
            timeframe=str(timeframe),
            limit=int(limit),
            since_ms=since_ms,
            db_path=db_path,
            warmup_bars=int(warmup_bars),
            min_train_bars=int(min_train_bars),
            test_bars=int(test_bars),
            step_bars=step_bars,
            max_windows=int(max_windows),
            initial_cash=float(initial_cash),
            fee_bps=float(fee_bps),
            slippage_bps=float(slippage_bps),
        )
        ranked.append(
            {
                "variant_id": str(variant.get("variant_id") or ""),
                "parameters": dict(variant.get("parameters") or {}),
                "ok": bool(result.get("ok")),
                "reason": str(result.get("reason") or ""),
                "strategy": str(result.get("strategy") or ""),
                "config_hash": str(result.get("config_hash") or ""),
                "dataset_hash": str(result.get("dataset_hash") or ""),
                "dataset": dict(result.get("dataset") or {}),
                "window_count": int(result.get("window_count") or 0),
                "summary": dict(result.get("summary") or {}),
                "score": _variant_score(result),
            }
        )

    ranked.sort(key=_sort_key)
    for idx, row in enumerate(ranked, start=1):
        row["rank"] = int(idx)

    successful = [row for row in ranked if bool(row.get("ok"))]
    return {
        "ok": bool(successful),
        "reason": "ok" if successful else "no_successful_variants",
        "research_only": True,
        "archive_backed": bool(successful),
        "artifact_type": ARTIFACT_TYPE,
        "venue": str(venue),
        "symbol": str(symbol),
        "timeframe": str(timeframe),
        "variant_count": int(len(ranked)),
        "successful_variant_count": int(len(successful)),
        "ranking_policy": {
            "name": "deterministic_archive_walk_forward_v1",
            "sort_order": [
                "ok first",
                "total_test_closed_trades desc",
                "non_negative_test_window_ratio desc",
                "avg_test_return_pct desc",
                "avg_test_max_drawdown_pct asc",
                "config_hash asc",
            ],
            "research_score": "avg_test_return_pct - avg_test_max_drawdown_pct",
            "promotion_decision": False,
        },
        "dataset_summary": _dataset_summary(ranked),
        "top_variant": dict(successful[0]) if successful else None,
        "ranked_variants": ranked,
    }
