from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from statistics import pstdev
from typing import Any, Dict, Iterable, List

from services.analytics.journal_analytics import fifo_pnl_from_fills
from services.analytics.strategy_feedback import (
    build_strategy_feedback_weighting,
    load_strategy_feedback_ledger,
)
from services.backtest.leaderboard import rank_strategy_rows, run_strategy_leaderboard
from services.backtest.walk_forward import run_anchored_walk_forward
from services.os.app_paths import code_root, data_dir, ensure_dirs
from services.strategies.presets import apply_preset
from services.strategies.hypotheses import get_strategy_hypothesis


from services.backtest.evidence_shared import (
    _fnum,
    _mean,
    _candles_from_closes,
    _default_benchmark_closes,
    _segment_closes,
)

def default_evidence_windows() -> list[dict[str, Any]]:
    return [
        {
            "window_id": "synthetic_default",
            "label": "Synthetic Default Benchmark",
            "notes": "Current repo benchmark series used by the Home Digest and prior decision cycle.",
            "warmup_bars": 50,
            "candles": _candles_from_closes(_default_benchmark_closes(count=180), start_ts_ms=1_700_000_000_000),
        },
        {
            "window_id": "trend_reversal",
            "label": "Trend Reversal",
            "notes": "Long downtrend that reverses into a sustained up move before a smaller fade.",
            "warmup_bars": 20,
            "candles": _candles_from_closes(
                _segment_closes((40, -0.45, None, None), (70, 0.55, 13, 0.8), (30, -0.35, None, None)),
                start_ts_ms=1_700_100_000_000,
            ),
        },
        {
            "window_id": "breakout_pulse",
            "label": "Breakout Pulse",
            "notes": "Tight base, sharp breakout, retrace, and controlled recovery.",
            "warmup_bars": 20,
            "candles": _candles_from_closes(
                _segment_closes((35, 0.01, 2, 0.04), (18, 0.9, None, None), (20, 0.15, None, None), (22, -0.6, None, None), (25, 0.35, None, None)),
                start_ts_ms=1_700_200_000_000,
            ),
        },
        {
            "window_id": "double_reversal",
            "label": "Double Reversal",
            "notes": "Two clear directional swings intended to test repeat participation and exit discipline.",
            "warmup_bars": 15,
            "candles": _candles_from_closes(
                _segment_closes((30, -0.5, None, None), (35, 0.65, 11, 0.7), (25, -0.55, 9, -0.6), (35, 0.5, 13, 0.5)),
                start_ts_ms=1_700_300_000_000,
            ),
        },
        {
            "window_id": "range_snapback",
            "label": "Range Snapback",
            "notes": "Repeating oversold/overbought swing pattern to test controlled countertrend participation.",
            "warmup_bars": 15,
            "candles": _candles_from_closes(
                [float(px) for _ in range(18) for px in (100.0, 98.2, 97.1, 98.9, 101.3, 102.7, 101.0, 99.2)],
                start_ts_ms=1_700_400_000_000,
            ),
        },
        {
            "window_id": "false_breakout_whipsaw",
            "label": "False Breakout Whipsaw",
            "notes": "Tight base, upside breakout, then fast reversal back through the base to test breakout false-positive handling and exit discipline.",
            "warmup_bars": 20,
            "candles": _candles_from_closes(
                _segment_closes(
                    (26, 0.01, 2, -0.02),
                    (14, 0.85, None, None),
                    (10, 0.20, None, None),
                    (18, -1.10, 4, -0.35),
                    (16, -0.20, None, None),
                    (24, 0.06, 2, -0.10),
                ),
                start_ts_ms=1_700_500_000_000,
            ),
        },
        {
            "window_id": "event_trend_grind",
            "label": "Event Trend Grind",
            "notes": "Persistent one-way trend with shallow pullbacks and periodic squeeze bars intended to punish early countertrend entries.",
            "warmup_bars": 20,
            "candles": _candles_from_closes(
                _segment_closes(
                    (28, 0.38, 7, 0.45),
                    (14, -0.06, None, None),
                    (26, 0.52, 5, 0.55),
                    (12, -0.04, None, None),
                    (24, 0.44, 6, 0.35),
                ),
                start_ts_ms=1_700_600_000_000,
            ),
        },
        {
            "window_id": "low_vol_fee_bleed",
            "label": "Low-Vol Fee Bleed",
            "notes": "Slow grind down, tiny reversal, and shallow rebound intended to trigger a small mean-reversion round trip that loses after costs.",
            "warmup_bars": 20,
            "candles": _candles_from_closes(
                _segment_closes(
                    (58, -0.032, None, None),
                    (14, 0.012, None, None),
                    (28, 0.004, None, None),
                    (8, -0.006, None, None),
                ),
                start_ts_ms=1_700_700_000_000,
            ),
        },
    ]


