from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from statistics import pstdev
from typing import Any, Dict, Iterable, List

from services.analytics.journal_analytics import fifo_pnl_from_fills
from services.backtest.leaderboard import rank_strategy_rows, run_strategy_leaderboard
from services.os.app_paths import code_root, data_dir, ensure_dirs
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
    if text in {"ema_cross", "mean_reversion_rsi", "breakout_donchian"}:
        return text
    if "ema" in text and ("cross" in text or "xover" in text or "crossover" in text):
        return "ema_cross"
    if "mean_reversion" in text or "mean-reversion" in text or "reversion" in text:
        return "mean_reversion_rsi"
    if "breakout" in text or "donchian" in text:
        return "breakout_donchian"
    return None


def load_paper_history_evidence(*, journal_path: str = "") -> dict[str, Any]:
    path = Path(journal_path).expanduser().resolve() if journal_path else default_trade_journal_path()
    if not path.exists():
        return {
            "ok": False,
            "status": "missing",
            "journal_path": str(path),
            "source": "trade_journal_sqlite",
            "as_of": None,
            "fills_count": 0,
            "strategy_count": 0,
            "rows": [],
            "unmapped_strategy_ids": [],
            "caveat": "No persisted trade journal exists yet, so strategy-attributed paper-history evidence is unavailable.",
        }

    try:
        con = sqlite3.connect(str(path))
        con.row_factory = sqlite3.Row
    except Exception as exc:
        return {
            "ok": False,
            "status": "missing",
            "journal_path": str(path),
            "source": "trade_journal_sqlite",
            "as_of": None,
            "fills_count": 0,
            "strategy_count": 0,
            "rows": [],
            "unmapped_strategy_ids": [],
            "caveat": f"Persisted trade journal could not be opened ({type(exc).__name__}); strategy-attributed paper-history evidence is unavailable.",
        }

    try:
        table = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='journal_fills'"
        ).fetchone()
        if not table:
            return {
                "ok": False,
                "status": "missing",
                "journal_path": str(path),
                "source": "trade_journal_sqlite",
                "as_of": None,
                "fills_count": 0,
                "strategy_count": 0,
                "rows": [],
                "unmapped_strategy_ids": [],
                "caveat": "Persisted trade journal exists but has no journal_fills table yet, so strategy-attributed paper-history evidence is unavailable.",
            }

        rows = con.execute(
            "SELECT fill_id, journal_ts, strategy_id, fill_ts, symbol, side, qty, price, fee, realized_pnl_total "
            "FROM journal_fills ORDER BY fill_ts ASC"
        ).fetchall()
    except Exception as exc:
        return {
            "ok": False,
            "status": "missing",
            "journal_path": str(path),
            "source": "trade_journal_sqlite",
            "as_of": None,
            "fills_count": 0,
            "strategy_count": 0,
            "rows": [],
            "unmapped_strategy_ids": [],
            "caveat": f"Persisted trade journal could not be read ({type(exc).__name__}); strategy-attributed paper-history evidence is unavailable.",
        }
    finally:
        con.close()

    grouped: dict[str, list[dict[str, Any]]] = {}
    strategy_ids_by_name: dict[str, set[str]] = {}
    unmapped: set[str] = set()
    latest_ts: str | None = None

    for row in rows:
        item = dict(row)
        latest_ts = str(item.get("fill_ts") or item.get("journal_ts") or latest_ts or "") or latest_ts
        raw_strategy_id = str(item.get("strategy_id") or "").strip()
        strategy_name = _normalize_strategy_name(raw_strategy_id)
        if strategy_name is None:
            if raw_strategy_id:
                unmapped.add(raw_strategy_id)
            continue
        grouped.setdefault(strategy_name, []).append(item)
        strategy_ids_by_name.setdefault(strategy_name, set()).add(raw_strategy_id)

    if not grouped:
        caveat = "Persisted trade journal has no strategy-attributed paper-history fills yet."
        if unmapped:
            caveat = (
                caveat
                + f" Unmapped strategy IDs were present: {', '.join(sorted(unmapped)[:5])}."
            )
        return {
            "ok": False,
            "status": "missing",
            "journal_path": str(path),
            "source": "trade_journal_sqlite",
            "as_of": latest_ts,
            "fills_count": 0,
            "strategy_count": 0,
            "rows": [],
            "unmapped_strategy_ids": sorted(unmapped),
            "caveat": caveat,
        }

    summary_rows: list[dict[str, Any]] = []
    total_fills = 0
    for strategy_name, fills in grouped.items():
        analytics = fifo_pnl_from_fills(fills)
        summary = dict(analytics.get("summary") or {})
        total_fills += len(fills)
        latest_fill_ts = str(fills[-1].get("fill_ts") or fills[-1].get("journal_ts") or "")
        summary_rows.append(
            {
                "strategy": strategy_name,
                "source_strategy_ids": sorted(strategy_ids_by_name.get(strategy_name) or []),
                "fills": int(len(fills)),
                "closed_trades": int(summary.get("closed_trades") or 0),
                "wins": int(summary.get("wins") or 0),
                "losses": int(summary.get("losses") or 0),
                "win_rate": float(summary.get("win_rate") or 0.0),
                "gross_realized_pnl": float(summary.get("gross_realized_pnl") or 0.0),
                "net_realized_pnl": float(summary.get("net_realized_pnl") or 0.0),
                "total_fees": float(summary.get("total_fees") or 0.0),
                "latest_fill_ts": latest_fill_ts or None,
            }
        )
    summary_rows.sort(key=lambda item: (-int(item.get("fills") or 0), str(item.get("strategy") or "")))

    caveat = "Persisted paper-history evidence is supplemental. It improves operator truth, but it is not enough by itself to prove profitability or promotion readiness."
    if unmapped:
        caveat += f" Unmapped strategy IDs were ignored: {', '.join(sorted(unmapped)[:5])}."
    return {
        "ok": True,
        "status": "available",
        "journal_path": str(path),
        "source": "trade_journal_sqlite",
        "as_of": latest_ts,
        "fills_count": int(total_fills),
        "strategy_count": int(len(summary_rows)),
        "rows": summary_rows,
        "unmapped_strategy_ids": sorted(unmapped),
        "caveat": caveat,
    }


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
    paper_history = load_paper_history_evidence(journal_path=paper_history_path)
    paper_history_by_strategy = {
        str(item.get("strategy") or ""): dict(item)
        for item in list(paper_history.get("rows") or [])
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
        "aggregate_leaderboard": {
            "candidate_count": int(len(aggregate_rows)),
            "rows": aggregate_rows,
        },
        "decisions": decisions,
    }


