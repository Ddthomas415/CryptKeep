"""Bounded, read-only archive research. No fetch, trading or campaign authority."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.backtest.next_open_research import run_frozen_segment, simulate_next_open, validate_bars
from services.backtest.research_prefix_freeze import verify_prefix

CONTRACT = ROOT / "research/multisymbol_baseline_v1"
HOUR = 3600000


def utc_ms(value):
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()*1000)


def load_contract():
    raw = (CONTRACT/"plan.json").read_bytes()
    plan = json.loads(raw)
    frozen_raw = (CONTRACT/"strategies.snapshot.json").read_bytes()
    snapshot = json.loads(frozen_raw)
    if hashlib.sha256(raw).hexdigest() != snapshot["plan_sha256"]:
        raise ValueError("plan_changed_after_freeze")
    if set(snapshot["strategies"]) != set(plan["strategies"]):
        raise ValueError("snapshot_strategy_set_mismatch")
    for name, expected in snapshot["selected_source_sha256"].items():
        path = (ROOT/name).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("selected_source_changed_after_freeze")
    return plan, snapshot, hashlib.sha256(frozen_raw).hexdigest()


def read_rows(path, *, venue, symbol, start_ms, end_ms):
    """Read exactly one stored market; no normalization, repair or fallback."""
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError("archive_missing")
    with sqlite3.connect(path.as_uri()+"?mode=ro", uri=True) as con:
        rows = con.execute(
            "SELECT ts_ms,o,h,l,cl,v FROM market_ohlcv WHERE exchange=? AND symbol=? "
            "AND timeframe='1h' AND ts_ms>=? AND ts_ms<? ORDER BY ts_ms",
            (venue, symbol, start_ms, end_ms),
        ).fetchall()
    if len(rows) != (end_ms-start_ms)//HOUR:
        raise ValueError("archive_incomplete")
    validate_bars(rows, interval_ms=HOUR)
    if rows[0][0] != start_ms or rows[-1][0]+HOUR != end_ms:
        raise ValueError("archive_boundary_mismatch")
    return [list(row) for row in rows]


def run_phase(path, *, phase="discovery", simulate=False, manifest_path=None):
    plan, snapshot, snapshot_hash = load_contract()
    boundaries = {
        "discovery": (plan["evaluation_start_utc"], plan["discovery_end_exclusive_utc"]),
        "validation": (plan["discovery_end_exclusive_utc"], plan["validation_end_exclusive_utc"]),
        "final": (plan["validation_end_exclusive_utc"], plan["evaluation_end_exclusive_utc"]),
    }
    if phase not in boundaries:
        raise ValueError("unsupported_phase")
    phase_start, end = map(utc_ms, boundaries[phase])
    start = utc_ms(plan["archive_start_utc"])
    manifest = None
    manifest_hash = None
    if simulate:
        if manifest_path is None:
            raise ValueError("frozen_dataset_manifest_required")
        raw_manifest = Path(manifest_path).read_bytes()
        manifest = json.loads(raw_manifest)
        manifest_hash = hashlib.sha256(raw_manifest).hexdigest()
    report = {"experiment_id": plan["experiment_id"], "phase": phase,
              "snapshot_sha256": snapshot_hash, "plan_sha256": snapshot["plan_sha256"],
              "archive_path": str(Path(path).resolve()), "simulation_requested": simulate,
              "qualification": "MODELLED_EXPLORATORY_NOT_PROMOTION_EVIDENCE",
              "split_account_policy": plan["split_account_policy"], "markets": {},
              "source_fingerprint_scope": "selected_files_not_complete_attestation"}
    report["dataset_manifest_sha256"] = manifest_hash
    for symbol in plan["symbols"]:
        try:
            rows = read_rows(path, venue=plan["venue"], symbol=symbol, start_ms=start, end_ms=end)
            market = {"status":"ARCHIVE_VERIFIED", "bars":len(rows),
                      "dataset_sha256":hashlib.sha256(json.dumps(rows,separators=(",",":"),allow_nan=False).encode()).hexdigest()}
            if simulate:
                verify_prefix(manifest, symbol=symbol, phase=phase, rows=rows,
                              plan_sha256=snapshot["plan_sha256"], snapshot_sha256=snapshot_hash)
                market["results"] = {}
                for arm in (*plan["strategies"], *plan["controls"]):
                    market["results"][arm] = {}
                    for fee in plan["fee_bps_per_side_scenarios"]:
                        kwargs = dict(start_index=plan["warmup_bars"], interval_ms=HOUR,
                                      initial_cash=plan["initial_cash_per_independent_arm"],
                                      entry_notional=plan["entry_notional_quote"], fee_bps=fee,
                                      slippage_bps=plan["slippage_bps_per_side"],
                                      terminal_liquidation=phase == "final")
                        if arm in snapshot["strategies"]:
                            result = run_frozen_segment(rows, strategy=snapshot["strategies"][arm],
                                                        symbol=symbol, **kwargs)
                        else:
                            actions = ["hold"]*len(rows)
                            if arm == "same_entry_notional_buy_and_hold":
                                actions[plan["warmup_bars"]-1] = "buy"
                            result = simulate_next_open(rows, actions, **kwargs)
                        before = [r for r in result["equity"] if r["bar_ts_ms"] < phase_start]
                        initial = before[-1]["equity_quote"] if before else plan["initial_cash_per_independent_arm"]
                        result["phase_net_quote_profit"] = result["terminal_equity_quote"]-initial
                        result["phase_starting_equity_quote"] = initial
                        result["phase_start_ms"] = phase_start
                        result["prefix_metrics_scope"] = "continuous_account_from_evaluation_start"
                        market["results"][arm][str(fee)] = result
                market["status"] = "MODELLED_RESULTS"
            report["markets"][symbol] = market
        except (ValueError, sqlite3.Error) as exc:
            report["markets"][symbol] = {"status":"INCOMPLETE", "error_type":type(exc).__name__, "reason":str(exc)}
    report["all_markets_complete"] = all(m["status"] != "INCOMPLETE" for m in report["markets"].values())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive-db", type=Path, required=True)
    parser.add_argument("--phase", choices=("discovery","validation","final"), default="discovery")
    parser.add_argument("--simulate", action="store_true", help="Default is coverage-only, no signals evaluated.")
    parser.add_argument("--dataset-manifest", type=Path, help="Required frozen prefixes for simulation.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == args.archive_db.resolve():
        raise ValueError("output_must_not_be_archive")
    report = run_phase(args.archive_db, phase=args.phase, simulate=args.simulate,
                       manifest_path=args.dataset_manifest)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps({"phase":args.phase, "all_markets_complete":report["all_markets_complete"],
                      "statuses":{s:m["status"] for s,m in report["markets"].items()}}))
    return 0 if report["all_markets_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
