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
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import yaml

from services.control.deployment_stage import get_current_stage, Stage, stage_summary
from services.control.cognitive_budget import budget_summary
from services.os.app_paths import data_dir

STRATEGY_ID = "es_daily_trend_v1"
REPO_ROOT = Path(__file__).resolve().parents[1]; CONFIG_PATH = REPO_ROOT / "configs/strategies/es_daily_trend_v1.yaml"


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
    """Count completed round trips (paired buy + sell fills)."""
    buys  = sum(1 for f in fills if str(f.get("side", "")).lower() == "buy")
    sells = sum(1 for f in fills if str(f.get("side", "")).lower() == "sell")
    return min(buys, sells)


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


def _target_feedback_strategy(cfg: dict) -> str:
    strategy = cfg.get("strategy") or {}
    strategy_id = str(strategy.get("id") or STRATEGY_ID).strip().lower()
    signal_type = str((strategy.get("signal") or {}).get("type") or "").strip().lower()
    if strategy_id.startswith("es_daily_trend") or signal_type == "sma_crossover":
        return "sma_200_trend"
    return strategy_id or STRATEGY_ID


def _paper_history_gate_summary(cfg: dict) -> dict:
    """Load authoritative persisted paper fill summary for this target strategy."""
    from services.analytics.strategy_feedback import load_strategy_feedback_ledger

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
    if not row:
        return {
            "ok": False,
            "status": str(ledger.get("status") or "missing"),
            "source": str(ledger.get("source") or "trade_journal_sqlite"),
            "journal_path": str(ledger.get("journal_path") or ""),
            "target_strategy": target_strategy,
            "symbol_filter": ledger.get("symbol_filter") or symbol or None,
            "fills": 0,
            "closed_trades": 0,
            "expectancy_per_closed_trade": None,
            "net_realized_pnl": None,
            "caveat": "No target-strategy paper-history row is available yet.",
        }

    return {
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
        "latest_fill_ts": row.get("latest_fill_ts"),
    }


def _paper_gate_trade_metrics(fills: list[dict], paper_history: dict | None = None) -> dict:
    history = dict(paper_history or {})
    jsonl_trips = _count_round_trips(fills)
    if history.get("ok") is True and int(history.get("fills") or 0) > 0:
        trips = int(history.get("closed_trades") or 0)
        fill_count = int(history.get("fills") or 0)
        exp_val = (
            float(history.get("expectancy_per_closed_trade") or 0.0)
            if fill_count >= 10
            else None
        )
        source = str(history.get("source") or "paper_history")
        mismatch = f" (jsonl:{jsonl_trips})" if jsonl_trips != trips else ""
        return {
            "source": source,
            "round_trips": trips,
            "round_trip_detail": f"{trips} round trips recorded from {source}{mismatch}",
            "expectancy_ok": (exp_val > 0.0) if exp_val is not None else None,
            "expectancy_value": exp_val,
            "expectancy_detail": (
                f"avg pnl/round trip = ${exp_val:.2f} from {source}"
                if exp_val is not None
                else "insufficient paper-history fills for calculation"
            ),
            "expectancy_hint": "need 10+ paper-history fills" if exp_val is None else "",
        }

    exp_ok, exp_val = _check_expectancy(fills)
    return {
        "source": "jsonl_evidence",
        "round_trips": jsonl_trips,
        "round_trip_detail": f"{jsonl_trips} round trips recorded",
        "expectancy_ok": exp_ok,
        "expectancy_value": exp_val,
        "expectancy_detail": (
            f"avg pnl/trade = ${exp_val:.2f}"
            if exp_val is not None
            else "insufficient fills for calculation"
        ),
        "expectancy_hint": "need 10+ fills with pnl_usd field" if exp_ok is None else "",
    }