def _decision_for_row(row: dict[str, Any]) -> tuple[str, str]:
    avg_return = _fnum(row.get("avg_return_pct"), 0.0)
    total_closed_trades = int(_fnum(row.get("closed_trades"), 0.0))
    active_window_count = int(_fnum(row.get("active_window_count"), 0.0))
    positive_window_fraction = _fnum(row.get("positive_window_fraction"), 0.0)
    worst_drawdown = _fnum(row.get("max_drawdown_pct"), 0.0)
    rank = int(_fnum(row.get("rank"), 0.0))

    if total_closed_trades <= 0:
        return "freeze", "No realized closed-trade evidence exists across the current window set."
    if avg_return < 0.0 and positive_window_fraction < 0.4:
        return "retire", "Aggregate post-cost return is negative and the strategy is not robust across windows."
    if rank == 1 and total_closed_trades >= 3 and avg_return > 0.0 and positive_window_fraction >= 0.5 and worst_drawdown <= 8.0:
        return "keep", "It is the strongest aggregate candidate with enough closed-trade evidence for continued research."
    if avg_return > 0.0 and active_window_count >= 2:
        if rank == 1:
            return "improve", "It remains the strongest aggregate candidate, but the evidence is still not strong enough for a stronger decision."
        return "improve", "It remains viable, but the evidence is still weaker than the top aggregate candidate."
    return "freeze", "The current evidence is too thin or too inconsistent to justify active iteration."


def _apply_paper_history_adjustment(
    *,
    decision: str,
    reason: str,
    paper_row: dict[str, Any] | None,
) -> tuple[str, str]:
    if not paper_row:
        return decision, reason
    closed_trades = int(_fnum(paper_row.get("closed_trades"), 0.0))
    net_realized = _fnum(paper_row.get("net_realized_pnl"), 0.0)
    win_rate = _fnum(paper_row.get("win_rate"), 0.0)

    if closed_trades >= 2 and net_realized < 0.0:
        downgraded = {
            "keep": "improve",
            "improve": "freeze",
            "freeze": "freeze",
            "retire": "retire",
        }.get(decision, decision)
        return (
            downgraded,
            f"{reason} Persisted paper-history evidence is negative after {closed_trades} closed trade(s), so the decision stays conservative.",
        )
    if closed_trades >= 3 and net_realized > 0.0:
        return (
            decision,
            f"{reason} Supplemental paper-history evidence is positive across {closed_trades} closed trade(s), but it is still not enough to justify promotion.",
        )
    if closed_trades >= 2 and win_rate < 0.4:
        downgraded = {
            "keep": "improve",
            "improve": "freeze",
            "freeze": "freeze",
            "retire": "retire",
        }.get(decision, decision)
        return (
            downgraded,
            f"{reason} Persisted paper-history win rate is weak across {closed_trades} closed trade(s), so the decision remains conservative.",
        )
    return decision, reason


def _paper_history_note(paper_row: dict[str, Any] | None) -> str:
    if not paper_row:
        return "No strategy-attributed persisted paper-history fills are available yet."
    return (
        f"{int(_fnum(paper_row.get('closed_trades'), 0.0))} closed trade(s), "
        f"{_fnum(paper_row.get('net_realized_pnl'), 0.0):+.2f} net realized PnL, "
        f"{_fnum(paper_row.get('win_rate'), 0.0) * 100.0:.1f}% win rate "
        f"across {int(_fnum(paper_row.get('fills'), 0.0))} fill(s)."
    )


RESEARCH_ACCEPTANCE_MIN_PAPER_CLOSED_TRADES = 30
RESEARCH_ACCEPTANCE_MIN_REPRESENTED_WINDOWS = 3
RESEARCH_ACCEPTANCE_MAX_DRAWDOWN_PCT = 10.0


