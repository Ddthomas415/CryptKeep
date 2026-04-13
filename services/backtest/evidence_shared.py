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


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    if not math.isfinite(out):
        return float(default)
    return out


def _mean(values: Iterable[float]) -> float:
    rows = [float(v) for v in values]
    return float(sum(rows) / len(rows)) if rows else 0.0


def _bounded_ratio(value: Any, full_credit: float) -> float:
    if full_credit <= 0.0:
        return 0.0
    return float(max(0.0, min(_fnum(value, 0.0) / float(full_credit), 1.0)))


def _candles_from_closes(closes: list[float], *, start_ts_ms: int) -> list[list[float]]:
    if not closes:
        return []
    rows: list[list[float]] = []
    prev = float(closes[0])
    for idx, close in enumerate(closes):
        cur = float(close)
        open_px = float(prev)
        rows.append(
            [
                float(start_ts_ms + (idx * 60_000)),
                open_px,
                float(max(open_px, cur) + 0.25),
                float(min(open_px, cur) - 0.25),
                cur,
                float(1.0 + ((idx % 5) * 0.1)),
            ]
        )
        prev = cur
    return rows


def _default_benchmark_closes(*, count: int = 180, start_px: float = 100.0) -> list[float]:
    rows: list[float] = []
    n = max(30, int(count))
    seg = max(10, n // 3)
    prev_close = float(start_px)
    for i in range(n):
        if i < seg:
            close_px = start_px - 0.32 * i
        elif i < 2 * seg:
            close_px = start_px - 0.32 * seg + 0.42 * (i - seg)
        else:
            close_px = start_px - 0.32 * seg + 0.42 * seg - 0.36 * (i - 2 * seg)
        if i % 17 == 0:
            close_px += 0.8
        elif i % 19 == 0:
            close_px -= 0.8
        rows.append(float(close_px))
        prev_close = close_px
    if rows:
        rows[0] = float(prev_close if len(rows) == 1 else rows[0])
    return rows


def _segment_closes(*segments: tuple[int, float, int | None, float | None], start_px: float = 100.0) -> list[float]:
    px = float(start_px)
    closes: list[float] = []
    for length, delta, spike_every, spike in segments:
        for idx in range(max(0, int(length))):
            px += float(delta)
            if spike_every and spike is not None and idx % int(spike_every) == 0:
                px += float(spike)
            closes.append(float(px))
    return closes


def default_trade_journal_path() -> Path:
    ensure_dirs()
    return (data_dir() / "trade_journal.sqlite").resolve()


def _normalize_strategy_name(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if not text:
        return None
    if text in {"ema_cross", "mean_reversion_rsi", "breakout_donchian", "momentum"}:
        return text
    if "ema" in text and ("cross" in text or "xover" in text or "crossover" in text):
        return "ema_cross"
    if "mean_reversion" in text or "mean-reversion" in text or "reversion" in text:
        return "mean_reversion_rsi"
    if "breakout" in text or "donchian" in text:
        return "breakout_donchian"
    return None


def _top_strategy_name(report: dict[str, Any]) -> str | None:
    rows = list(((dict(report or {}).get("aggregate_leaderboard") or {}).get("rows") or []))
    for item in rows:
        if not isinstance(item, dict):
            continue
        strategy = str(item.get("strategy") or "").strip()
        if strategy:
            return strategy
    return None


def _load_recent_history_payloads(evidence_root: Path, *, limit: int = 4) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    paths = sorted(
        path
        for path in evidence_root.glob("strategy_evidence.*.json")
        if path.name != "strategy_evidence.latest.json"
    )
    payloads: list[dict[str, Any]] = []
    for path in paths[-int(limit) :]:
        payload = _load_evidence_payload(path)
        if payload:
            payloads.append(payload)
    return payloads


def _build_recent_trend(
    current_report: dict[str, Any],
    *,
    previous_history_reports: list[dict[str, Any]] | None = None,
    lookback: int = 5,
) -> dict[str, Any]:
    reports = [dict(item) for item in list(previous_history_reports or []) if isinstance(item, dict)]
    reports.append(dict(current_report or {}))
    sequence: list[dict[str, str]] = []
    for payload in reports:
        as_of = str(payload.get("as_of") or "").strip()
        top_strategy = _top_strategy_name(payload)
        if as_of and top_strategy:
            sequence.append({"as_of": as_of, "top_strategy": top_strategy})
    recent = sequence[-max(1, int(lookback)) :]
    if not recent:
        return {
            "has_recent_history": False,
            "run_count": 0,
            "transition_count": 0,
            "distinct_top_strategy_count": 0,
            "current_top_streak": 0,
            "top_strategy_current": None,
            "top_strategy_sequence": [],
            "runs": [],
            "summary_text": "No persisted strategy evidence artifacts are available for recent-trend comparison.",
        }

    top_sequence = [str(item.get("top_strategy") or "") for item in recent if str(item.get("top_strategy") or "").strip()]
    current_top = top_sequence[-1] if top_sequence else None
    transitions = sum(1 for prev, cur in zip(top_sequence, top_sequence[1:]) if prev != cur)
    streak = 0
    if current_top:
        streak = 1
        for strategy in reversed(top_sequence[:-1]):
            if strategy != current_top:
                break
            streak += 1
    distinct_top_count = len({strategy for strategy in top_sequence if strategy})
    if len(recent) <= 1:
        summary_text = "Only one persisted strategy evidence artifact is available, so no recent-trend summary is available."
    elif distinct_top_count <= 1 and current_top:
        summary_text = f"Top strategy has remained {current_top} across the last {len(recent)} persisted evidence runs."
    else:
        summary_text = (
            f"Top strategy changed {transitions} time(s) across the last {len(recent)} persisted evidence runs; "
            f"current top is {current_top or 'unknown'}."
        )
    return {
        "has_recent_history": len(recent) > 1,
        "run_count": int(len(recent)),
        "transition_count": int(transitions),
        "distinct_top_strategy_count": int(distinct_top_count),
        "current_top_streak": int(streak),
        "top_strategy_current": current_top,
        "top_strategy_sequence": top_sequence,
        "runs": recent,
        "summary_text": summary_text,
    }


