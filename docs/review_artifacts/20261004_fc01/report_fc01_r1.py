#!/usr/bin/env python3
"""Descriptive FC-01-r1 pilot only; no live orders or confirmation claims."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import random

EXPECTED_INPUT_HASH = "cd106bd53cf045d6ae10a76d439777d96e832dedceb62b2ca53ad9795f7a60f7"


def trade(entry, exit_quote):
    entry_mid = (entry[2] + entry[3]) / 2
    exit_mid = (exit_quote[2] + exit_quote[3]) / 2
    proceeds = 100 * exit_quote[2] / entry[3]
    fees = 0.005 * (100 + proceeds)
    return dict(midpoint_bps=(exit_mid / entry_mid - 1) * 10000,
                net_usd=proceeds - 100 - fees, fees_usd=fees,
                entry_notional_usd=100, exit_notional_usd=proceeds)


def bootstrap(days, block_length):
    rng = random.Random(20261004)
    estimates = []
    for _ in range(10000):
        sample = []
        while len(sample) < len(days):
            start = rng.randrange(len(days))
            sample.extend(days[(start + j) % len(days)] for j in range(block_length))
        sample = sample[:len(days)]
        n = sum(d[0] for d in sample)
        if n:
            estimates.append((sum(d[1] for d in sample) / n * 100,
                              sum(d[2] for d in sample) / n * 100))
    if not estimates:
        raise ValueError("No eligible bootstrap sample")
    def interval(column):
        values = sorted(e[column] for e in estimates)
        return [values[int((len(values)-1)*p)] for p in (0.025, 0.975)]
    return dict(block_days=block_length, resamples=len(estimates),
                incremental_bps_per_window_ci95=interval(0),
                absolute_bps_per_window_ci95=interval(1))


def report(pinned):
    canonical = json.dumps(pinned["inputs"], sort_keys=True, separators=(",", ":"),
                           allow_nan=False).encode()
    actual_hash = hashlib.sha256(canonical).hexdigest()
    if actual_hash != EXPECTED_INPUT_HASH or actual_hash != pinned["input_content_sha256"]:
        raise ValueError("Pinned input content changed")
    quotes = {r[0]: r for r in pinned["inputs"]["quotes"]}
    rows = []
    dates = sorted({w["boundary"][:10] for w in pinned["windows"]})
    daily = {date: [0, 0.0, 0.0] for date in dates}
    for w in pinned["windows"]:
        if not w["paired_eligible"]:
            continue
        values = trade(quotes[w["entry_quote_id"]], quotes[w["exit_quote_id"]])
        selected = bool(w["qualifying"])
        gated = values["net_usd"] if selected else 0.0
        incremental = gated - values["net_usd"]
        rows.append(dict(boundary=w["boundary"], qualifying=selected,
                         entry_quote_id=w["entry_quote_id"], exit_quote_id=w["exit_quote_id"],
                         baseline=values, gated_net_usd=gated, incremental_net_usd=incremental))
        d = daily[w["boundary"][:10]]
        d[0] += 1
        d[1] += incremental
        d[2] += gated
    selected = [r for r in rows if r["qualifying"]]
    gated = sum(r["gated_net_usd"] for r in rows)
    baseline = sum(r["baseline"]["net_usd"] for r in rows)
    return dict(design="FC-01-r1", evidence="CF-MODELLED exploratory, not actual fills",
                input_content_sha256=actual_hash,
                costs=dict(taker_fee_bps_per_side=50, additional_slippage_bps=0,
                           fee_basis="each leg notional; entry fee additional to $100 purchase",
                           infrastructure="excluded", quote_currency="USD"),
                summary=dict(complete_windows=len(rows), entries=len(selected),
                             excluded_windows=len(pinned["windows"])-len(rows),
                             gated_net_usd=gated, always_long_net_usd=baseline,
                             incremental_net_usd=gated-baseline,
                             gated_mean_midpoint_bps=sum(r["baseline"]["midpoint_bps"]
                                                       for r in selected)/len(selected),
                             gated_fees_usd=sum(r["baseline"]["fees_usd"] for r in selected),
                             gated_turnover_usd=sum(100+r["baseline"]["exit_notional_usd"]
                                                    for r in selected),
                             rejected_opportunity_net_usd=sum(r["baseline"]["net_usd"]
                                                              for r in rows if not r["qualifying"])),
                bootstrap=[bootstrap(list(daily.values()), length) for length in (1, 3)],
                windows=rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pinned")
    args = parser.parse_args()
    result = report(json.loads(Path(args.pinned).read_text()))
    result["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    print(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
