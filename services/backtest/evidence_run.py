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
    _now_iso,
    _fnum,
)

def run_strategy_evidence_cycle(
    *,
    base_cfg: Dict[str, Any] | None = None,
    symbol: str = "BTC/USDT",
    initial_cash: float = 10_000.0,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
    windows: list[dict[str, Any]] | None = None,
    paper_history_path: str = "",
) -> dict[str, Any]:
    as_of = _now_iso()
    window_defs = [dict(item) for item in list(windows or default_evidence_windows())]
    combined_walk_forward_candles = _combined_walk_forward_candles(window_defs)
    walk_forward_warmup = max([int(item.get("warmup_bars") or 20) for item in window_defs] or [20])
    paper_history = load_paper_history_evidence(journal_path=paper_history_path, symbol=str(symbol or ""))
    strategy_feedback_ledger = load_strategy_feedback_ledger(journal_path=paper_history_path, symbol=str(symbol or ""))
    paper_history_by_strategy = {
        str(item.get("strategy") or ""): dict(item)
        for item in list(paper_history.get("rows") or [])
        if str(item.get("strategy") or "")
    }
    strategy_feedback_by_strategy = {
        str(item.get("strategy") or ""): dict(item)
        for item in list(strategy_feedback_ledger.get("rows") or [])
        if str(item.get("strategy") or "")
    }
    window_reports: list[dict[str, Any]] = []
    for item in window_defs:
        candles = [list(row) for row in list(item.get("candles") or [])]
        result = run_strategy_leaderboard(
            base_cfg=dict(base_cfg or {}),
            symbol=str(symbol or ""),
            candles=candles,
            warmup_bars=int(item.get("warmup_bars") or 20),
            initial_cash=float(initial_cash),
            fee_bps=float(fee_bps),
            slippage_bps=float(slippage_bps),
        )
        window_reports.append(
            {
                "window_id": str(item.get("window_id") or ""),
                "label": str(item.get("label") or ""),
                "notes": str(item.get("notes") or ""),
                "bars": int(len(candles)),
                "warmup_bars": int(item.get("warmup_bars") or 20),
                "rows": [dict(row) for row in list(result.get("rows") or [])],
            }
        )

    aggregate_rows = rank_strategy_rows(_aggregate_rows(window_reports))
    weighted_rows: list[dict[str, Any]] = []
    for row in aggregate_rows:
        feedback_row = strategy_feedback_by_strategy.get(str(row.get("strategy") or ""))
        feedback_weighting = build_strategy_feedback_weighting(feedback_row)
        base_score = _fnum(row.get("leaderboard_score"), 0.0)
        adjusted_score = float(round(base_score + _fnum(feedback_weighting.get("adjustment"), 0.0), 6))
        row["base_leaderboard_score"] = float(base_score)
        row["strategy_feedback"] = dict(feedback_row or {})
        row["feedback_weighting"] = dict(feedback_weighting)
        row["leaderboard_score"] = float(adjusted_score)
        components = dict(row.get("leaderboard_components") or {})
        components["strategy_feedback_adjustment"] = float(_fnum(feedback_weighting.get("adjustment"), 0.0))
        row["leaderboard_components"] = components
        weighted_rows.append(row)
    aggregate_rows = _rerank_rows_by_leaderboard_score(weighted_rows)
    decisions: list[dict[str, Any]] = []
    for row in aggregate_rows:
        hypothesis = get_strategy_hypothesis(str(row.get("strategy") or ""))
        decision, reason = _decision_for_row(row)
        paper_row = paper_history_by_strategy.get(str(row.get("strategy") or ""))
        decision, reason = _apply_paper_history_adjustment(decision=decision, reason=reason, paper_row=paper_row)
        evidence_status, confidence_label, evidence_note = _evidence_status_for_row(
            row=row,
            paper_row=paper_row,
            paper_history_status=str(paper_history.get("status") or "missing"),
        )
        row["decision"] = decision
        row["decision_reason"] = reason
        row["evidence_status"] = evidence_status
        row["confidence_label"] = confidence_label
        row["evidence_note"] = evidence_note
        row["biggest_weakness"] = _weakness_for_row(row, hypothesis)
        row["next_improvement"] = _improvement_for_row(row, hypothesis)
        row["paper_history"] = dict(paper_row or {})
        row["paper_history_note"] = _paper_history_note(paper_row)
        row["research_acceptance"] = _research_acceptance_for_row(
            row=row,
            paper_row=paper_row,
            evidence_status=evidence_status,
            confidence_label=confidence_label,
        )
        row["walk_forward"] = _walk_forward_summary_for_row(
            row=row,
            base_cfg=dict(base_cfg or {}),
            symbol=str(symbol or ""),
            combined_candles=combined_walk_forward_candles,
            warmup_bars=walk_forward_warmup,
            initial_cash=float(initial_cash),
            fee_bps=float(fee_bps),
            slippage_bps=float(slippage_bps),
        )
        decisions.append(
            {
                "candidate": str(row.get("candidate") or ""),
                "strategy": str(row.get("strategy") or ""),
                "rank": int(row.get("rank") or 0),
                "decision": decision,
                "reason": reason,
                "evidence_status": evidence_status,
                "confidence_label": confidence_label,
                "evidence_note": evidence_note,
                "biggest_weakness": str(row.get("biggest_weakness") or ""),
                "next_improvement": str(row.get("next_improvement") or ""),
                "paper_history_note": str(row.get("paper_history_note") or ""),
                "feedback_weighting_summary": str(((row.get("feedback_weighting") or {}).get("summary")) or ""),
            }
        )

    return {
        "ok": True,
        "as_of": as_of,
        "source": "multi_window_synthetic",
        "symbol": str(symbol or ""),
        "window_count": int(len(window_reports)),
        "fee_bps": float(fee_bps),
        "slippage_bps": float(slippage_bps),
        "initial_cash": float(initial_cash),
        "windows": window_reports,
        "paper_history": paper_history,
        "strategy_feedback_ledger": strategy_feedback_ledger,
        "aggregate_leaderboard": {
            "candidate_count": int(len(aggregate_rows)),
            "rows": aggregate_rows,
        },
        "decisions": decisions,
    }