def evidence_dir() -> Path:
    ensure_dirs()
    path = data_dir() / "strategy_evidence"
    path.mkdir(parents=True, exist_ok=True)
    return path


def persist_strategy_evidence(report: dict[str, Any], *, latest_path: str = "") -> dict[str, Any]:
    payload = dict(report or {})
    evidence_root = evidence_dir()
    ts_token = str(payload.get("as_of") or _now_iso()).replace(":", "").replace("-", "").replace("Z", "Z")
    latest = Path(latest_path).expanduser().resolve() if latest_path else (evidence_root / "strategy_evidence.latest.json").resolve()
    history = (evidence_root / f"strategy_evidence.{ts_token}.json").resolve()
    latest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    history.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "latest_path": str(latest),
        "history_path": str(history),
    }


def default_decision_record_path(*, report: dict[str, Any] | None = None) -> Path:
    payload = dict(report or {})
    as_of = str(payload.get("as_of") or _now_iso())
    date_token = as_of.split("T", 1)[0]
    return (code_root() / "docs" / "strategies" / f"decision_record_{date_token}.md").resolve()


def render_decision_record(report: dict[str, Any], *, artifact_path: str = "") -> str:
    payload = dict(report or {})
    rows = [dict(item) for item in list(((payload.get("aggregate_leaderboard") or {}).get("rows") or []))]
    decisions = [dict(item) for item in list(payload.get("decisions") or [])]
    windows = [dict(item) for item in list(payload.get("windows") or [])]
    paper_history = dict(payload.get("paper_history") or {})
    as_of = str(payload.get("as_of") or _now_iso())
    date_token = as_of.split("T", 1)[0]

    keep = [f"`{item['strategy']}`" for item in decisions if str(item.get("decision") or "") == "keep"]
    improve = [f"`{item['strategy']}`" for item in decisions if str(item.get("decision") or "") == "improve"]
    freeze = [f"`{item['strategy']}`" for item in decisions if str(item.get("decision") or "") == "freeze"]
    retire = [f"`{item['strategy']}`" for item in decisions if str(item.get("decision") or "") == "retire"]

    out: list[str] = [
        f"# Strategy Decision Record — {date_token}",
        "",
        "## Scope",
        "",
        f"This record reflects the current repo state on {date_token}.",
        "",
        "Guardrails:",
        "- crypto-first scope",
        "- paper-heavy defaults remain active",
        "- live trading is guarded and fail-closed",
        "- stock support is not proven",
        "- shorting is not fully validated",
        "- this is not a profitability claim",
        "",
        "## Safety Gate",
        "",
        "Phase 1 safety pack should be rerun before relying on this record.",
        "",
        "## Evaluation Inputs",
        "",
        f"- symbol: `{str(payload.get('symbol') or '')}`",
        f"- windows: `{int(payload.get('window_count') or 0)}` deterministic synthetic windows",
        f"- initial cash: `{_fnum(payload.get('initial_cash'), 0.0):.0f}`",
        f"- fees: `{_fnum(payload.get('fee_bps'), 0.0):.0f} bps`",
        f"- slippage: `{_fnum(payload.get('slippage_bps'), 0.0):.0f} bps`",
    ]
    if paper_history:
        out.append(f"- paper-history source: `{str(paper_history.get('source') or 'unknown')}`")
        out.append(f"- paper-history status: `{str(paper_history.get('status') or 'missing')}`")
        out.append(f"- paper-history journal: `{str(paper_history.get('journal_path') or '')}`")
        out.append(f"- paper-history fills: `{int(paper_history.get('fills_count') or 0)}`")
    if artifact_path:
        out.append(f"- evidence artifact: `{artifact_path}`")
    out.extend(
        [
            "",
            "Window set:",
        ]
    )
    for window in windows:
        out.append(
            f"- `{str(window.get('window_id') or '')}`: {str(window.get('label') or '')} ({int(window.get('bars') or 0)} bars)"
        )
    out.extend(
        [
            "",
            "Important limitation:",
            "- these windows are deterministic synthetic benchmarks, not live or market-history proof",
            "- this cycle is stronger than a single-window pass, but it still does not prove profitability or promotion readiness by itself",
            f"- persisted paper-history status for this run is `{str(paper_history.get('status') or 'missing')}`",
            "",
            "## Results",
            "",
        ]
    )
    for row in rows:
        out.extend(
            [
                f"### `{str(row.get('strategy') or '')}`",
                f"- candidate: `{str(row.get('candidate') or '')}`",
                f"- rank: `{int(row.get('rank') or 0)}`",
                f"- aggregate leaderboard score: `{_fnum(row.get('leaderboard_score'), 0.0):.6f}`",
                f"- average net return after costs: `{_fnum(row.get('avg_return_pct'), 0.0):+.2f}%`",
                f"- worst-window return: `{_fnum(row.get('worst_window_return_pct'), 0.0):+.2f}%`",
                f"- worst drawdown: `{_fnum(row.get('max_drawdown_pct'), 0.0):.2f}%`",
                f"- closed trades: `{int(row.get('closed_trades') or 0)}`",
                f"- active windows: `{int(row.get('active_window_count') or 0)}` / `{int(row.get('window_count') or 0)}`",
                f"- positive windows: `{int(row.get('positive_window_count') or 0)}` / `{int(row.get('window_count') or 0)}`",
                f"- best window: `{str(row.get('best_window_id') or 'unknown')}`",
                f"- worst window: `{str(row.get('worst_window_id') or 'unknown')}`",
                f"- evidence status: `{str(row.get('evidence_status') or 'unknown')}`",
                f"- confidence: `{str(row.get('confidence_label') or 'unknown')}`",
                f"- paper-history: {str(row.get('paper_history_note') or 'No strategy-attributed persisted paper-history fills are available yet.')}",
                "",
                f"Decision: `{str(row.get('decision') or 'unknown')}`",
                "",
                "Reason:",
                f"- {str(row.get('decision_reason') or 'No reason recorded.')}",
                f"- Evidence note: {str(row.get('evidence_note') or 'No evidence note recorded.')}",
                f"- Biggest weakness: {str(row.get('biggest_weakness') or 'Unknown.')}",
                "",
                "Next work:",
                f"- {str(row.get('next_improvement') or 'Rerun the evidence cycle after the next smallest change.')}",
                "",
            ]
        )
    out.extend(
        [
            "## Forced Decision Set",
            "",
            "Keep:",
            *([f"- {item}" for item in keep] or ["- none"]),
            "",
            "Improve:",
            *([f"- {item}" for item in improve] or ["- none"]),
            "",
            "Freeze:",
            *([f"- {item}" for item in freeze] or ["- none"]),
            "",
            "Retire:",
            *([f"- {item}" for item in retire] or ["- none"]),
            "",
            "## Operator Interpretation",
            "",
            "What this does **not** mean:",
            "- no strategy is proven profitable",
            "- no strategy is approved for real-live promotion",
            "- no claim is made about validated short support",
            "",
            "What it **does** mean:",
            "- the strategy ranking now reflects multiple deterministic windows instead of one benchmark pass",
            "- inactive or low-participation candidates are easier to challenge with explicit evidence",
            "- persisted paper-history evidence is included when available, but missing paper history is now explicit instead of silent",
            "- promotion decisions should still remain conservative until broader paper or sandbox evidence exists",
            "",
            "## Follow-up Gaps",
            "",
            "The next improvement to the evaluation layer should be:",
            "- persist multiple evidence runs and compare deltas over time",
            "- grow the trade journal so paper-history evidence is no longer missing or thin",
            "- feed the persisted evidence artifact into the Home Digest instead of rebuilding a single-window summary on demand",
            "",
        ]
    )
    return "\n".join(out)


def write_decision_record(report: dict[str, Any], *, path: str = "", artifact_path: str = "") -> dict[str, Any]:
    target = Path(path).expanduser().resolve() if path else default_decision_record_path(report=report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_decision_record(report, artifact_path=artifact_path), encoding="utf-8")
    return {
        "ok": True,
        "path": str(target),
    }
