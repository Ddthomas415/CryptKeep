#!/usr/bin/env python3
"""scripts/check_promotion_gates.py

Machine-readable promotion gate checker for es_daily_trend_v1.

Reads evidence logs, session logs, and runtime state to produce a
pass/fail report for each gate in the promotion checklist.

Usage:
    python scripts/check_promotion_gates.py
    python scripts/check_promotion_gates.py --stage paper
    python scripts/check_promotion_gates.py --json
    python scripts/check_promotion_gates.py --strict   # exit 1 if any gate fails

Output:
    PASS / FAIL / UNKNOWN per gate, with reason.
    Overall: READY or NOT READY to promote.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml

from services.control.cognitive_budget import budget_summary
from services.control.deployment_stage import Stage, get_current_stage, stage_summary
from services.control.paper_promotion_policy import (
    count_qualified_signal_bars,
    resolve_paper_promotion_policy,
)
from services.control.promotion_thresholds import (
    ES_DAILY_TREND_STRATEGY_ID,
    PAPER_MIN_DAYS,
    PAPER_MIN_ROUND_TRIPS,
)

STRATEGY_ID = ES_DAILY_TREND_STRATEGY_ID
REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs/strategies/es_daily_trend_v1.yaml"


# ---------------------------------------------------------------------------
# Evidence readers
# ---------------------------------------------------------------------------

def _evidence_dir() -> Path:
    from services.os.app_paths import data_dir
    return data_dir() / "evidence" / STRATEGY_ID


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def _load_all_evidence(ev_dir: Path) -> dict[str, list[dict]]:
    """Load all evidence log files by type. Delegates to service layer."""
    from services.control.retirement_checker import load_all_evidence
    return load_all_evidence(ev_dir)


def _count_round_trips(fills: list[dict]) -> int:
    """Count completed long round trips without bridging symbols or time.

    This is a fallback/diagnostic helper. The authoritative paper gate uses
    paper-history qualification, but capped-live and legacy JSONL summaries
    still need a conservative count. Count a trip only when chronological fills
    for the same symbol close an open long cycle.
    """
    open_qty_by_symbol: dict[str, float] = {}
    trips = 0
    for fill in sorted(list(fills or []), key=_record_timestamp_sort_key):
        side = str(fill.get("side") or "").strip().lower()
        if side not in {"buy", "sell"}:
            continue
        qty = _fill_qty(fill)
        if qty <= 0.0:
            continue
        symbol = _fill_symbol(fill)
        open_qty = float(open_qty_by_symbol.get(symbol, 0.0))
        if side == "buy":
            open_qty_by_symbol[symbol] = open_qty + qty
            continue
        if open_qty <= 1e-12:
            continue
        remaining = max(0.0, open_qty - qty)
        open_qty_by_symbol[symbol] = remaining
        if remaining <= 1e-12:
            trips += 1
    return trips


def _fill_symbol(fill: dict) -> str:
    for key in ("symbol", "ohlcv_symbol", "market_symbol", "pair"):
        value = str(fill.get(key) or "").strip().upper()
        if value:
            return value
    return "__unknown_symbol__"


def _fill_qty(fill: dict) -> float:
    for key in ("size", "qty", "amount"):
        if key not in fill:
            continue
        try:
            return float(fill.get(key))
        except Exception:
            return 0.0
    # Legacy JSONL evidence sometimes recorded side without quantity; preserve
    # the old single-fill counting contract for those rows.
    return 1.0


def _record_timestamp_sort_key(fill: dict) -> tuple[int, str]:
    for key in ("timestamp", "_logged_at", "fill_ts", "date"):
        raw = str(fill.get(key) or "").strip()
        if not raw:
            continue
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except Exception:
            return (1, raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return (0, parsed.isoformat())
    return (1, "")


def _first_session_date(sessions: list[dict]) -> datetime | None:
    for s in sessions:
        ts = s.get("timestamp") or s.get("date") or s.get("session_start")
        if ts:
            try:
                return datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            except Exception:
                pass
    return None


def _days_of_operation(sessions: list[dict]) -> int:
    dates = set()
    for s in sessions:
        ts = s.get("timestamp") or s.get("date") or s.get("session_start")
        if ts:
            try:
                d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                dates.add(d.date())
            except Exception:
                pass
    return len(dates)


def _any_regime_block(signals: list[dict]) -> bool:
    """Check if regime filter ever blocked an entry."""
    return any(
        str(s.get("regime_flag", "")).lower() in ("chop", "high_vol")
        for s in signals
    )


def _halt_tested(sessions: list[dict]) -> bool:
    """Check if a daily loss halt was triggered at least once."""
    return any(
        "daily_loss_halt" in str(s.get("halts_triggered", "")).lower()
        for s in sessions
    )


def _kill_switch_tested(sessions: list[dict]) -> bool:
    return any(s.get("kill_switch_tested") is True for s in sessions)


def _session_ts(row: dict) -> datetime | None:
    ts = row.get("timestamp") or row.get("date") or row.get("session_start")
    if not ts:
        return None
    try:
        parsed = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _kill_switch_max_age_days(cfg: dict) -> int:
    raw = str(((cfg.get("ops") or {}).get("kill_switch_test_frequency")) or "weekly").strip().lower()
    if raw in {"daily", "1d", "1 day"}:
        return 1
    if raw in {"weekly", "7d", "7 days", "1 week"}:
        return 7
    if raw in {"monthly", "30d", "30 days", "1 month"}:
        return 30
    try:
        return max(1, int(raw))
    except Exception:
        return 7


def _kill_switch_test_status(
    sessions: list[dict],
    cfg: dict,
    *,
    reference_ts: datetime | None = None,
) -> dict:
    max_age_days = _kill_switch_max_age_days(cfg)
    tested = [
        ts
        for row in list(sessions or [])
        if row.get("kill_switch_tested") is True
        if (ts := _session_ts(dict(row))) is not None
    ]
    if not sessions:
        return {
            "ok": None,
            "detail": "no session logs found",
            "hint": "set kill_switch_tested=True in session log after testing",
            "last_tested_ts": None,
            "max_age_days": max_age_days,
        }
    if not tested:
        return {
            "ok": False,
            "detail": "no kill_switch_tested=True session log found",
            "hint": "set kill_switch_tested=True in session log after testing",
            "last_tested_ts": None,
            "max_age_days": max_age_days,
        }

    last_tested = max(tested)
    reference = reference_ts or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    age_days = max(0.0, (reference - last_tested).total_seconds() / 86400.0)
    ok = age_days <= float(max_age_days)
    return {
        "ok": ok,
        "detail": (
            f"kill_switch_tested=True last seen {last_tested.isoformat()} "
            f"({age_days:.1f} days old, max {max_age_days})"
        ),
        "hint": "" if ok else "repeat kill-switch test before promotion",
        "last_tested_ts": last_tested.isoformat(),
        "age_days": float(age_days),
        "max_age_days": max_age_days,
    }


def _check_expectancy(fills: list[dict]) -> tuple[bool | None, float | None]:
    """Check if observed expectancy is positive."""
    pnls = [float(f.get("pnl_usd") or 0) for f in fills if "pnl_usd" in f]
    if len(pnls) < 10:
        return None, None
    avg = sum(pnls) / len(pnls)
    return avg > 0, avg


def _pnl_semantics_summary(fills: list[dict]) -> dict:
    """Summarize pnl_usd semantics for expectancy-eligible evidence.

    This is report-only. It makes mixed legacy gross-PnL and net-of-fees
    evidence visible without changing gate pass/fail behavior.
    """
    counts: dict[str, int] = {}
    for fill in fills:
        if "pnl_usd" not in fill:
            continue
        semantics = str(fill.get("pnl_usd_semantics") or "unknown_legacy")
        counts[semantics] = counts.get(semantics, 0) + 1
    distinct = [key for key, value in counts.items() if value > 0]
    warning = ""
    if len(distinct) > 1:
        warning = (
            "expectancy averages fills with mixed pnl_usd semantics; segment "
            "legacy gross-PnL and net_of_fees evidence before treating the "
            "value as profitability proof"
        )
    return {"counts": counts, "mixed": len(distinct) > 1, "warning": warning}


def _target_feedback_strategy(cfg: dict) -> str:
    strategy = cfg.get("strategy") or {}
    strategy_id = str(strategy.get("id") or STRATEGY_ID).strip().lower()
    signal_type = str((strategy.get("signal") or {}).get("type") or "").strip().lower()
    if strategy_id.startswith("es_daily_trend") or signal_type == "sma_crossover":
        return "sma_200_trend"
    return strategy_id or STRATEGY_ID


def _paper_history_gate_summary(cfg: dict, evidence_fills: list[dict] | None = None) -> dict:
    """Load raw history and derive provenance-qualified promotion metrics."""
    from services.analytics.strategy_feedback import load_strategy_feedback_ledger
    from services.control.paper_evidence_qualification import qualify_paper_history

    strategy = cfg.get("strategy") or {}
    target_strategy = _target_feedback_strategy(cfg)
    symbol = str(strategy.get("symbol") or "").strip()
    try:
        ledger = load_strategy_feedback_ledger(symbol=symbol)
    except Exception as exc:
        return {
            "ok": False,
            "status": "error",
            "source": "trade_journal_sqlite",
            "target_strategy": target_strategy,
            "symbol_filter": symbol or None,
            "fills": 0,
            "closed_trades": 0,
            "expectancy_per_closed_trade": None,
            "net_realized_pnl": None,
            "caveat": f"paper-history could not be read ({type(exc).__name__})",
        }

    rows = [dict(row) for row in list(ledger.get("rows") or []) if isinstance(row, dict)]
    row = next((item for item in rows if str(item.get("strategy") or "") == target_strategy), None)
    qualified = qualify_paper_history(
        evidence_fills=list(evidence_fills or []),
        config=cfg,
        journal_path=str(ledger.get("journal_path") or ""),
    )
    if not row:
        return {
            **qualified,
            "target_strategy": target_strategy,
            "symbol_filter": ledger.get("symbol_filter") or symbol or None,
            "all_history": {
                "ok": False,
                "status": str(ledger.get("status") or "missing"),
                "source": str(ledger.get("source") or "trade_journal_sqlite"),
                "journal_path": str(ledger.get("journal_path") or ""),
                "fills": 0,
                "closed_trades": 0,
            },
            "all_history_fills": 0,
            "all_history_closed_trades": 0,
            "caveat": "No target-strategy paper-history row is available yet.",
        }

    raw_history = {
        "ok": True,
        "status": "available",
        "source": str(ledger.get("source") or "trade_journal_sqlite"),
        "journal_path": str(ledger.get("journal_path") or ""),
        "target_strategy": target_strategy,
        "symbol_filter": ledger.get("symbol_filter") or symbol or None,
        "fills": int(row.get("fills") or 0),
        "closed_trades": int(row.get("closed_trades") or 0),
        "expectancy_per_closed_trade": float(row.get("expectancy_per_closed_trade") or 0.0),
        "net_realized_pnl": float(row.get("net_realized_pnl") or 0.0),
        "win_rate": float(row.get("win_rate") or 0.0),
        "avg_win": float(row.get("avg_win") or 0.0),
        "avg_loss": float(row.get("avg_loss") or 0.0),
        "avg_win_return_pct": float(row.get("avg_win_return_pct") or 0.0),
        "avg_loss_return_pct": float(row.get("avg_loss_return_pct") or 0.0),
        "expectancy_return_pct": float(row.get("expectancy_return_pct") or 0.0),
        "latest_fill_ts": row.get("latest_fill_ts"),
    }
    return {
        **qualified,
        "target_strategy": target_strategy,
        "symbol_filter": ledger.get("symbol_filter") or symbol or None,
        "all_history": raw_history,
        "all_history_fills": int(raw_history["fills"]),
        "all_history_closed_trades": int(raw_history["closed_trades"]),
    }


def _paper_gate_trade_metrics(fills: list[dict], paper_history: dict | None = None) -> dict:
    history = dict(paper_history or {})
    jsonl_trips = _count_round_trips(fills)
    semantics = _pnl_semantics_summary(fills)
    if history.get("qualification") is not None or (
        history.get("ok") is True and int(history.get("fills") or 0) > 0
    ):
        trips = int(history.get("closed_trades") or 0)
        fill_count = int(history.get("fills") or 0)
        exp_val = (
            float(history.get("expectancy_per_closed_trade") or 0.0)
            if fill_count >= 10
            else None
        )
        source = str(history.get("source") or "paper_history")
        if history.get("qualification") is not None:
            all_history_trips = int(history.get("all_history_closed_trades") or 0)
            qualification = dict(history.get("qualification") or {})
            evidence_fills = int(qualification.get("evidence_fills") or 0)
            unqualified_fills = int(
                qualification.get("unqualified_evidence_fills") or 0
            )
            incomplete_fills = int(
                qualification.get("incomplete_qualified_evidence_fills") or 0
            )
            excluded_before_cohort = int(
                qualification.get("excluded_before_cohort_evidence_fills") or 0
            )
            clauses: list[str] = []
            excluded_trips = max(0, all_history_trips - trips)
            if excluded_trips:
                clauses.append(
                    f"{excluded_trips} diagnostic-only all-history round trips"
                )
            if evidence_fills <= 0:
                clauses.append("no JSONL fills available for provenance qualification")
            elif unqualified_fills:
                clauses.append(
                    f"{unqualified_fills}/{evidence_fills} JSONL fills lack or mismatch "
                    "required provenance"
                )
            if incomplete_fills:
                noun = "fill is" if incomplete_fills == 1 else "fills are"
                clauses.append(
                    f"{incomplete_fills} qualified JSONL {noun} not part of a "
                    "complete qualified round trip"
                )
            if excluded_before_cohort:
                noun = "fill" if excluded_before_cohort == 1 else "fills"
                clauses.append(
                    f"{excluded_before_cohort} evidence {noun} excluded before cohort_start"
                )
            first_qualified_ts = str(
                qualification.get("first_provenance_qualified_fill_ts") or ""
            ).strip()
            latest_qualified_ts = str(
                qualification.get("latest_provenance_qualified_fill_ts") or ""
            ).strip()
            if first_qualified_ts and latest_qualified_ts:
                clauses.append(
                    "qualified fill window "
                    f"{first_qualified_ts} to {latest_qualified_ts}"
                )
            unqualified_dates = {
                str(key): int(value)
                for key, value in dict(
                    qualification.get("unqualified_date_counts") or {}
                ).items()
                if str(key).strip() and int(value or 0) > 0
            }
            if unqualified_dates:
                date_summary = ", ".join(
                    f"{date}:{count}" for date, count in sorted(unqualified_dates.items())
                )
                clauses.append(f"unqualified fill dates {date_summary}")
            context = f"; {'; '.join(clauses)}" if clauses else ""
            mismatch = (
                f" (all_history:{all_history_trips}, raw_jsonl:{jsonl_trips}{context})"
            )
        else:
            mismatch = f" (jsonl:{jsonl_trips})" if jsonl_trips != trips else ""
        return {
            "source": source,
            "round_trips": trips,
            "round_trip_detail": f"{trips} round trips recorded from {source}{mismatch}",
            "expectancy_ok": (exp_val > 0.0) if exp_val is not None else None,
            "expectancy_value": exp_val,
            "expectancy_pnl_semantics": semantics["counts"],
            "expectancy_mixed_semantics": semantics["mixed"],
            "expectancy_semantics_warning": semantics["warning"],
            "expectancy_detail": (
                f"avg pnl/round trip = ${exp_val:.2f} from {source}"
                if exp_val is not None
                else "insufficient paper-history fills for calculation"
            ),
            "expectancy_hint": "need 10+ paper-history fills" if exp_val is None else "",
        }

    return {
        "source": "jsonl_evidence",
        "round_trips": jsonl_trips,
        "round_trip_detail": f"{jsonl_trips} round trips recorded",
        "expectancy_ok": None,
        "expectancy_value": None,
        "expectancy_pnl_semantics": semantics["counts"],
        "expectancy_mixed_semantics": semantics["mixed"],
        "expectancy_semantics_warning": semantics["warning"],
        "expectancy_detail": "paper-history qualification is required for authoritative expectancy",
        "expectancy_hint": (
            "do not use JSONL per-fill pnl fallback for paper promotion; "
            "collect provenance-qualified paper-history round trips"
        ),
    }


def _paper_progress_summary(
    paper_history: dict | None,
    *,
    policy: Any | None = None,
    bar_summary: dict | None = None,
) -> dict:
    """Machine-readable paper threshold progress for alerts and dashboards."""
    history = dict(paper_history or {})
    resolved_policy = policy or resolve_paper_promotion_policy({})
    bars = dict(bar_summary or {})
    round_trips = int(history.get("closed_trades") or 0)
    out = {
        "source": str(history.get("source") or "paper_history"),
        "round_trips_recorded": round_trips,
        "round_trips_required": int(getattr(resolved_policy, "min_qualified_round_trips", PAPER_MIN_ROUND_TRIPS)),
        "round_trips_remaining": max(
            0,
            int(getattr(resolved_policy, "min_qualified_round_trips", PAPER_MIN_ROUND_TRIPS))
            - round_trips,
        ),
        "round_trips_ready": round_trips
        >= int(getattr(resolved_policy, "min_qualified_round_trips", PAPER_MIN_ROUND_TRIPS)),
        "all_history_round_trips": int(history.get("all_history_closed_trades") or 0),
    }
    policy_id = str(getattr(resolved_policy, "policy_id", ""))
    should_extend = (
        policy_id != "legacy_round_trip_v1"
        or not bool(getattr(resolved_policy, "valid", True))
        or bool(getattr(resolved_policy, "cohort_start", None))
        or bool(bars.get("enabled"))
    )
    if should_extend:
        out.update(
            {
                "policy_id": policy_id,
                "policy_valid": bool(getattr(resolved_policy, "valid", True)),
                "policy_invalid_reasons": list(
                    getattr(resolved_policy, "invalid_reasons", ())
                ),
                "cohort_start": getattr(resolved_policy, "cohort_start", None),
                "qualified_bars_recorded": int(
                    bars.get("qualified_bars_recorded") or 0
                ),
                "qualified_bars_required": int(
                    bars.get("qualified_bars_required") or 0
                ),
                "qualified_bars_remaining": int(
                    bars.get("qualified_bars_remaining") or 0
                ),
                "qualified_bars_ready": bool(bars.get("qualified_bars_ready", True)),
                "qualified_bars_enabled": bool(bars.get("enabled")),
                "bar_count_source": str(bars.get("bar_count_source") or "none"),
            }
        )
    return out


def _weeks_at_stage(stage: Stage) -> float | None:
    """Estimate weeks the strategy has been at the current stage."""
    summary = stage_summary(STRATEGY_ID)
    if summary.get("stage") != stage.value:
        return None
    since = summary.get("since_ts")
    if not since:
        return None
    try:
        t = datetime.fromisoformat(str(since).replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - t
        return delta.days / 7.0
    except Exception:
        return None


def _record_stage(row: dict) -> str:
    return str(row.get("_stage") or "").strip().lower()


def _record_timestamp(row: dict) -> datetime | None:
    ts = row.get("timestamp") or row.get("_logged_at") or row.get("date")
    if not ts:
        return None
    try:
        parsed = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _active_stage_evidence(
    evidence: dict[str, list[dict]],
    *,
    requested_stage: Stage,
    current_stage: Stage,
    since_ts: str | None,
) -> tuple[dict[str, list[dict]], dict]:
    """Select evidence explicitly stamped for the active requested stage."""
    empty = {record_type: [] for record_type in ("signal", "order", "fill", "session", "drawdown")}
    if requested_stage != current_stage:
        return empty, {
            "stage": requested_stage.value,
            "current_stage": current_stage.value,
            "status": "not_started",
            "since_ts": None,
            "counts": {record_type: 0 for record_type in empty},
            "rule": "only records explicitly stamped for the active stage count",
        }

    since: datetime | None = None
    if since_ts:
        try:
            since = datetime.fromisoformat(str(since_ts).replace("Z", "+00:00"))
            if since.tzinfo is None:
                since = since.replace(tzinfo=timezone.utc)
        except Exception:
            since = None

    selected: dict[str, list[dict]] = {}
    for record_type in empty:
        rows: list[dict] = []
        for row in list(evidence.get(record_type) or []):
            if _record_stage(row) != requested_stage.value:
                continue
            row_ts = _record_timestamp(row)
            if since is not None and (row_ts is None or row_ts < since):
                continue
            rows.append(row)
        selected[record_type] = rows

    counts = {record_type: len(rows) for record_type, rows in selected.items()}
    return selected, {
        "stage": requested_stage.value,
        "current_stage": current_stage.value,
        "status": "active" if any(counts.values()) else "active_no_evidence",
        "since_ts": since_ts,
        "counts": counts,
        "rule": "only records explicitly stamped for the active stage count",
    }


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def _validate_schema(records: list[dict], required_fields: list[str],
                     record_type: str) -> dict:
    """Check that all records contain all required fields.

    This validates schema shape, not semantic completeness. A field that is
    present with a null value still satisfies the contract for this checker.
    """
    if not records:
        return {"ok": None, "total": 0, "missing_fields": [], "bad_records": 0,
                "note": f"no {record_type} records found"}
    missing_by_field: dict[str, int] = {}
    for r in records:
        for f in required_fields:
            if f not in r:
                missing_by_field[f] = missing_by_field.get(f, 0) + 1
    bad = sum(1 for r in records if any(f not in r for f in required_fields))
    ok = len(missing_by_field) == 0
    return {
        "ok": ok,
        "total": len(records),
        "bad_records": bad,
        "missing_fields": [
            {"field": f, "missing_in": n} for f, n in missing_by_field.items()
        ],
        "note": "all records valid" if ok else f"{bad}/{len(records)} records missing fields",
    }


def _validate_evidence_schema(
    evidence: dict[str, list[dict]],
    cfg: dict,
) -> dict[str, dict]:
    """Validate the supplied evidence scope against config requirements."""
    ev = cfg.get("evidence", {})
    return {
        "signal":   _validate_schema(evidence["signal"],   ev.get("required_signal_fields", []),   "signal"),
        "order":    _validate_schema(evidence["order"],    ev.get("required_order_fields", []),    "order"),
        "fill":     _validate_schema(evidence["fill"],     ev.get("required_fill_fields", []),     "fill"),
        "session":  _validate_schema(evidence["session"],  ev.get("required_session_fields", []),  "session"),
        "drawdown": _validate_schema(evidence["drawdown"], ev.get("required_drawdown_fields", []), "drawdown"),
    }


def _run_schema_validation(ev_dir: Path, cfg: dict) -> dict[str, dict]:
    """Validate all evidence log schemas against config requirements."""
    return _validate_evidence_schema(_load_all_evidence(ev_dir), cfg)


# ---------------------------------------------------------------------------
# Provenance validation
# ---------------------------------------------------------------------------

def _evidence_provenance_summary(evidence: dict[str, list[dict]]) -> dict:
    """Summarize whether promotion evidence is attributable to public market data."""
    by_type: dict[str, dict] = {}
    totals = {"total": 0, "public": 0, "sample": 0, "missing": 0, "unknown": 0}
    total_unknown_sources: Counter[str] = Counter()
    for record_type in ("signal", "order", "fill", "session"):
        rows = evidence.get(record_type, []) or []
        counts = {"total": len(rows), "public": 0, "sample": 0, "missing": 0, "unknown": 0}
        unknown_sources: Counter[str] = Counter()
        for row in rows:
            source = str(row.get("market_data_source") or "").strip().lower()
            raw_sample_mode = row.get("ohlcv_sample_mode")
            sample_mode = (
                raw_sample_mode is True
                or str(raw_sample_mode).strip().lower() in {"1", "true", "yes", "on"}
            )
            if not source:
                counts["missing"] += 1
            elif source == "sample_ohlcv" or sample_mode:
                counts["sample"] += 1
            elif source in {"public_ohlcv", "live_market", "exchange", "local_snapshot"}:
                counts["public"] += 1
            else:
                counts["unknown"] += 1
                unknown_sources[source] += 1
                total_unknown_sources[source] += 1
        counts["unknown_sources"] = dict(sorted(unknown_sources.items()))
        by_type[record_type] = counts
        for key in totals:
            totals[key] += counts[key]

    ok = (
        True
        if totals["total"] > 0
        and totals["missing"] == 0
        and totals["sample"] == 0
        and totals["unknown"] == 0
        else False
    )
    if totals["total"] == 0:
        ok = None
    return {
        "ok": ok,
        **totals,
        "unknown_sources": dict(sorted(total_unknown_sources.items())),
        "by_type": by_type,
    }


def _provenance_gate_detail(provenance: dict) -> str:
    detail = (
        f"window:{provenance.get('window_date') or 'all'} "
        f"public:{provenance['public']} missing:{provenance['missing']} "
        f"sample:{provenance['sample']} unknown:{provenance['unknown']}"
    )
    unknown_sources = dict(provenance.get("unknown_sources") or {})
    if unknown_sources:
        parts = [f"{source}={count}" for source, count in sorted(unknown_sources.items())]
        detail += f" unknown_sources:{','.join(parts)}"
    return detail


def _record_date(row: dict) -> str | None:
    ts = row.get("timestamp") or row.get("date") or row.get("session_start")
    if not ts:
        return None
    try:
        return datetime.fromisoformat(str(ts).replace("Z", "+00:00")).date().isoformat()
    except Exception:
        return None


def _latest_evidence_date(evidence: dict[str, list[dict]]) -> str | None:
    dates = []
    for record_type in ("signal", "order", "fill", "session"):
        for row in list(evidence.get(record_type) or []):
            date = _record_date(dict(row))
            if date:
                dates.append(date)
    return max(dates) if dates else None


def _filter_evidence_by_date(evidence: dict[str, list[dict]], date: str) -> dict[str, list[dict]]:
    return {
        record_type: [
            dict(row)
            for row in list(evidence.get(record_type) or [])
            if _record_date(dict(row)) == date
        ]
        for record_type in ("signal", "order", "fill", "session", "drawdown")
    }


def _promotion_provenance_summary(evidence: dict[str, list[dict]]) -> dict:
    """Evaluate provenance over the latest dated evidence window."""
    latest_date = _latest_evidence_date(evidence)
    if not latest_date:
        out = _evidence_provenance_summary(evidence)
        out["window_date"] = None
        out["window"] = "all_time"
        return out
    out = _evidence_provenance_summary(_filter_evidence_by_date(evidence, latest_date))
    out["window_date"] = latest_date
    out["window"] = "latest_date"
    return out


def _latest_session_health(sessions: list[dict]) -> dict:
    dated = [
        (date, dict(row))
        for row in list(sessions or [])
        if (date := _record_date(dict(row)))
    ]
    if not dated:
        return {
            "ok": None,
            "window_date": None,
            "critical_error_count": 0,
            "detail": "no session logs found",
            "hint": "check logs/errors manually",
        }
    latest_date = max(date for date, _row in dated)
    window_rows = [row for date, row in dated if date == latest_date]
    critical = [row for row in window_rows if bool(row.get("critical_error"))]
    if critical:
        return {
            "ok": False,
            "window_date": latest_date,
            "critical_error_count": len(critical),
            "detail": f"{len(critical)} critical_error session log(s) found in window:{latest_date}",
            "hint": "investigate latest session errors before promotion",
        }
    return {
        "ok": True,
        "window_date": latest_date,
        "critical_error_count": 0,
        "detail": f"0 critical_error session logs in window:{latest_date}",
        "hint": "",
    }


def _latest_evidence_log_presence(evidence: dict[str, list[dict]]) -> dict:
    latest_date = _latest_evidence_date(evidence)
    if not latest_date:
        return {
            "ok": False,
            "window_date": None,
            "counts": {"signal": 0, "order": 0, "fill": 0, "session": 0},
            "trade_evidence_expected": False,
            "no_trade_window": False,
            "detail": "window:all signal:0 order:0 fill:0 session:0",
            "hint": "start running to generate evidence",
        }
    window = _filter_evidence_by_date(evidence, latest_date)
    counts = {
        record_type: len(window.get(record_type) or [])
        for record_type in ("signal", "order", "fill", "session")
    }
    trade_evidence_expected = counts["order"] > 0 or counts["fill"] > 0
    core_ok = counts["signal"] > 0 and counts["session"] > 0
    trade_ok = counts["order"] > 0 and counts["fill"] > 0 if trade_evidence_expected else True
    ok = bool(core_ok and trade_ok)
    no_trade_window = bool(core_ok and not trade_evidence_expected)
    if ok:
        hint = ""
    elif not core_ok:
        hint = "start running to generate signal and session evidence"
    else:
        hint = "order/fill evidence is incomplete for latest trade window"
    return {
        "ok": ok,
        "window_date": latest_date,
        "counts": counts,
        "trade_evidence_expected": trade_evidence_expected,
        "no_trade_window": no_trade_window,
        "detail": (
            f"window:{latest_date} signal:{counts['signal']} order:{counts['order']} "
            f"fill:{counts['fill']} session:{counts['session']}"
            f"{' no_trade_window:true' if no_trade_window else ''}"
        ),
        "hint": hint,
    }


def _evidence_writer_status() -> dict:
    try:
        from services.strategies.evidence_logger import load_evidence_writer_status
        status = load_evidence_writer_status()
        return dict(status) if isinstance(status, dict) else {}
    except Exception as exc:
        return {
            "ok": False,
            "evidence_writer_status": "degraded",
            "evidence_write_failures_total": 0,
            "evidence_write_failures_consecutive": 0,
            "last_evidence_write_error_type": type(exc).__name__,
            "last_evidence_write_error_ts": datetime.now(timezone.utc).isoformat(),
            "last_successful_evidence_write_ts": "",
            "evidence_refusal_reason": "evidence writer status unavailable",
            "threshold": 0,
            "updated_ts": datetime.now(timezone.utc).isoformat(),
        }


def _evidence_writer_gate(status: dict) -> dict:
    writer_status = str(status.get("evidence_writer_status") or "ok").strip().lower()
    consecutive = int(status.get("evidence_write_failures_consecutive") or 0)
    total = int(status.get("evidence_write_failures_total") or 0)
    threshold = int(status.get("threshold") or 0)
    last_error = str(status.get("last_evidence_write_error_type") or "")
    detail = (
        f"status:{writer_status or 'ok'} consecutive:{consecutive}/{threshold} "
        f"total:{total}"
    )
    if last_error:
        detail += f" last_error:{last_error}"
    refusing = writer_status == "refusing"
    return _gate(
        "Evidence writer accepting records",
        False if refusing else True,
        detail,
        str(status.get("evidence_refusal_reason") or "recover evidence writer before promotion"),
    )


# ---------------------------------------------------------------------------
# Gate evaluation
# ---------------------------------------------------------------------------

def _gate(label: str, passed: bool | None, detail: str = "", hint: str = "") -> dict:
    return {
        "label":  label,
        "passed": passed,   # True=PASS, False=FAIL, None=UNKNOWN
        "detail": detail,
        "hint":   "" if passed is True else hint,
    }


def evaluate_paper_gates(
    evidence: dict,
    sessions: list,
    signals: list,
    fills: list,
    paper_history: dict | None = None,
    cfg: dict | None = None,
) -> list[dict]:
    resolved_cfg = cfg
    if resolved_cfg is None:
        resolved_cfg = yaml.safe_load(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    policy = resolve_paper_promotion_policy(resolved_cfg or {})
    bar_summary = count_qualified_signal_bars(
        [dict(row) for row in list(signals or []) if isinstance(row, dict)],
        config=resolved_cfg or {},
    )
    min_days = int(policy.min_calendar_days)
    min_trips = int(policy.min_qualified_round_trips)
    days  = _days_of_operation(sessions)
    trade_metrics = _paper_gate_trade_metrics(fills, paper_history)
    trips = int(trade_metrics["round_trips"])
    days_remaining = max(0, min_days - days)
    trips_remaining = max(0, min_trips - trips)
    provenance = _promotion_provenance_summary(evidence)
    session_health = _latest_session_health(sessions)
    kill_switch = _kill_switch_test_status(sessions, resolved_cfg or {})
    evidence_logs = _latest_evidence_log_presence(evidence)

    gates = []
    if policy.policy_id != "legacy_round_trip_v1" or not policy.valid:
        gates.append(
            _gate("Paper promotion policy valid",
                  policy.valid,
                  f"{policy.policy_id}: {', '.join(policy.invalid_reasons) if policy.invalid_reasons else 'valid'}",
                  "fix promotion.paper.policy before promotion" if not policy.valid else "")
        )
    gates.extend([
        _gate(f"{min_days} calendar days of operation",
              days >= min_days if days > 0 else None,
              f"{days}/{min_days} days recorded ({days_remaining} remaining)",
              "run the paper runner daily" if days < min_days else ""),
        _gate(f"{min_trips}+ completed round trips",
              trips >= min_trips if trips > 0 else None,
              f"{trade_metrics['round_trip_detail']} ({trips}/{min_trips}, {trips_remaining} remaining)",
              "continue running" if trips < min_trips else ""),
        _gate("Expectancy within tolerable range of backtest",
              trade_metrics["expectancy_ok"],
              str(trade_metrics["expectancy_detail"]),
              str(trade_metrics["expectancy_hint"])),
        _gate("No critical operational bugs",
              session_health["ok"],
              str(session_health["detail"]),
              str(session_health["hint"])),
        _gate("Kill switch tested",
              kill_switch["ok"],
              str(kill_switch["detail"]),
              str(kill_switch["hint"])),
        _gate("All evidence logs present",
              evidence_logs["ok"],
              str(evidence_logs["detail"]),
              str(evidence_logs["hint"])),
        _gate("Promotion evidence has non-sample provenance",
              provenance["ok"],
              _provenance_gate_detail(provenance),
              "collect fresh public-market evidence with provenance before promotion"),
        *(
            [
                _gate(
                    f"{int(bar_summary.get('qualified_bars_required') or 0)}+ qualified source bars",
                    bool(bar_summary.get("qualified_bars_ready")),
                    (
                        f"{int(bar_summary.get('qualified_bars_recorded') or 0)}/"
                        f"{int(bar_summary.get('qualified_bars_required') or 0)} "
                        f"qualified source bars "
                        f"({int(bar_summary.get('qualified_bars_remaining') or 0)} remaining; "
                        f"source={bar_summary.get('bar_count_source')})"
                    ),
                    "continue collecting provenance-qualified source bars",
                )
            ]
            if bool(bar_summary.get("enabled"))
            else []
        ),
        _gate("Daily loss halt tested in simulation",
              _halt_tested(sessions) if sessions else None,
              "halt test found" if _halt_tested(sessions) else "not found in session logs",
              "set daily_loss_halt_pct to 0.001 temporarily, verify halt fires"),
        _gate("Regime filter blocked at least one entry",
              _any_regime_block(signals) if signals else None,
              "regime block found in signal logs" if _any_regime_block(signals) else "no chop/high_vol block recorded",
              "wait for a chop/high-vol period, or simulate one"),
    ])
    return gates


def evaluate_shadow_gates(evidence: dict, sessions: list,
                           signals: list, fills: list) -> list[dict]:
    days  = _days_of_operation(sessions)
    spread_count = sum(1 for signal in signals if _signal_has_spread_or_depth(signal))
    ops_pass_count = sum(1 for session in sessions if session.get("ops_checks_passed") is True)
    recovery_count = sum(1 for session in sessions if session.get("recovery_tested") is True)
    return [
        _gate("20+ trading days on live data",
              days >= 20 if days > 0 else None,
              f"{days}/20 shadow trading days",
              "start shadow stage to collect live-data sessions" if days == 0 else "continue running shadow sessions"),
        _gate("All signals logged with spread/depth data",
              all(_signal_has_spread_or_depth(s) for s in signals) if signals else None,
              f"{spread_count}/{len(signals)} shadow signals include spread/depth",
              "start shadow stage to collect market-quality evidence" if not signals
              else "add spread/depth fields to every shadow signal"),
        _gate("Slippage within 1.5× backtest estimate",
              None,
              (
                  f"manual check required across {len(fills)} shadow fill records"
                  if fills
                  else "no shadow fill/slippage evidence recorded"
              ),
              "collect shadow would-be-fill slippage evidence before manual comparison"),
        _gate("All ops integrity checks passing consistently",
              all(s.get("ops_checks_passed") is True for s in sessions) if sessions else None,
              f"{ops_pass_count}/{len(sessions)} shadow sessions passed ops checks",
              "start shadow stage to collect session integrity evidence" if not sessions
              else "investigate shadow sessions without ops_checks_passed=True"),
        _gate("Recovery rule exercised (restart + state validation)",
              any(s.get("recovery_tested") for s in sessions) if sessions else None,
              f"{recovery_count} shadow recovery proof record(s)",
              "after shadow starts, perform a deliberate restart and record recovery_tested=True"),
    ]


def _signal_has_spread_or_depth(signal: dict) -> bool:
    if not isinstance(signal, dict):
        return False
    spread_keys = {"spread", "spread_bps", "market_spread_bps"}
    depth_keys = {
        "depth",
        "depth_bid_notional",
        "depth_ask_notional",
        "market_depth",
        "market_bid_depth",
        "market_ask_depth",
    }
    return any(key in signal for key in spread_keys | depth_keys)


def evaluate_capped_live_gates(evidence: dict, sessions: list,
                                fills: list) -> list[dict]:
    trips = _count_round_trips(fills)
    weeks = _weeks_at_stage(Stage.CAPPED_LIVE)
    exp_ok, exp_val = _check_expectancy(fills)
    return [
        _gate("Position size at 25% of intended",
              True,  # enforced in code — see decide() stage cap
              "enforced by code: capped_live → max 1 contract"),
        _gate("20+ completed live round trips",
              trips >= 20 if trips > 0 else None,
              f"{trips} round trips", "continue running"),
        _gate("8+ weeks at capped live stage",
              (weeks >= 8) if weeks is not None else None,
              f"{weeks:.1f} weeks" if weeks else "unknown",
              "low-frequency system — time gate is binding, not trade count"),
        _gate("Expectancy holding within range of shadow",
              exp_ok,
              f"avg pnl/trade = ${exp_val:.2f}" if exp_val is not None else "insufficient data",
              "need 10+ fills with pnl_usd"),
        _gate("No operational halts from infra failures",
              all(not s.get("infra_halt") for s in sessions) if sessions else None,
              "no infra_halt flags found" if sessions else "no sessions",
              "check halt logs"),
        _gate("All evidence logs complete",
              all(len(v) > 0 for v in evidence.values()),
              f"signal:{len(evidence['signal'])} fill:{len(fills)}",
              "start collecting evidence"),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _slippage_within_baseline(fills: list[dict], multiplier: float = 1.5) -> dict:
    """Compare observed fill slippage to baseline from config."""
    if not fills:
        return {"ok": None, "note": "no fills recorded", "observed_p95": None, "baseline": None}
    
    slippages = [abs(float(f.get("slippage_pct") or 0)) for f in fills
                 if f.get("slippage_pct") is not None]
    if len(slippages) < 5:
        return {"ok": None, "note": f"only {len(slippages)} fills with slippage data (need 5+)",
                "observed_p95": None, "baseline": None}
    
    slippages.sort()
    p95_idx = int(len(slippages) * 0.95)
    observed_p95 = slippages[min(p95_idx, len(slippages)-1)]
    
    # Baseline from config — use the warn threshold as reference
    cfg = yaml.safe_load(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    warn_mult = float(cfg.get("ops", {}).get("slippage_warn_multiplier", 1.5))
    
    # Without a measured backtest baseline, we use 0.1% as a reasonable starting reference
    # This should be replaced with actual backtest slippage once measured
    baseline = float(cfg.get("ops", {}).get("baseline_slippage_pct", 0.10))
    
    ok = observed_p95 <= baseline * warn_mult
    return {
        "ok": ok,
        "observed_p95": round(observed_p95, 4),
        "baseline": baseline,
        "warn_threshold": round(baseline * warn_mult, 4),
        "note": f"p95={observed_p95:.3f}% vs warn={baseline*warn_mult:.3f}%"
    }


def _check_retirement_triggers(
    fills: list[dict],
    sessions: list[dict],
    paper_history: dict | None = None,
) -> dict:
    """Check retirement conditions. Delegates to service layer."""
    from services.control.retirement_checker import check_retirement_triggers
    cfg = yaml.safe_load(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    r = cfg.get("retirement", {})
    max_drawdown_pct = float(r.get("max_drawdown_pct", 12.0))
    rolling_window = int(r.get("rolling_expectancy_window_days", 60))
    jsonl_result = check_retirement_triggers(
        fills, sessions,
        max_drawdown_pct=max_drawdown_pct,
        rolling_window=rolling_window,
    )
    history = dict(paper_history or {})
    if history.get("qualification") is None and (
        history.get("ok") is not True or int(history.get("fills") or 0) <= 0
    ):
        jsonl_result["source"] = "jsonl_evidence"
        return jsonl_result

    triggers = []
    fill_count = int(history.get("fills") or 0)
    expectancy = float(history.get("expectancy_per_closed_trade") or 0.0)
    if fill_count >= 10 and expectancy < 0:
        triggers.append(f"rolling_expectancy_negative:avg={expectancy:.2f}")

    actual_dd = max(
        (float(s.get("drawdown_from_peak") or 0) for s in sessions),
        default=0.0,
    )
    if actual_dd > max_drawdown_pct:
        triggers.append(f"drawdown_exceeded:{actual_dd:.1f}%>{max_drawdown_pct:.1f}%")

    return {
        "triggers_fired": triggers,
        "retirement_required": len(triggers) >= 2,
        "single_trigger_review": len(triggers) == 1,
        "note": f"{len(triggers)} retirement trigger(s) active",
        "source": str(history.get("source") or "trade_journal_sqlite"),
        "jsonl_comparison": jsonl_result,
    }


def _gate_by_label(gates: list[dict], label: str) -> dict:
    return next((dict(item) for item in list(gates or []) if str(item.get("label") or "") == label), {})


def _optional_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _backtest_expectations(cfg: dict) -> dict:
    promotion = cfg.get("promotion") or {}
    paper = promotion.get("paper") or {}
    expectations = paper.get("backtest_expectations") or {}
    return expectations if isinstance(expectations, dict) else {}


def _relative_bounds(expected: float, tolerance_pct: float) -> tuple[float, float]:
    factor = abs(float(tolerance_pct)) / 100.0
    low = expected * (1.0 - factor)
    high = expected * (1.0 + factor)
    return (min(low, high), max(low, high))


def _paper_backtest_expectation_item(paper_history: dict | None, cfg: dict) -> dict:
    history = dict(paper_history or {})
    expectations = _backtest_expectations(cfg)
    tolerance_pct = _optional_float(expectations.get("tolerance_pct"))
    if tolerance_pct is None:
        tolerance_pct = 25.0

    metric_basis = str(expectations.get("metric_basis") or "quote_pnl").strip().lower()
    metrics = (
        ("win_rate", "avg_win_return_pct", "avg_loss_return_pct")
        if metric_basis == "net_return_pct"
        else ("win_rate", "avg_win", "avg_loss")
    )
    comparison_label = (
        "Observed win rate and average winning/losing trade returns within 25% of backtest expectations"
        if metric_basis == "net_return_pct"
        else "Observed win rate and avg win/loss within 25% of backtest expectations"
    )
    observed = {
        "closed_trades": int(history.get("closed_trades") or 0),
        "fills": int(history.get("fills") or 0),
        "win_rate": history.get("win_rate"),
        "avg_win": history.get("avg_win"),
        "avg_loss": history.get("avg_loss"),
        "avg_win_return_pct": history.get("avg_win_return_pct"),
        "avg_loss_return_pct": history.get("avg_loss_return_pct"),
        "expectancy_return_pct": history.get("expectancy_return_pct"),
        "net_realized_pnl": history.get("net_realized_pnl"),
        "expectancy_per_closed_trade": history.get("expectancy_per_closed_trade"),
    }
    expected_values = {metric: _optional_float(expectations.get(metric)) for metric in metrics}
    missing = [metric for metric, value in expected_values.items() if value is None]
    if missing:
        return {
            "id": "win_rate_avg_win_loss_vs_backtest",
            "label": comparison_label,
            "status": "manual_required",
            "reason": (
                "No complete machine-readable backtest baseline is configured for "
                f"{', '.join(missing)}, so this spec item requires operator review before promotion."
            ),
            "baseline": {
                "source": expectations.get("source"),
                "metric_basis": metric_basis,
                "tolerance_pct": tolerance_pct,
                "missing_metrics": missing,
            },
            "observed": observed,
        }

    comparisons = []
    failed = []
    for metric in metrics:
        observed_value = _optional_float(history.get(metric))
        expected_value = expected_values[metric]
        if observed_value is None or expected_value is None:
            failed.append(metric)
            comparisons.append(
                {
                    "metric": metric,
                    "observed": observed_value,
                    "expected": expected_value,
                    "passed": False,
                    "reason": "missing observed or expected value",
                }
            )
            continue
        lower, upper = _relative_bounds(expected_value, tolerance_pct)
        passed = lower <= observed_value <= upper
        if not passed:
            failed.append(metric)
        comparisons.append(
            {
                "metric": metric,
                "observed": observed_value,
                "expected": expected_value,
                "tolerance_pct": tolerance_pct,
                "lower_bound": lower,
                "upper_bound": upper,
                "passed": passed,
            }
        )

    status = "machine_checked" if not failed else "machine_blocking"
    return {
        "id": "win_rate_avg_win_loss_vs_backtest",
        "label": comparison_label,
        "status": status,
        "reason": (
            "Observed paper metrics are within configured backtest tolerance."
            if status == "machine_checked"
            else f"Observed paper metrics are outside configured tolerance for: {', '.join(failed)}."
        ),
        "baseline": {
            "source": expectations.get("source"),
            "metric_basis": metric_basis,
            "tolerance_pct": tolerance_pct,
            "metrics": expected_values,
        },
        "observed": observed,
        "comparisons": comparisons,
    }


def _paper_manual_review_status(paper_history: dict | None, gates: list[dict], cfg: dict | None = None) -> dict:
    """Surface spec checklist items that are not fully machine-verifiable."""
    cfg = dict(cfg or {})
    items: list[dict] = [_paper_backtest_expectation_item(paper_history, cfg)]
    daily_loss_halt = _gate_by_label(gates, "Daily loss halt tested in simulation")
    regime_block = _gate_by_label(gates, "Regime filter blocked at least one entry")
    if daily_loss_halt:
        items.append(
            {
                "id": "daily_loss_halt_simulation",
                "label": "Daily loss halt triggered and recovered correctly at least once in simulation",
                "status": "machine_checked" if daily_loss_halt.get("passed") is True else "machine_blocking",
                "detail": str(daily_loss_halt.get("detail") or ""),
                "hint": str(daily_loss_halt.get("hint") or ""),
            }
        )
    if regime_block:
        items.append(
            {
                "id": "regime_filter_blocked_entry",
                "label": "Regime filter blocked at least one entry in the run",
                "status": "machine_checked" if regime_block.get("passed") is True else "machine_blocking",
                "detail": str(regime_block.get("detail") or ""),
                "hint": str(regime_block.get("hint") or ""),
            }
        )

    required = any(str(item.get("status") or "") in {"manual_required", "machine_blocking"} for item in items)
    return {
        "required": required,
        "items": items,
        "outstanding_items": [
            dict(item)
            for item in items
            if str(item.get("status") or "") in {"manual_required", "machine_blocking"}
        ],
        "summary": (
            "Paper gate review required: observed win rate and average winning/losing trade metrics must satisfy "
            "configured backtest expectations before paper promotion."
            if required
            else "No manual paper-gate review items are outstanding."
        ),
    }



def run_check(stage_override: str | None = None) -> dict:
    if not CONFIG_PATH.exists():
        return {"error": f"config not found: {CONFIG_PATH}", "ready": False}

    cfg     = yaml.safe_load(CONFIG_PATH.read_text())
    current_stage = get_current_stage(STRATEGY_ID)
    stage   = Stage(stage_override) if stage_override else current_stage
    current_stage_summary = stage_summary(STRATEGY_ID)
    ev_dir  = _evidence_dir()
    evidence = _load_all_evidence(ev_dir)
    sessions = evidence["session"]
    signals  = evidence["signal"]
    fills    = evidence["fill"]
    paper_history = _paper_history_gate_summary(cfg, fills)
    paper_policy = resolve_paper_promotion_policy(cfg)
    paper_bar_summary = count_qualified_signal_bars(signals, config=cfg)
    gate_evidence = evidence
    gate_sessions = sessions
    gate_fills = fills
    retirement_history = paper_history

    # Gate evaluation for current stage
    if stage == Stage.PAPER:
        gates = evaluate_paper_gates(evidence, sessions, signals, fills, paper_history, cfg)
        evidence_scope = {
            "stage": stage.value,
            "current_stage": current_stage.value,
            "status": "all_paper_evidence",
            "since_ts": current_stage_summary.get("since_ts") if current_stage == Stage.PAPER else None,
            "counts": {record_type: len(evidence.get(record_type) or []) for record_type in evidence},
            "rule": "paper gate retains its existing evidence qualification rules",
        }
    elif stage == Stage.SHADOW:
        scoped_evidence, evidence_scope = _active_stage_evidence(
            evidence,
            requested_stage=Stage.SHADOW,
            current_stage=current_stage,
            since_ts=current_stage_summary.get("since_ts"),
        )
        gate_evidence = scoped_evidence
        gate_sessions = scoped_evidence["session"]
        gate_fills = scoped_evidence["fill"]
        retirement_history = None
        gates = evaluate_shadow_gates(
            scoped_evidence,
            gate_sessions,
            scoped_evidence["signal"],
            gate_fills,
        )
    elif stage == Stage.CAPPED_LIVE:
        gates = evaluate_capped_live_gates(evidence, sessions, fills)
        evidence_scope = {
            "stage": stage.value,
            "current_stage": current_stage.value,
            "status": "legacy_all_evidence",
            "since_ts": None,
            "counts": {record_type: len(evidence.get(record_type) or []) for record_type in evidence},
            "rule": "capped-live scoping is unchanged by this patch",
        }
    else:
        gates = [{"label": "No promotion gate for this stage", "passed": True,
                  "detail": str(stage.value), "hint": ""}]
        evidence_scope = {
            "stage": stage.value,
            "current_stage": current_stage.value,
            "status": "not_applicable",
            "since_ts": None,
            "counts": {},
            "rule": "no gate evidence scope is defined for this stage",
        }

    evidence_writer = _evidence_writer_status()
    gates.append(_evidence_writer_gate(evidence_writer))

    schema = _validate_evidence_schema(gate_evidence, cfg)
    passed  = [g for g in gates if g["passed"] is True]
    failed  = [g for g in gates if g["passed"] is False]
    unknown = [g for g in gates if g["passed"] is None]

    schema_ok = all(v.get("ok") is not False for v in schema.values())
    provenance = _promotion_provenance_summary(gate_evidence)
    provenance_all_time = _evidence_provenance_summary(evidence)

    slippage_check = _slippage_within_baseline(gate_fills)
    retirement = _check_retirement_triggers(
        gate_fills,
        gate_sessions,
        retirement_history,
    )

    # Retirement check overrides "ready" regardless of gates
    retirement_block = retirement["retirement_required"]
    manual_review = _paper_manual_review_status(paper_history, gates, cfg) if stage == Stage.PAPER else {
        "required": False,
        "items": [],
        "outstanding_items": [],
        "summary": "No manual review items defined for this stage.",
    }
    machine_ready = len(failed) == 0 and len(unknown) == 0 and schema_ok and not retirement_block

    return {
        "strategy_id": STRATEGY_ID,
        "stage":       stage.value,
        "current_stage": current_stage.value,
        "stage_override": stage_override,
        "evidence_scope": evidence_scope,
        "ready":       machine_ready and not bool(manual_review.get("required")),
        "machine_ready": machine_ready,
        "manual_review_required": bool(manual_review.get("required")),
        "manual_review": manual_review,
        "summary": {
            "pass":    len(passed),
            "fail":    len(failed),
            "unknown": len(unknown),
            "total":   len(gates),
        },
        "gates":        gates,
        "schema":       schema,
        "evidence_writer": evidence_writer,
        "paper_history": paper_history,
        "paper_progress": (
            _paper_progress_summary(
                paper_history,
                policy=paper_policy,
                bar_summary=paper_bar_summary,
            )
            if stage == Stage.PAPER
            else None
        ),
        "provenance":   provenance,
        "provenance_all_time": provenance_all_time,
        "slippage":     slippage_check,
        "retirement":   retirement,
        "cognitive_budget": budget_summary(STRATEGY_ID),
    }


def print_report(result: dict) -> None:
    stage = result.get("stage", "?")
    ready = result.get("ready", False)
    s     = result.get("summary", {})

    print(f"\n=== Promotion Gate Check — {STRATEGY_ID} ({stage}) ===")
    print("Spec: docs/strategies/es_daily_trend_v1.md §6\n")

    for g in result.get("gates", []):
        icon = "✅" if g["passed"] is True else "❌" if g["passed"] is False else "⬜"
        print(f"  {icon}  {g['label']}")
        if g.get("detail"):
            print(f"       {g['detail']}")
        if g.get("hint") and g["passed"] is not True:
            print(f"       → {g['hint']}")

    print("\nSchema validation:")
    for record_type, v in result.get("schema", {}).items():
        icon = "✅" if v.get("ok") is True else "❌" if v.get("ok") is False else "⬜"
        print(f"  {icon}  {record_type}: {v.get('note', '')}")

    budget = result.get("cognitive_budget", {})
    print(f"\nCognitive budget: {budget.get('alert_count', 0)}/4 alerts")
    if budget.get("breach"):
        print(f"  ⚠️  BREACH: {budget.get('breaches', [])}")

    manual_review = dict(result.get("manual_review") or {})
    if bool(result.get("manual_review_required")):
        print(f"\nManual review required: {manual_review.get('summary', '')}")
        for item in list(manual_review.get("outstanding_items") or []):
            print(f"  - {item.get('label')}: {item.get('status')}")

    print(f"\nResult: {'✅ READY TO PROMOTE' if ready else '🔴 NOT READY'}")
    print(f"  {s.get('pass', 0)} pass / {s.get('fail', 0)} fail / {s.get('unknown', 0)} unknown\n")
    if ready:
        print(f"  Next: python scripts/show_control_kernel_status.py --promote {STRATEGY_ID}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Promotion gate checker for es_daily_trend_v1")
    ap.add_argument("--stage",  type=str, default=None,
                    help="Override stage (paper|shadow|capped_live)")
    ap.add_argument("--json",   action="store_true", help="Output JSON")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 1 if any gate fails or is unknown")
    ap.add_argument(
        "--alert",
        action="store_true",
        help="Dispatch alerts on gate flips vs the previous persisted snapshot (best-effort)",
    )
    args = ap.parse_args()

    result = run_check(stage_override=args.stage)

    try:  # notification-only; never affects gate results or exit codes
        from datetime import datetime, timezone

        from services.alerts.paper_gate_events import record_gate_result_and_alert

        record_gate_result_and_alert(
            result,
            alert=args.alert,
            now_iso=datetime.now(timezone.utc).isoformat(),
        )
    except Exception:
        pass

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print_report(result)

    if args.strict:
        return 0 if result["ready"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
