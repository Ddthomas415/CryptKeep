"""Frozen breakout trade diagnostics; no new search or promotion evidence."""

import argparse
import ast
import collections
import contextlib
import hashlib
import io
import json
import math
from pathlib import Path
import random
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
SEARCH = ROOT / "docs/research/strategy_search_20261009/search.py"
CANDIDATE = ROOT / "docs/research/strategy_search_20261009/candidate.py"


def observed_trade(opens, present, signal, hold=72, fee=.005, slip=.001):
    """Hold exactly 72 hours from next-open entry to exit open; gaps unknown."""
    entry, exit_ = signal + 1, signal + 1 + hold
    if exit_ >= len(opens):
        return None, "immature"
    if not all(present[entry:exit_ + 1]):
        return None, "missing_candle"
    e, x = float(opens[entry]), float(opens[exit_])
    if not (math.isfinite(e) and math.isfinite(x) and e > 0 and x > 0):
        return None, "invalid_price"
    return x / e * (1 - slip) * (1 - fee) / ((1 + slip) * (1 + fee)) - 1, None


def calendar_block_mean(trades, days, block=14, repeats=2000, seed=7):
    """Resample contiguous days jointly across coins, including no-event days.

    Trade-mean diagnostic, NOT a tradable portfolio or selection-adjusted CI.
    Preserve overlapping cohorts via multi-day blocks; block choice is sensitivity.
    """
    if days < block or block < 1 or repeats < 20:
        return {"status": "INSUFFICIENT_POWER", "block_days": block}
    totals, counts = [0.0] * days, [0] * days
    for day, value in trades:
        if not 0 <= day < days or not math.isfinite(value):
            raise ValueError("invalid aligned event")
        totals[day] += value
        counts[day] += 1
    if not sum(counts):
        return {"status": "INSUFFICIENT_POWER", "block_days": block}
    rng, values, undefined = random.Random(seed), [], 0
    for _ in range(repeats):
        indices = []
        while len(indices) < days:
            start = rng.randrange(days - block + 1)
            indices.extend(range(start, start + block))
        indices = indices[:days]
        count = sum(counts[i] for i in indices)
        if count:
            values.append(sum(totals[i] for i in indices) / count)
        else:
            undefined += 1
    values.sort()
    return {"status": "INCOMPLETE" if undefined else "DESCRIPTIVE",
            "mean": sum(totals) / sum(counts),
            "p025": None if undefined else values[int(repeats * .025)],
            "p975": None if undefined else values[int(repeats * .975)],
            "undefined_replicates": undefined, "block_days": block,
            "repeats": repeats, "seed": seed, "not_selection_adjusted": True}


def load_frozen_features(input_root):
    source = SEARCH.read_text().split("EXITS = {")[0]
    namespace = {"__file__": str(SEARCH)}
    previous = sys.argv
    try:
        sys.argv = [str(SEARCH), str(input_root)]
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(source, str(SEARCH), "exec"), namespace)
    finally:
        sys.argv = previous
    # Extract only the frozen signal generator, not its search or IID bootstrap.
    function = next(n for n in ast.parse(CANDIDATE.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == "events")
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(CANDIDATE), "exec"), namespace)
    return namespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    inputs = sorted(p for folder in ("cb/h1", "cb2/h1")
                    for p in (args.input_root / folder).glob("*.json"))
    if not all(list((args.input_root / folder).glob("*.json")) for folder in ("cb/h1", "cb2/h1")):
        raise ValueError("original hourly archives required")
    hashes = {str(p.relative_to(args.input_root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in inputs}
    ns = load_frozen_features(args.input_root)
    split = (ns["SPLIT"] - ns["START"]) // 3600
    results = []
    for mult in (3, 2):
        events = ns["events"](mult)
        for fee in (.005, .006, .012):
            for part, lo, hi in (("train", 0, split), ("test", split, ns["NH"])):
                excluded, scored = collections.Counter(), []
                eligible = [(i, ci) for i, ci in events if lo <= i < hi]
                for i, ci in eligible:
                    # Entry AND label end must remain in discovery, not just signal.
                    if part == "train" and i + 73 >= split:
                        excluded["purged_split_overlap"] += 1
                        continue
                    value, reason = observed_trade(ns["O"][ci], ns["PRES"][ci], i, fee=fee)
                    if reason:
                        excluded[reason] += 1
                    else:
                        scored.append({"symbol": ns["coins"][ci],
                                       "signal_time": ns["START"] + i * 3600,
                                       "entry_time": ns["START"] + (i + 1) * 3600,
                                       "exit_time": ns["START"] + (i + 73) * 3600,
                                       "net_return": value, "entry_day": (i + 1 - lo) // 24})
                days = math.ceil((hi - lo) / 24)
                xs = [r["net_return"] for r in scored]
                results.append({"volume_multiple": mult, "fee_bps": fee * 10000,
                                "segment": part, "eligible_signals": len(eligible),
                                "scored": len(scored), "excluded": dict(excluded),
                                "mean_net_return": statistics.mean(xs) if xs else None,
                                "calendar_blocks": [calendar_block_mean(
                                    [(r["entry_day"], r["net_return"]) for r in scored], days, block=b)
                                    for b in (7, 14, 28)], "trades": scored})
    output = {"artifact_type": "corrected_frozen_breakout_trade_diagnostic_v1",
              "not_promotion_evidence": True, "not_fresh_holdout": True,
              "not_portfolio_profit": True, "input_sha256": hashes,
              "original_search": SEARCH.read_text(), "original_candidate": CANDIDATE.read_text(),
              "correction_source": Path(__file__).read_text(),
              "execution": "next observed open; 72h exit open; contiguous candles required",
              "fee_contract": "50bps current recorded tier scenario; 60/120bps stress, historical fees unverified",
              "results": results}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(output, stream, allow_nan=False)
    print(json.dumps({"file": str(args.out), "configurations": len(results)}))


if __name__ == "__main__":
    main()