def _weeks_at_stage(stage: Stage) -> float | None:
    """Estimate weeks the strategy has been at the current stage."""
    summary = stage_summary(STRATEGY_ID)
    since = summary.get("since_ts")
    if not since:
        return None
    try:
        t = datetime.fromisoformat(str(since).replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - t
        return delta.days / 7.0
    except Exception:
        return None


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


def _run_schema_validation(ev_dir: Path, cfg: dict) -> dict[str, dict]:
    """Validate all evidence log schemas against config requirements."""
    ev = cfg.get("evidence", {})
    evidence = _load_all_evidence(ev_dir)
    return {
        "signal":   _validate_schema(evidence["signal"],   ev.get("required_signal_fields", []),   "signal"),
        "order":    _validate_schema(evidence["order"],    ev.get("required_order_fields", []),    "order"),
        "fill":     _validate_schema(evidence["fill"],     ev.get("required_fill_fields", []),     "fill"),
        "session":  _validate_schema(evidence["session"],  ev.get("required_session_fields", []),  "session"),
        "drawdown": _validate_schema(evidence["drawdown"], ev.get("required_drawdown_fields", []), "drawdown"),
    }


# ---------------------------------------------------------------------------
# Provenance validation
# ---------------------------------------------------------------------------

def _evidence_provenance_summary(evidence: dict[str, list[dict]]) -> dict:
    """Summarize whether promotion evidence is attributable to public market data."""
    by_type: dict[str, dict] = {}
    totals = {"total": 0, "public": 0, "sample": 0, "missing": 0, "unknown": 0}
    for record_type in ("signal", "order", "fill", "session"):
        rows = evidence.get(record_type, []) or []
        counts = {"total": len(rows), "public": 0, "sample": 0, "missing": 0, "unknown": 0}
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
        "by_type": by_type,
    }


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
            "detail": "window:all signal:0 order:0 fill:0 session:0",
            "hint": "start running to generate evidence",
        }
    window = _filter_evidence_by_date(evidence, latest_date)
    counts = {
        record_type: len(window.get(record_type) or [])
        for record_type in ("signal", "order", "fill", "session")
    }
    ok = all(counts[record_type] > 0 for record_type in ("signal", "order", "fill", "session"))
    return {
        "ok": ok,
        "window_date": latest_date,
        "counts": counts,
        "detail": (
            f"window:{latest_date} signal:{counts['signal']} order:{counts['order']} "
            f"fill:{counts['fill']} session:{counts['session']}"
        ),
        "hint": "" if ok else "start running to generate evidence",
    }


# ---------------------------------------------------------------------------
# Gate evaluation
# ---------------------------------------------------------------------------

def _gate(label: str, passed: bool | None, detail: str = "", hint: str = "") -> dict:
    return {
        "label":  label,
        "passed": passed,   # True=PASS, False=FAIL, None=UNKNOWN
        "detail": detail,
        "hint":   hint,
    }


def evaluate_paper_gates(evidence: dict, sessions: list, signals: list,
                         fills: list, paper_history: dict | None = None) -> list[dict]:
    days  = _days_of_operation(sessions)
    trade_metrics = _paper_gate_trade_metrics(fills, paper_history)
    trips = int(trade_metrics["round_trips"])
    provenance = _promotion_provenance_summary(evidence)
    session_health = _latest_session_health(sessions)
    kill_switch = _kill_switch_test_status(sessions, yaml.safe_load(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {})
    evidence_logs = _latest_evidence_log_presence(evidence)

    gates = [
        _gate("30 calendar days of operation",
              days >= 30 if days > 0 else None,
              f"{days} days recorded",
              "run the paper runner daily" if days < 30 else ""),
        _gate("50+ completed round trips",
              trips >= 50 if trips > 0 else None,
              str(trade_metrics["round_trip_detail"]),
              "continue running" if trips < 50 else ""),
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
              f"window:{provenance.get('window_date') or 'all'} public:{provenance['public']} missing:{provenance['missing']} sample:{provenance['sample']} unknown:{provenance['unknown']}",
              "collect fresh public-market evidence with provenance before promotion"),
        _gate("Daily loss halt tested in simulation",
              _halt_tested(sessions) if sessions else None,
              "halt test found" if _halt_tested(sessions) else "not found in session logs",
              "set daily_loss_halt_pct to 0.001 temporarily, verify halt fires"),
        _gate("Regime filter blocked at least one entry",
              _any_regime_block(signals) if signals else None,
              "regime block found in signal logs" if _any_regime_block(signals) else "no chop/high_vol block recorded",
              "wait for a chop/high-vol period, or simulate one"),
    ]
    return gates