def _evidence_status_for_row(
    *,
    row: dict[str, Any],
    paper_row: dict[str, Any] | None,
    paper_history_status: str,
) -> tuple[str, str, str]:
    total_closed_trades = int(_fnum(row.get("closed_trades"), 0.0))
    active_window_count = int(_fnum(row.get("active_window_count"), 0.0))
    if total_closed_trades <= 0 or active_window_count <= 0:
        return (
            "insufficient",
            "low",
            "No realized closed-trade participation exists across the current evidence windows.",
        )
    if not paper_row:
        basis = "missing" if paper_history_status != "available" else "strategy_missing"
        if basis == "strategy_missing":
            return (
                "synthetic_only",
                "low",
                "Persisted paper-history exists, but this strategy has no attributed paper fills yet, so the decision still relies on synthetic windows.",
            )
        return (
            "synthetic_only",
            "low",
            "Persisted paper-history is missing, so the decision still relies on synthetic windows.",
        )

    paper_fills = int(_fnum(paper_row.get("fills"), 0.0))
    paper_closed_trades = int(_fnum(paper_row.get("closed_trades"), 0.0))
    if paper_fills < 6 or paper_closed_trades < 3:
        return (
            "paper_thin",
            "low",
            "Persisted paper-history exists, but the sample is still too thin to confirm the synthetic ranking.",
        )
    return (
        "paper_supported",
        "medium",
        "Persisted paper-history is present, but the current sample is still research-grade rather than promotion-grade.",
    )


def _research_acceptance_for_row(
    *,
    row: dict[str, Any],
    paper_row: dict[str, Any] | None,
    evidence_status: str,
    confidence_label: str,
) -> dict[str, Any]:
    paper_closed_trades = int(_fnum((paper_row or {}).get("closed_trades"), 0.0))
    represented_windows = int(_fnum(row.get("closed_trade_window_count"), 0.0))
    post_cost_return = _fnum(row.get("net_return_after_costs_pct"), _fnum(row.get("avg_return_pct"), 0.0))
    slippage_sensitivity = _fnum(row.get("slippage_sensitivity_pct"), 0.0)
    stressed_post_cost_return = post_cost_return - slippage_sensitivity
    max_drawdown_pct = _fnum(row.get("max_drawdown_pct"), 0.0)
    blockers: list[str] = []

    if paper_closed_trades < RESEARCH_ACCEPTANCE_MIN_PAPER_CLOSED_TRADES:
        blockers.append(
            f"Persisted paper history only has {paper_closed_trades} closed trade(s); "
            f"the current research floor requires {RESEARCH_ACCEPTANCE_MIN_PAPER_CLOSED_TRADES}."
        )
    if represented_windows < RESEARCH_ACCEPTANCE_MIN_REPRESENTED_WINDOWS:
        blockers.append(
            f"Only {represented_windows} represented window(s) produced realized closed trades; "
            f"the current research floor requires {RESEARCH_ACCEPTANCE_MIN_REPRESENTED_WINDOWS}."
        )
    if post_cost_return <= 0.0:
        blockers.append("Post-cost return is not positive.")
    if stressed_post_cost_return <= 0.0:
        blockers.append("Stressed slippage turns the current post-cost result non-positive.")
    if max_drawdown_pct > RESEARCH_ACCEPTANCE_MAX_DRAWDOWN_PCT:
        blockers.append(
            f"Max drawdown is {max_drawdown_pct:.2f}%; the current research floor requires "
            f"{RESEARCH_ACCEPTANCE_MAX_DRAWDOWN_PCT:.2f}% or less."
        )
    if str(evidence_status or "").strip().lower() != "paper_supported":
        blockers.append(
            f"Evidence status is {str(evidence_status or 'unknown').strip() or 'unknown'}; "
            "the current research floor requires paper_supported."
        )
    if str(confidence_label or "").strip().lower() not in {"medium", "high"}:
        blockers.append(
            f"Confidence is {str(confidence_label or 'unknown').strip() or 'unknown'}; "
            "the current research floor requires at least medium confidence."
        )

    strategy_name = str(row.get("strategy") or "").strip() or "current strategy"
    if blockers:
        return {
            "accepted": False,
            "status": "not_accepted",
            "summary": f"`{strategy_name}` does not meet the current research-acceptance floor yet.",
            "blockers": blockers,
        }
    return {
        "accepted": True,
        "status": "accepted",
        "summary": f"`{strategy_name}` meets the current research-acceptance floor from persisted evidence.",
        "blockers": [],
    }


def _weakness_for_row(row: dict[str, Any], hypothesis: dict[str, Any] | None) -> str:
    expected_failures = [str(item).replace("_", " ") for item in list((hypothesis or {}).get("expected_failure_regimes") or [])]
    decision = str(row.get("decision") or "")
    total_closed_trades = int(_fnum(row.get("closed_trades"), 0.0))
    positive_window_fraction = _fnum(row.get("positive_window_fraction"), 0.0)
    if total_closed_trades <= 0:
        return "No realized trading participation across the current evidence windows."
    if positive_window_fraction < 0.5:
        return "Performance is fragile across windows, not just thin in sample size."
    if decision == "improve" and expected_failures:
        return f"Expected failure regimes are still concentrated in {', '.join(expected_failures[:2])}."
    return "The sample is still small relative to the confidence needed for promotion."


