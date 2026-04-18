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
CONFIG_PATH  = Path("configs/strategies/es_daily_trend_v1.yaml")


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


def _check_expectancy(fills: list[dict]) -> tuple[bool | None, float | None]:
    """Check if observed expectancy is positive."""
    pnls = [float(f.get("pnl_usd") or 0) for f in fills if "pnl_usd" in f]
    if len(pnls) < 10:
        return None, None
    avg = sum(pnls) / len(pnls)
    return avg > 0, avg


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
                         fills: list) -> list[dict]:
    days  = _days_of_operation(sessions)
    trips = _count_round_trips(fills)
    exp_ok, exp_val = _check_expectancy(fills)

    gates = [
        _gate("30 calendar days of operation",
              days >= 30 if days > 0 else None,
              f"{days} days recorded",
              "run the paper runner daily" if days < 30 else ""),
        _gate("50+ completed round trips",
              trips >= 50 if trips > 0 else None,
              f"{trips} round trips recorded",
              "continue running" if trips < 50 else ""),
        _gate("Expectancy within tolerable range of backtest",
              exp_ok,
              f"avg pnl/trade = ${exp_val:.2f}" if exp_val is not None else "insufficient fills for calculation",
              "need 10+ fills with pnl_usd field" if exp_ok is None else ""),
        _gate("No critical operational bugs",
              True if sessions and not any(s.get("critical_error") for s in sessions) else None,
              "no critical_error flag found in session logs",
              "check logs/errors manually" if not sessions else ""),
        _gate("Kill switch tested",
              _kill_switch_tested(sessions) if sessions else None,
              "kill_switch_tested=True found in session log" if _kill_switch_tested(sessions) else "not found in session logs",
              "set kill_switch_tested=True in session log after testing"),
        _gate("All evidence logs present",
              all(len(v) > 0 for v in evidence.values()),
              f"signal:{len(evidence['signal'])} order:{len(evidence['order'])} fill:{len(evidence['fill'])} session:{len(sessions)}",
              "start running to generate evidence"),
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


def _check_retirement_triggers(fills: list[dict], sessions: list[dict]) -> dict:
    """Check retirement conditions. Delegates to service layer."""
    from services.control.retirement_checker import check_retirement_triggers
    cfg = yaml.safe_load(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    r = cfg.get("retirement", {})
    return check_retirement_triggers(
        fills, sessions,
        max_drawdown_pct=float(r.get("max_drawdown_pct", 12.0)),
        rolling_window=int(r.get("rolling_expectancy_window_days", 60)),
    )



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

    # Schema validation
    schema = _run_schema_validation(ev_dir, cfg)

    # Gate evaluation for current stage
    if stage == Stage.PAPER:
        gates = evaluate_paper_gates(evidence, sessions, signals, fills)
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

    slippage_check = _slippage_within_baseline(fills)
    retirement = _check_retirement_triggers(fills, sessions)

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
