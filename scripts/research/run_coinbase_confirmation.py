"""Isolated Coinbase research contract support; no fetch, orders or campaigns."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.research.run_multisymbol_baseline import HOUR, read_rows, utc_ms
from services.backtest.next_open_research import run_frozen_segment, simulate_next_open
from services.backtest.research_prefix_freeze import rows_hash


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference(name):
    path = (ROOT/name).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("reference_outside_repo")
    return path


def load_contract(path):
    path = Path(path)
    plan = json.loads(path.read_bytes())
    if (plan["venue"] != "coinbase" or plan["market_type"] != "spot"
            or plan["timeframes"] != ["1h"] or not plan["research_only"]
            or plan["execution_authority"] or plan["promotion_authority"]
            or plan["parameter_search"]):
        raise ValueError("unsupported_contract_authority")
    baskets = [[f"{base}/{quote}" for base in ("BTC", "ETH", "SOL", "ADA", "XRP")]
               for quote in ("USDT", "USD")]
    if (plan["symbols"] not in baskets
            or plan.get("quote_currency", "USDT") != plan["symbols"][0].split("/")[1]
            or plan["controls"] != ["cash", "same_entry_notional_buy_and_hold"]):
        raise ValueError("unsupported_market_or_control_set")
    snapshot_path = reference(plan["strategy_source_snapshot_path"])
    fee_path = reference(plan["fee_observation_path"])
    if (digest(snapshot_path) != plan["strategy_source_snapshot_sha256"]
            or digest(fee_path) != plan["fee_observation_sha256"]):
        raise ValueError("referenced_evidence_changed")
    snapshot = json.loads(snapshot_path.read_bytes())
    fee = json.loads(fee_path.read_bytes())
    if (fee["venue"] != "coinbase" or fee["product_type"] != "SPOT"
            or fee["status"] != "OBSERVED_ACCOUNT_SPOT_FEE_TIER"
            or fee["taker_bps"] != plan["primary_taker_fee_bps_per_side"]):
        raise ValueError("fee_contract_mismatch")
    if set(snapshot["strategies"]) != set(plan["strategies"]):
        raise ValueError("strategy_set_mismatch")
    for name, expected in snapshot["selected_source_sha256"].items():
        if digest(reference(name)) != expected:
            raise ValueError("selected_source_changed")
    a, s, c, e = (utc_ms(plan[k]) for k in ("archive_start_utc", "evaluation_start_utc",
                                         "descriptive_checkpoint_utc", "evaluation_end_exclusive_utc"))
    if (not a < s < c < e or (s-a)//HOUR != plan["warmup_bars"]
            or any(t % HOUR for t in (a, s, c, e))
            or (e-a)//HOUR != plan["expected_warmup_and_evaluation_bars_per_market"]):
        raise ValueError("invalid_contract_boundaries")
    identity = {"plan_sha256": digest(path), "snapshot_sha256": digest(snapshot_path),
                "fee_receipt_sha256": digest(fee_path), "runner_sha256": digest(__file__)}
    return plan, snapshot, identity


def register(plan_path, *, now_ms):
    plan, _, identity = load_contract(plan_path)
    if now_ms >= utc_ms(plan["evaluation_start_utc"]):
        raise ValueError("registration_deadline_missed")
    return {"kind": "RESEARCH_PREREGISTRATION_NOT_ACTIVATION", "identity": identity,
            "registered_at_ms": now_ms, "experiment_id": plan["experiment_id"]}


def check_registration(path, plan, identity, now_ms):
    registration = json.loads(Path(path).read_bytes())
    timestamp = registration.get("registered_at_ms")
    if (registration.get("kind") != "RESEARCH_PREREGISTRATION_NOT_ACTIVATION"
            or registration.get("identity") != identity
            or registration.get("experiment_id") != plan["experiment_id"]
            or type(timestamp) is not int or timestamp > now_ms
            or timestamp >= utc_ms(plan["evaluation_start_utc"])):
        raise ValueError("invalid_or_stale_registration")
    return digest(path)


def run(plan_path, archive_path, *, phase="warmup", mode="coverage", now_ms,
        registration_path=None, manifest_path=None, previous_manifest_path=None):
    plan, snapshot, identity = load_contract(plan_path)
    endpoints = {"warmup": "evaluation_start_utc", "checkpoint": "descriptive_checkpoint_utc",
                 "final": "evaluation_end_exclusive_utc"}
    if phase not in endpoints or mode not in ("coverage", "freeze", "simulate"):
        raise ValueError("unsupported_mode_or_phase")
    target_end = utc_ms(plan[endpoints[phase]])
    start = utc_ms(plan["archive_start_utc"])
    end = min(target_end, now_ms//HOUR*HOUR) if phase == "warmup" and mode == "coverage" else target_end
    if end > now_ms or end <= start:
        raise ValueError("requested_data_not_completed")
    if mode == "simulate" and phase == "warmup":
        raise ValueError("warmup_cannot_be_scored")
    registration_hash = None
    if mode != "coverage":
        if registration_path is None:
            raise ValueError("registration_required")
        registration_hash = check_registration(registration_path, plan, identity, now_ms)
    report = {"experiment_id": plan["experiment_id"], "identity": identity, "phase": phase,
              "mode": mode, "archive_path": str(Path(archive_path).resolve()),
              "requested_end_ms": end, "target_end_ms": target_end,
              "full_phase_completed": end == target_end, "registration_sha256": registration_hash,
              "qualification": "RESEARCH_ONLY_NOT_PROMOTION", "markets": {}}
    rows_by_symbol = {}
    for symbol in plan["symbols"]:
        try:
            rows = read_rows(archive_path, venue="coinbase", symbol=symbol, start_ms=start, end_ms=end)
            rows_by_symbol[symbol] = rows
            report["markets"][symbol] = {"status": "ARCHIVE_VERIFIED", "bars": len(rows),
                                         "rows_sha256": rows_hash(rows)}
        except (ValueError, sqlite3.Error) as exc:
            report["markets"][symbol] = {"status": "INCOMPLETE", "reason": str(exc)}
    report["all_markets_complete"] = len(rows_by_symbol) == len(plan["symbols"])
    if mode == "coverage" or not report["all_markets_complete"]:
        return report
    if mode == "freeze":
        old = {symbol: {} for symbol in plan["symbols"]}
        parent_hash = None
        if phase != "warmup":
            if previous_manifest_path is None:
                raise ValueError("previous_manifest_required")
            previous = json.loads(Path(previous_manifest_path).read_bytes())
            expected_phase = "warmup" if phase == "checkpoint" else "checkpoint"
            if (previous["identity"] != identity or previous["phase"] != expected_phase
                    or previous["registration_sha256"] != registration_hash):
                raise ValueError("previous_manifest_contract_mismatch")
            old = previous["prefixes"]
            parent_hash = digest(previous_manifest_path)
            expected_keys = {"warmup"} if phase == "checkpoint" else {"warmup", "checkpoint"}
            if set(old) != set(plan["symbols"]) or any(set(p) != expected_keys for p in old.values()):
                raise ValueError("missing_previous_prefix")
        prefixes = {}
        for symbol, rows in rows_by_symbol.items():
            for name, prefix in old[symbol].items():
                expected_bars = (utc_ms(plan[endpoints[name]])-start)//HOUR
                if prefix["bars"] != expected_bars or len(rows) < prefix["bars"] or rows_hash(rows[:prefix["bars"]]) != prefix["rows_sha256"]:
                    raise ValueError("previous_prefix_changed")
            prefixes[symbol] = {**old[symbol], phase: {"bars": len(rows), "rows_sha256": rows_hash(rows)}}
        return {"kind": "CONTENT_FREEZE_NOT_AUTHENTICITY_PROOF", "phase": phase,
                "identity": identity, "registration_sha256": registration_hash,
                "parent_manifest_sha256": parent_hash, "prefixes": prefixes}
    if manifest_path is None:
        raise ValueError("manifest_required")
    manifest = json.loads(Path(manifest_path).read_bytes())
    if (manifest["identity"] != identity or manifest["phase"] != phase
            or manifest["registration_sha256"] != registration_hash):
        raise ValueError("manifest_contract_mismatch")
    required = {"warmup", "checkpoint"} if phase == "checkpoint" else {"warmup", "checkpoint", "final"}
    if (set(manifest["prefixes"]) != set(plan["symbols"])
            or any(set(p) != required for p in manifest["prefixes"].values())):
        raise ValueError("missing_previous_prefix")
    for symbol, rows in rows_by_symbol.items():
        current = manifest["prefixes"][symbol][phase]
        if current["bars"] != len(rows) or current["rows_sha256"] != rows_hash(rows):
            raise ValueError("dataset_changed_after_freeze")
        for name, prefix in manifest["prefixes"][symbol].items():
            expected_bars = (utc_ms(plan[endpoints[name]])-start)//HOUR
            if prefix["bars"] != expected_bars or len(rows) < prefix["bars"] or rows_hash(rows[:prefix["bars"]]) != prefix["rows_sha256"]:
                raise ValueError("previous_prefix_changed")
    report["dataset_manifest_sha256"] = digest(manifest_path)
    for symbol, rows in rows_by_symbol.items():
        results = {}
        for arm in plan["strategies"]+plan["controls"]:
            results[arm] = {}
            for slip in [plan["primary_slippage_bps_per_side"]]+plan["slippage_stress_bps_per_side"]:
                costs = dict(start_index=plan["warmup_bars"], interval_ms=HOUR,
                             initial_cash=plan["initial_cash_per_independent_arm"],
                             entry_notional=plan["entry_notional_quote"],
                             fee_bps=plan["primary_taker_fee_bps_per_side"], slippage_bps=slip,
                             terminal_liquidation=phase == "final")
                if arm in snapshot["strategies"]:
                    result = run_frozen_segment(rows, strategy=snapshot["strategies"][arm], symbol=symbol, **costs)
                else:
                    actions = ["hold"]*len(rows)
                    if arm == "same_entry_notional_buy_and_hold":
                        actions[plan["warmup_bars"]-1] = "buy"
                    result = simulate_next_open(rows, actions, **costs)
                boundary = utc_ms(plan["descriptive_checkpoint_utc"] if phase == "final" else plan["evaluation_start_utc"])
                before = [row for row in result["equity"] if row["bar_ts_ms"] < boundary]
                starting = before[-1]["equity_quote"] if before else plan["initial_cash_per_independent_arm"]
                result["phase_net_quote_profit"] = result["terminal_equity_quote"]-starting
                result["phase_starting_equity_quote"] = starting
                result["natural_closed_cycles"] = sum(t["side"] == "sell" and not t["terminal"] for t in result["trades"])
                result["terminal_equity_adjustment_quote"] = result["terminal_equity_quote"]-result["equity"][-1]["equity_quote"]
                result["prefix_metrics_scope"] = "new_confirmation_account_from_evaluation_start"
                results[arm][str(slip)] = result
        report["markets"][symbol].update(status="MODELLED_RESULTS", results=results)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--archive-db", type=Path)
    parser.add_argument("--mode", choices=("coverage", "register", "freeze", "simulate"), default="coverage")
    parser.add_argument("--phase", choices=("warmup", "checkpoint", "final"), default="warmup")
    parser.add_argument("--registration", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--previous-manifest", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    now = int(datetime.now(timezone.utc).timestamp()*1000)
    with args.output.open("x") as stream:
        if args.mode == "register":
            result = register(args.plan, now_ms=now)
        else:
            if args.archive_db is None:
                raise ValueError("archive_required")
            result = run(args.plan, args.archive_db, phase=args.phase, mode=args.mode, now_ms=now,
                         registration_path=args.registration, manifest_path=args.manifest,
                         previous_manifest_path=args.previous_manifest)
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({"mode": args.mode, "phase": args.phase,
                      "all_markets_complete": result.get("all_markets_complete"),
                      "kind": result.get("kind")}))


if __name__ == "__main__":
    main()
