"""Frozen historical reversal diagnostic; no download, orders or promotion."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from services.backtest.next_open_research import run_frozen_segment, simulate_next_open, validate_bars
from services.strategies.presets import PRESETS

DAY = 86400000
SOURCE_FILES = ["scripts/research/run_reversal_diagnostic.py", "services/backtest/next_open_research.py",
                "services/strategies/presets.py", "services/strategies/strategy_registry.py",
                "services/strategies/mean_reversion_rsi.py", "services/strategies/volatility_reversal.py",
                "services/strategies/indicators.py", "services/strategies/market_filters.py"]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def freeze(dataset):
    return {"kind": "FROZEN_HISTORICAL_DIAGNOSTIC_NOT_HOLDOUT",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "dataset": str(Path(dataset).resolve()), "dataset_sha256": digest(dataset),
            "source_sha256": {p: digest(ROOT/p) for p in SOURCE_FILES},
            "symbols": ["AVAX-USD", "QNT-USD", "ICP-USD"], "start_index": 52,
            "initial_cash_usd": 1000, "entry_notional_usd": 100,
            "presets": {p: deepcopy(PRESETS[p]["strategy"]) for p in
                        ("mean_reversion_default", "volatility_reversal_default")},
            "costs": [{"name": "primary", "fee_bps": 50, "slippage_bps": 10},
                      {"name": "cost_stress", "fee_bps": 100, "slippage_bps": 25},
                      {"name": "retail_cost_sensitivity", "fee_bps": 300, "slippage_bps": 50}],
            "rules": ["no_parameter_search", "long_only_no_pyramiding", "completed_candles_only",
                      "next_open_execution", "terminal_close_liquidation_labelled", "cash_and_equal_notional_hold_controls"],
            "limitations": ["already_explored_coin_selection_and_data", "not_out_of_sample_confirmation",
                            "assumed_costs_not_actual_retail_fees", "no_orderbook_fill_proof",
                            "not_max_drawdown_risk_policy_simulation", "no_intrabar_stops_or_perfect_peaks"],
            "orders_authorized": False, "promotion_authorized": False}


def rows_for(data, product):
    if data["markets"][product]["status"] != "GRID_VERIFIED":
        raise ValueError("unverified_dataset")
    cutoff = int(datetime.fromisoformat(data["observed_at_utc"]).timestamp())//86400*86400
    raw = data["markets"][product]["raw_candles"]["candles"]
    rows = sorted([[int(c["start"])*1000, *[float(c[k]) for k in
                  ("open", "high", "low", "close", "volume")]] for c in raw
                   if cutoff-182*86400 <= int(c["start"]) < cutoff], key=lambda r:r[0])
    validate_bars(rows, interval_ms=DAY)
    if len(rows) != 182:
        raise ValueError("wrong_historical_window")
    return rows


def run(plan_path):
    plan = json.loads(Path(plan_path).read_text())
    if plan["kind"] != "FROZEN_HISTORICAL_DIAGNOSTIC_NOT_HOLDOUT":
        raise ValueError("wrong_plan")
    if digest(plan["dataset"]) != plan["dataset_sha256"]:
        raise ValueError("dataset_changed")
    for p, expected in plan["source_sha256"].items():
        if digest(ROOT/p) != expected:
            raise ValueError("source_changed")
    data = json.loads(Path(plan["dataset"]).read_text())
    result = {"kind": "CF_MODELLED_REVERSAL_DIAGNOSTIC", "plan_sha256": digest(plan_path),
              "trials": [], "parameter_search": False, "orders_submitted": False,
              "promotion_authorized": False, "limitations": plan["limitations"]}
    for product in plan["symbols"]:
        rows = rows_for(data, product)
        for costs in plan["costs"]:
            args = dict(start_index=plan["start_index"], interval_ms=DAY,
                        initial_cash=plan["initial_cash_usd"], entry_notional=plan["entry_notional_usd"],
                        fee_bps=costs["fee_bps"], slippage_bps=costs["slippage_bps"], terminal_liquidation=True)
            for name, strategy in plan["presets"].items():
                output = run_frozen_segment(rows, strategy=strategy, symbol=product, **args)
                result["trials"].append({"symbol": product, "arm": name, "cost": costs, "result": output})
            for name in ("cash", "equal_notional_buy_and_hold"):
                actions = ["hold"]*len(rows)
                if name != "cash":
                    actions[plan["start_index"]-1] = "buy"
                output = simulate_next_open(rows, actions, **args)
                result["trials"].append({"symbol": product, "arm": name, "cost": costs, "result": output})
    if digest(plan["dataset"]) != plan["dataset_sha256"] or any(digest(ROOT/p) != h for p,h in plan["source_sha256"].items()):
        raise ValueError("evidence_changed_during_run")
    result["experiment_arm_runs"] = len(result["trials"])
    result["strategy_arm_runs"] = sum(t["arm"] in plan["presets"] for t in result["trials"])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--freeze-dataset", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.freeze_dataset and args.output:
        parser.error("freeze and run are separate stages")
    if args.freeze_dataset:
        with args.plan.open("x") as stream:
            json.dump(freeze(args.freeze_dataset), stream, indent=2, allow_nan=False)
        print("HISTORICAL_DIAGNOSTIC_PLAN_SAVED")
    elif args.output:
        with args.output.open("x") as stream:
            json.dump(run(args.plan), stream, indent=2, allow_nan=False)
        print("MODELLED_RESULT_SAVED_NOT_PROFIT_CONFIRMATION")
    else:
        parser.error("freeze dataset or output required")


if __name__ == "__main__":
    main()
