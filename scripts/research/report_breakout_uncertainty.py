"""Paired later-period daily mean sensitivity, not selection-adjusted proof."""
import argparse
import hashlib
import json
import math
import random
import statistics
from pathlib import Path


def paired_daily(left, right, start_timestamp, split):
    a = {r["hour"]: r["equity"] for r in left}
    b = {r["hour"]: r["equity"] for r in right}
    hours = sorted(h for h in a.keys() & b.keys() if h >= split - 1)
    if not hours:
        raise ValueError("no aligned later valuations")
    # Reject incomplete interior evidence, rather than silently dropping bad days.
    for h in range(hours[0], hours[-1] + 1):
        if any(v is None or not math.isfinite(v) or v <= 0
               for v in (a.get(h), b.get(h))):
            raise ValueError("unknown later valuation")
    ends = [h for h in hours if (start_timestamp // 3600 + h) % 24 == 23]
    pairs = [(h, a[h] / a[h - 24] - 1, b[h] / b[h - 24] - 1)
             for h in ends if h - 24 >= split - 1 and h - 24 in a and h - 24 in b]
    return pairs


def block_mean_gap(pairs, block, repeats=2000, seed=7):
    gaps = [a - b for _, a, b in pairs]
    if len(gaps) < block or block < 2:
        return {"status": "INSUFFICIENT_POWER", "days": len(gaps)}
    rng = random.Random(seed)
    estimates = []
    for _ in range(repeats):
        indices = []
        while len(indices) < len(gaps):
            first = rng.randrange(len(gaps) - block + 1)
            indices.extend(range(first, first + block))
        estimates.append(statistics.mean(gaps[i] for i in indices[:len(gaps)]))
    estimates.sort()
    return {"status": "DESCRIPTIVE", "days": len(gaps), "block_days": block,
            "mean_daily_return_gap": statistics.mean(gaps),
            "p025": estimates[int(repeats * .025)], "p975": estimates[int(repeats * .975)],
            "repeats": repeats, "seed": seed}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portfolio", type=Path, required=True)
    parser.add_argument("--comparison", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    p_raw, b_raw = args.portfolio.read_bytes(), args.comparison.read_bytes()
    p, b = json.loads(p_raw), json.loads(b_raw)
    if hashlib.sha256(p_raw).hexdigest() != b["portfolio_sha256"]:
        raise ValueError("parent mismatch")
    lookup = {(r["volume_multiple"], r["fee_bps"]): r for r in b["results"]}
    results = []
    for r in p["results"]:
        btc = lookup[(r["volume_multiple"], r["fee_bps"])]
        pairs = paired_daily(r["curve"], btc["btc"]["curve"], p["start_timestamp"], p["segment_split_hour"])
        results.append({"volume_multiple": r["volume_multiple"], "fee_bps": r["fee_bps"],
                        "paired_daily_returns": pairs,
                        "sensitivity": [block_mean_gap(pairs, k) for k in (14, 28)]})
    output = {"artifact_type": "later_daily_mean_gap_sensitivity_v1",
              "not_fresh_holdout": True, "not_selection_adjusted": True,
              "not_promotion_evidence": True,
              "exclusions": "partial boundary days and final open liquidation; mark-to-market daily returns, not terminal return CI",
              "portfolio_sha256": hashlib.sha256(p_raw).hexdigest(),
              "comparison_sha256": hashlib.sha256(b_raw).hexdigest(),
              "source": Path(__file__).read_text(), "results": results}
    with args.out.open("x") as stream:
        json.dump(output, stream, allow_nan=False)
    print(json.dumps([{ "volume_multiple": r["volume_multiple"], "fee_bps": r["fee_bps"],
                       "sensitivity": r["sensitivity"]} for r in results]))


if __name__ == "__main__":
    main()
