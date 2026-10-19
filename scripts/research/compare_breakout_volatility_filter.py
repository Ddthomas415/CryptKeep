"""Exploratory candle counterfactual, not fills, portfolio PnL or promotion proof."""
from copy import deepcopy
import json
from pathlib import Path
import hashlib
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from services.strategies.strategy_registry import compute_signal


def normalize_candle(raw):
    if not isinstance(raw, (list, tuple)) or len(raw) != 6:
        raise ValueError("invalid raw candle shape")
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not math.isfinite(v) for v in raw):
        raise ValueError("invalid raw candle values")
    ts, lo, hi, op, cl, vol = raw
    if ts < 0 or ts % 300 != 0:
        raise ValueError("invalid raw candle timestamp")
    if not 0 < lo <= min(op, cl) <= max(op, cl) <= hi or vol < 0:
        raise ValueError("invalid raw candle prices or volume")
    return [int(ts)*1000, op, hi, lo, cl, vol]


def evaluate(rows, strategy):
    for row in rows:
        if not isinstance(row, (list, tuple)) or len(row) != 6:
            raise ValueError("invalid candle shape")
        ts, op, hi, lo, cl, vol = row
        if type(ts) is not int or ts < 0 or ts % 300000:
            raise ValueError("invalid candle timestamp")
        if any(isinstance(v, bool) or not isinstance(v, (int, float))
               or not math.isfinite(v) for v in (op, hi, lo, cl, vol)):
            raise ValueError("invalid candle values")
        if not 0 < lo <= min(op, cl) <= max(op, cl) <= hi or vol < 0:
            raise ValueError("invalid candle prices or volume")
    relaxed = deepcopy(strategy)
    relaxed.pop("min_volatility_pct", None)
    by_time = {r[0]: r for r in rows}
    if len(by_time) != len(rows):
        raise ValueError("duplicate timestamps")
    window, results = [], []
    for row in sorted(rows):
        if window and row[0]-window[-1][0] != 300000:
            window = []
        window = (window+[row])[-40:]
        if len(window) < 40:
            continue
        baseline = compute_signal(cfg={"strategy": strategy}, symbol="BTC/USD", ohlcv=window)
        ind = baseline["ind"]
        upward = ind["close"] > ind["upper_prev"]*(1+strategy["breakout_buffer_pct"]/100)
        if not upward or baseline["reason"] != "low_volatility_filter":
            continue
        variant = compute_signal(cfg={"strategy": relaxed}, symbol="BTC/USD", ohlcv=window)
        record = {"signal_ms": row[0], "variant_action": variant["action"],
                  "variant_reason": variant["reason"], "gross_bps": None,
                  "net_scenario_bps": None}
        # Entry at next open, exit three five-minute intervals after entry.
        future = [by_time.get(row[0]+j*300000) for j in range(1, 5)]
        if all(r is not None for r in future):
            entry, exit_price = future[0][1], future[3][1]
            gross = (exit_price/entry-1)*10000
            record.update(entry_ms=future[0][0], exit_ms=future[3][0],
                          gross_bps=gross, net_scenario_bps={str(c): gross-c for c in (20, 50, 100)})
        results.append(record)
    accepted = [r for r in results if r["variant_action"] == "buy" and r["gross_bps"] is not None]
    return {"filtered_upward_candidates": len(results), "variant_buy_labels": len(accepted),
            "candidates": results,
            "mean_gross_bps": sum(r["gross_bps"] for r in accepted)/len(accepted) if accepted else None,
            "mean_net_scenario_bps": {str(c): sum(r["net_scenario_bps"][str(c)] for r in accepted)/len(accepted)
                                      if accepted else None for c in (20, 50, 100)},
            "overlapping_pairs": sum(a["entry_ms"] < b["exit_ms"] and b["entry_ms"] < a["exit_ms"]
                                     for i, a in enumerate(accepted) for b in accepted[i+1:]),
            "scope": "exploratory_signal_counterfactual_not_portfolio_or_fills",
            "costs": "assumed_total_round_trip_bps_not_account_fees",
            "holdout": "none_previously_inspected_sample", "promotion": "NOT_SUPPORTED"}


def main(path):
    root = Path(path)
    raw = (root/"raw.jsonl").read_bytes()
    strategy = json.loads((root/"contract.json").read_text())["strategy"]
    plan = {"question": "Does removing only volatility filtering help rejected upward signals?",
            "entry": "next_bar_open", "exit": "entry_plus_15_minutes_open",
            "cost_scenarios_round_trip_bps": [20, 50, 100], "tuning": "none",
            "scope": "exploratory_not_preregistered_holdout", "strategy": strategy,
            "raw_sha256": hashlib.sha256(raw).hexdigest()}
    with (root/"volatility_comparison_plan.json").open("x") as out:
        json.dump(plan, out, indent=2)
    seen, conflicts = {}, set()
    for line in raw.splitlines():
        packet = json.loads(line)
        if packet["kind"] != "candles":
            continue
        for r in packet["payload"]:
            row = normalize_candle(r)
            ts = row[0]
            if (ts+300000)*1000000 > packet["received_ns"]:
                continue
            if ts in seen and row != seen[ts]:
                conflicts.add(ts)
            seen.setdefault(ts, row)
    result = evaluate([seen[k] for k in sorted(seen) if k not in conflicts], strategy)
    result["excluded_revisions"] = len(conflicts)
    (root/"volatility_comparison.json").write_text(json.dumps(result, indent=2, allow_nan=False))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
