"""Read frozen results only; exploratory calendar and paired block diagnostics."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

import numpy as np

HOUR = 3_600_000
DAY = 24 * HOUR
SEED = 20261008
REPS = 2000
BLOCKS = (7, 14, 28)


def finite(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("nonfinite_result")
    return value


def daily_rows(result, *, start, end, capital):
    """A midnight close belongs to the day just ended, not the next day."""
    equity = result["equity"]
    if end <= start or start % DAY or end % DAY:
        raise ValueError("invalid_day_boundaries")
    if len(equity) != (end-start)//HOUR:
        raise ValueError("incomplete_hourly_equity")
    previous = finite(capital)
    output = []
    for i, row in enumerate(equity):
        if row["bar_ts_ms"] != start+i*HOUR:
            raise ValueError("equity_grid_mismatch")
        mark = finite(row["equity_quote"])
        if mark <= 0:
            raise ValueError("nonpositive_equity")
        if (i+1) % 24 == 0:
            # Replace only the last day's final mark with liquidated cash.
            close = finite(result["terminal_equity_quote"]) if i == len(equity)-1 else mark
            if close <= 0:
                raise ValueError("nonpositive_equity")
            date = datetime.fromtimestamp((row["bar_ts_ms"]+HOUR-1)/1000,
                                          timezone.utc).date().isoformat()
            output.append({"date": date, "start_equity_quote": previous,
                           "end_equity_quote": close, "net_quote_change": close-previous})
            previous = close
    if not math.isclose(previous-capital, finite(result["net_quote_profit"]), abs_tol=1e-7):
        raise ValueError("calendar_total_mismatch")
    return output


def aggregate(rows, *, weekly=False):
    groups = {}
    for row in rows:
        date = datetime.fromisoformat(row["date"]).date()
        iso = date.isocalendar()
        key = f"{iso.year}-W{iso.week:02d}" if weekly else row["date"][:7]
        group = groups.setdefault(key, {"period": key, "days": 0,
                                       "start_equity_quote": row["start_equity_quote"],
                                       "net_quote_change": 0.})
        group["days"] += 1
        group["net_quote_change"] += row["net_quote_change"]
        group["end_equity_quote"] = row["end_equity_quote"]
    return list(groups.values())


def block_indices(days, block, *, reps=REPS, seed=SEED):
    if not 1 <= block <= days or reps < 2:
        raise ValueError("invalid_bootstrap_dimensions")
    rng = np.random.default_rng(seed)
    starts = rng.integers(days, size=(reps, math.ceil(days/block)))
    return ((starts[..., None]+np.arange(block)) % days).reshape(reps, -1)[:, :days]


def drawdowns(changes, capital):
    changes = np.atleast_2d(np.asarray(changes, dtype=float))
    paths = np.concatenate((np.full((len(changes), 1), capital),
                            capital+np.cumsum(changes, axis=1)), axis=1)
    if not np.isfinite(paths).all() or (paths <= 0).any():
        raise ValueError("invalid_resampled_equity")
    peaks = np.maximum.accumulate(paths, axis=1)
    return np.max((peaks-paths)/peaks*100, axis=1)


def interval(values):
    values = np.asarray(values, dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("nonfinite_bootstrap")
    return [float(x) for x in np.quantile(values, [0.025, 0.975])]


def diagnostics(changes, benchmark, indices, capital):
    changes, benchmark = np.asarray(changes), np.asarray(benchmark)
    if changes.shape != benchmark.shape or changes.ndim != 1:
        raise ValueError("unpaired_daily_paths")
    sampled, control = changes[indices], benchmark[indices]
    dd, control_dd = drawdowns(sampled, capital), drawdowns(control, capital)
    return {"net_quote_profit_percentile_95": interval(sampled.sum(axis=1)),
            "net_quote_gap_vs_buy_hold_percentile_95": interval((sampled-control).sum(axis=1)),
            "daily_close_drawdown_pct_percentile_95": interval(dd),
            "drawdown_pct_gap_vs_buy_hold_percentile_95": interval(dd-control_dd)}


def build_report(folder):
    folder = Path(folder)
    names = ("final_20261008.json", "plan.json", "strategies.snapshot.json", "dataset.freeze.json")
    raw = {name: (folder/name).read_bytes() for name in names}
    hashes = {name: hashlib.sha256(value).hexdigest() for name, value in raw.items()}
    final, plan, snapshot, manifest = (json.loads(raw[name]) for name in names)
    if (final["phase"] != "final" or not final["all_markets_complete"]
            or final["plan_sha256"] != hashes["plan.json"]
            or snapshot["plan_sha256"] != hashes["plan.json"]
            or final["snapshot_sha256"] != hashes["strategies.snapshot.json"]
            or final["dataset_manifest_sha256"] != hashes["dataset.freeze.json"]):
        raise ValueError("input_contract_mismatch")
    if set(final["markets"]) != set(plan["symbols"]):
        raise ValueError("market_set_mismatch")
    stamp = lambda text: int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()*1000)
    start, end = stamp(plan["evaluation_start_utc"]), stamp(plan["evaluation_end_exclusive_utc"])
    days, capital = (end-start)//DAY, plan["initial_cash_per_independent_arm"]
    indices = {block: block_indices(days, block) for block in BLOCKS}
    report = {"qualification": "MODELLED_EXPLORATORY_POST_RESULT_DIAGNOSTICS_NOT_PROMOTION",
              "input_sha256": hashes, "reporter_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "numpy_version": np.__version__, "seed": SEED, "reps": REPS,
              "blocks_days": list(BLOCKS), "days": days,
              "method": "paired_circular_blocks_of_additive_daily_quote_equity_changes",
              "interval_scope": "pointwise_percentile_not_multiple_testing_corrected_not_future_prediction",
              "limits": ["post_result_method_not_preregistered", "nonstationarity_unresolved",
                         "resampled_increments_are_not_reexecuted_strategies",
                         "terminal_cost_resampled_with_last_day", "no_portfolio_or_scaling_model",
                         "daily_drawdown_not_hourly_or_intrabar_drawdown"], "markets": {}}
    expected = set(plan["strategies"]+plan["controls"])
    for symbol, market in final["markets"].items():
        if market["status"] != "MODELLED_RESULTS" or set(market["results"]) != expected:
            raise ValueError("arm_set_mismatch")
        arms = {}
        for arm, scenarios in market["results"].items():
            if set(scenarios) != {str(f) for f in plan["fee_bps_per_side_scenarios"]}:
                raise ValueError("fee_set_mismatch")
            arms[arm] = {}
            for fee, result in scenarios.items():
                if result["ending_position_qty"] != 0 or result["profit_basis"] != "liquidated_cash":
                    raise ValueError("final_position_not_flat")
                rows = daily_rows(result, start=start, end=end, capital=capital)
                benchmark = daily_rows(market["results"]["same_entry_notional_buy_and_hold"][fee],
                                       start=start, end=end, capital=capital)
                changes = [row["net_quote_change"] for row in rows]
                controls = [row["net_quote_change"] for row in benchmark]
                arms[arm][fee] = {"daily": rows, "weekly": aggregate(rows, weekly=True),
                                  "monthly": aggregate(rows), "net_quote_profit": result["net_quote_profit"],
                                  "closed_cycles": result["closed_cycles"], "fees_quote": result["fees_quote"],
                                  "time_in_market_bar_fraction": result["time_in_market_bar_fraction"],
                                  "hourly_drawdown_pct": result["bar_close_and_terminal_drawdown_pct"],
                                  "daily_drawdown_pct": float(drawdowns(changes, capital)[0]),
                                  "bootstrap": {str(b): diagnostics(changes, controls, idx, capital)
                                                for b, idx in indices.items()}}
        report["markets"][symbol] = arms
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_report(args.folder)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps({"markets": len(report["markets"]), "days": report["days"],
                      "qualification": report["qualification"]}))


if __name__ == "__main__":
    main()