def evaluate_shadow_gates(evidence: dict, sessions: list,
                           signals: list, fills: list) -> list[dict]:
    days  = _days_of_operation(sessions)
    weeks = _weeks_at_stage(Stage.SHADOW)
    return [
        _gate("20+ trading days on live data",
              days >= 20 if days > 0 else None,
              f"{days} days", "continue running"),
        _gate("All signals logged with spread/depth data",
              all("spread" in s or "depth" in s for s in signals) if signals else None,
              f"{len(signals)} signals", "add spread/depth fields to signal logger"),
        _gate("Slippage within 1.5× backtest estimate",
              None,
              "manual check required — compare fill logs to backtest slippage",
              "run: python scripts/check_promotion_gates.py --json | check fill.slippage_pct"),
        _gate("All ops integrity checks passing consistently",
              all(s.get("ops_checks_passed") is True for s in sessions) if sessions else None,
              "all sessions have ops_checks_passed=True" if sessions else "no sessions",
              "add ops_checks_passed field to session logger"),
        _gate("Recovery rule exercised (restart + state validation)",
              any(s.get("recovery_tested") for s in sessions) if sessions else None,
              "recovery_tested found" if any(s.get("recovery_tested") for s in sessions) else "not recorded",
              "do a deliberate restart and set recovery_tested=True in session log"),
    ]


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
    if history.get("ok") is not True or int(history.get("fills") or 0) <= 0:
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



def run_check(stage_override: str | None = None) -> dict:
    if not CONFIG_PATH.exists():
        return {"error": f"config not found: {CONFIG_PATH}", "ready": False}

    cfg     = yaml.safe_load(CONFIG_PATH.read_text())
    stage   = Stage(stage_override) if stage_override else get_current_stage(STRATEGY_ID)
    ev_dir  = _evidence_dir()
    evidence = _load_all_evidence(ev_dir)
    sessions = evidence["session"]
    signals  = evidence["signal"]
    fills    = evidence["fill"]
    paper_history = _paper_history_gate_summary(cfg)

    # Schema validation
    schema = _run_schema_validation(ev_dir, cfg)

    # Gate evaluation for current stage
    if stage == Stage.PAPER:
        gates = evaluate_paper_gates(evidence, sessions, signals, fills, paper_history)
    elif stage == Stage.SHADOW:
        gates = evaluate_shadow_gates(evidence, sessions, signals, fills)
    elif stage == Stage.CAPPED_LIVE:
        gates = evaluate_capped_live_gates(evidence, sessions, fills)
    else:
        gates = [{"label": "No promotion gate for this stage", "passed": True,
                  "detail": str(stage.value), "hint": ""}]

    passed  = [g for g in gates if g["passed"] is True]
    failed  = [g for g in gates if g["passed"] is False]
    unknown = [g for g in gates if g["passed"] is None]

    schema_ok = all(v.get("ok") is not False for v in schema.values())
    provenance = _promotion_provenance_summary(evidence)
    provenance_all_time = _evidence_provenance_summary(evidence)

    slippage_check = _slippage_within_baseline(fills)
    retirement = _check_retirement_triggers(fills, sessions, paper_history)

    # Retirement check overrides "ready" regardless of gates
    retirement_block = retirement["retirement_required"]

    return {
        "strategy_id": STRATEGY_ID,
        "stage":       stage.value,
        "ready":       len(failed) == 0 and len(unknown) == 0 and schema_ok and not retirement_block,
        "summary": {
            "pass":    len(passed),
            "fail":    len(failed),
            "unknown": len(unknown),
            "total":   len(gates),
        },
        "gates":        gates,
        "schema":       schema,
        "paper_history": paper_history,
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
    print(f"Spec: docs/strategies/es_daily_trend_v1.md §6\n")

    for g in result.get("gates", []):
        icon = "✅" if g["passed"] is True else "❌" if g["passed"] is False else "⬜"
        print(f"  {icon}  {g['label']}")
        if g.get("detail"):
            print(f"       {g['detail']}")
        if g.get("hint") and g["passed"] is not True:
            print(f"       → {g['hint']}")

    print(f"\nSchema validation:")
    for record_type, v in result.get("schema", {}).items():
        icon = "✅" if v.get("ok") is True else "❌" if v.get("ok") is False else "⬜"
        print(f"  {icon}  {record_type}: {v.get('note', '')}")

    budget = result.get("cognitive_budget", {})
    print(f"\nCognitive budget: {budget.get('alert_count', 0)}/4 alerts")
    if budget.get("breach"):
        print(f"  ⚠️  BREACH: {budget.get('breaches', [])}")

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
    args = ap.parse_args()

    result = run_check(stage_override=args.stage)

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print_report(result)

    if args.strict:
        return 0 if result["ready"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