def _improvement_for_row(row: dict[str, Any], hypothesis: dict[str, Any] | None) -> str:
    strategy = str(row.get("strategy") or "")
    total_closed_trades = int(_fnum(row.get("closed_trades"), 0.0))
    if total_closed_trades <= 0:
        return "Review entry filters and regime assumptions before spending more effort on tuning."
    if strategy == "ema_cross":
        return "Tighten chop and low-vol invalidation behavior, then rerun the same window set."
    if strategy == "mean_reversion_rsi":
        return "Relax or retarget participation filters only after a regime-specific hypothesis review."
    if strategy == "breakout_donchian":
        return "Test false-breakout handling and exit discipline over a longer multi-window pack."
    return "Rerun the same evidence pack after the next smallest strategy rule adjustment."


def _combined_walk_forward_candles(window_defs: list[dict[str, Any]]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for item in list(window_defs or []):
        for candle in list(item.get("candles") or []):
            if isinstance(candle, (list, tuple)) and len(candle) >= 5:
                rows.append(list(candle))
    return rows


def _walk_forward_cfg_for_row(*, base_cfg: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    cfg = dict(base_cfg or {})
    candidate = str(row.get("candidate") or "").strip()
    if candidate:
        try:
            cfg = apply_preset(cfg, candidate)
        except Exception:
            cfg = dict(cfg or {})
    strategy_name = str(row.get("strategy") or "").strip()
    strategy_cfg = dict(cfg.get("strategy") or {})
    if strategy_name:
        strategy_cfg["name"] = strategy_name
    cfg["strategy"] = strategy_cfg
    return cfg


def _walk_forward_summary_for_row(
    *,
    row: dict[str, Any],
    base_cfg: dict[str, Any],
    symbol: str,
    combined_candles: list[list[Any]],
    warmup_bars: int,
    initial_cash: float,
    fee_bps: float,
    slippage_bps: float,
) -> dict[str, Any]:
    try:
        result = run_anchored_walk_forward(
            cfg=_walk_forward_cfg_for_row(base_cfg=base_cfg, row=row),
            symbol=str(symbol or ""),
            candles=list(combined_candles or []),
            warmup_bars=max(1, int(warmup_bars)),
            min_train_bars=max(120, int(warmup_bars) + 1),
            test_bars=30,
            step_bars=30,
            max_windows=5,
            initial_cash=float(initial_cash),
            fee_bps=float(fee_bps),
            slippage_bps=float(slippage_bps),
        )
    except Exception as exc:
        result = {
            "ok": False,
            "reason": f"error:{type(exc).__name__}",
            "research_only": True,
            "bars": int(len(combined_candles or [])),
            "warmup_bars": int(max(1, int(warmup_bars))),
            "min_train_bars": int(max(120, int(warmup_bars) + 1)),
            "test_bars": 30,
            "step_bars": 30,
            "window_count": 0,
            "summary": {},
        }
    summary = dict(result.get("summary") or {})
    return {
        "available": bool(result.get("ok")),
        "status": "ok" if bool(result.get("ok")) else str(result.get("reason") or "unavailable"),
        "research_only": bool(result.get("research_only", True)),
        "bars": int(result.get("bars") or 0),
        "warmup_bars": int(result.get("warmup_bars") or 0),
        "min_train_bars": int(result.get("min_train_bars") or 0),
        "test_bars": int(result.get("test_bars") or 0),
        "step_bars": int(result.get("step_bars") or 0),
        "window_count": int(result.get("window_count") or 0),
        "summary": {
            "window_count": int(summary.get("window_count") or 0),
            "positive_test_window_count": int(summary.get("positive_test_window_count") or 0),
            "non_negative_test_window_ratio": float(summary.get("non_negative_test_window_ratio") or 0.0),
            "avg_test_return_pct": float(summary.get("avg_test_return_pct") or 0.0),
            "median_like_test_return_pct": float(summary.get("median_like_test_return_pct") or 0.0),
            "worst_test_return_pct": float(summary.get("worst_test_return_pct") or 0.0),
            "best_test_return_pct": float(summary.get("best_test_return_pct") or 0.0),
            "avg_test_max_drawdown_pct": float(summary.get("avg_test_max_drawdown_pct") or 0.0),
            "total_test_trades": int(summary.get("total_test_trades") or 0),
            "total_test_closed_trades": int(summary.get("total_test_closed_trades") or 0),
        },
    }


def _aggregate_rows(window_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for window in window_reports:
        for row in list(window.get("rows") or []):
            candidate = str(row.get("candidate") or "candidate")
            bucket = grouped.setdefault(
                candidate,
                {
                    "candidate": candidate,
                    "strategy": str(row.get("strategy") or ""),
                    "symbol": str(row.get("symbol") or ""),
                    "window_results": [],
                },
            )
            bucket["window_results"].append(
                {
                    "window_id": str(window.get("window_id") or ""),
                    "label": str(window.get("label") or ""),
                    "rank": int(_fnum(row.get("rank"), 0.0)),
                    "net_return_after_costs_pct": _fnum(row.get("net_return_after_costs_pct"), 0.0),
                    "max_drawdown_pct": _fnum(row.get("max_drawdown_pct"), 0.0),
                    "closed_trades": int(_fnum(row.get("closed_trades"), 0.0)),
                    "trade_count": int(_fnum(row.get("trade_count"), 0.0)),
                    "exposure_fraction": _fnum(row.get("exposure_fraction"), 0.0),
                    "slippage_sensitivity_pct": _fnum(row.get("slippage_sensitivity_pct"), 0.0),
                    "leaderboard_score": _fnum(row.get("leaderboard_score"), 0.0),
                }
            )

    aggregates: list[dict[str, Any]] = []
    for bucket in grouped.values():
        window_rows = list(bucket.get("window_results") or [])
        returns = [_fnum(item.get("net_return_after_costs_pct"), 0.0) for item in window_rows]
        drawdowns = [_fnum(item.get("max_drawdown_pct"), 0.0) for item in window_rows]
        slippage = [_fnum(item.get("slippage_sensitivity_pct"), 0.0) for item in window_rows]
        exposures = [_fnum(item.get("exposure_fraction"), 0.0) for item in window_rows]
        leaderboard_scores = [_fnum(item.get("leaderboard_score"), 0.0) for item in window_rows]
        positive_window_count = sum(1 for value in returns if value > 0.0)
        active_window_count = sum(1 for item in window_rows if int(item.get("trade_count") or 0) > 0)
        closed_trade_window_count = sum(1 for item in window_rows if int(item.get("closed_trades") or 0) > 0)
        total_closed_trades = sum(int(item.get("closed_trades") or 0) for item in window_rows)
        total_trade_count = sum(int(item.get("trade_count") or 0) for item in window_rows)
        worst_idx = min(range(len(returns)), key=lambda idx: returns[idx]) if returns else 0
        best_idx = max(range(len(returns)), key=lambda idx: returns[idx]) if returns else 0
        aggregates.append(
            {
                "candidate": str(bucket.get("candidate") or ""),
                "strategy": str(bucket.get("strategy") or ""),
                "symbol": str(bucket.get("symbol") or ""),
                "window_count": int(len(window_rows)),
                "active_window_count": int(active_window_count),
                "closed_trade_window_count": int(closed_trade_window_count),
                "positive_window_count": int(positive_window_count),
                "positive_window_fraction": float((positive_window_count / len(window_rows)) if window_rows else 0.0),
                "net_return_after_costs_pct": float(_mean(returns)),
                "avg_return_pct": float(_mean(returns)),
                "best_window_return_pct": float(max(returns)) if returns else 0.0,
                "worst_window_return_pct": float(min(returns)) if returns else 0.0,
                "best_window_id": str(window_rows[best_idx].get("window_id") or "") if window_rows else None,
                "worst_window_id": str(window_rows[worst_idx].get("window_id") or "") if window_rows else None,
                "max_drawdown_pct": float(max(drawdowns)) if drawdowns else 0.0,
                "avg_drawdown_pct": float(_mean(drawdowns)),
                "regime_robustness": float((positive_window_count / len(window_rows)) if window_rows else 0.0),
                "regime_return_dispersion_pct": float(pstdev(returns)) if len(returns) >= 2 else 0.0,
                "slippage_sensitivity_pct": float(_mean(slippage)),
                "paper_live_drift_pct": None,
                "closed_trades": int(total_closed_trades),
                "trade_count": int(total_trade_count),
                "exposure_fraction": float(_mean(exposures)),
                "avg_leaderboard_score": float(_mean(leaderboard_scores)),
                "window_results": window_rows,
            }
        )
    return aggregates


def _rerank_rows_by_leaderboard_score(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = [dict(item) for item in list(rows or [])]
    ranked.sort(
        key=lambda row: (
            -_fnum(row.get("leaderboard_score"), 0.0),
            -_fnum(row.get("net_return_after_costs_pct"), 0.0),
            _fnum(row.get("max_drawdown_pct"), 0.0),
        )
    )
    for idx, row in enumerate(ranked, start=1):
        row["rank"] = int(idx)
    return ranked


