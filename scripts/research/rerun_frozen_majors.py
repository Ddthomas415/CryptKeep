"""Versioned diagnostic rerun: frozen targets, next-open taker-cost execution.

Does not alter original artifacts, preregistered verdicts, or campaigns.
Daily OHLC remains an approximation, not recorded latency-aware fills.
"""

import argparse
import ast
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import statistics

from scripts.research.corrected_research_math import rebalance

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/research/majors_trend_20261009"


def load_frozen():
    source = SOURCE / "majors.py"
    tree = ast.parse(source.read_text())
    names = {"ret", "sma", "vol", "target", "stats"}
    definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    if {n.name for n in definitions} != names:
        raise ValueError("frozen source interface changed")
    rules = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == "RULES" for t in n.targets))
    paths = [SOURCE / f"{asset}-USD_d1.json" for asset in ("BTC", "ETH")]
    raw = {asset: {r[0]: r for r in json.loads(path.read_text())}
           for asset, path in zip(("BTC", "ETH"), paths)}
    cutoff = int(dt.datetime(2026, 10, 9, tzinfo=dt.timezone.utc).timestamp())
    days = sorted(t for t in set(raw["BTC"]) & set(raw["ETH"]) if t < cutoff)
    first_required = int(dt.datetime(2016, 6, 1, tzinfo=dt.timezone.utc).timestamp())
    required_days = [t for t in days if t >= first_required]
    if any(b - a != 86400 for a, b in zip(required_days, required_days[1:])):
        raise ValueError("daily gaps: do not compress calendar history")
    prices = {asset: [raw[asset][t][4] for t in days] for asset in raw}
    namespace = {"P": prices, "days": days, "math": math, "statistics": statistics, "dt": dt}
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(source), "exec"), namespace)
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [source] + paths}
    return namespace, rules, raw, hashes


def run(namespace, raw, rule, fee, start, end):
    days = namespace["days"]
    timestamp = lambda text: int(dt.datetime.fromisoformat(text).replace(tzinfo=dt.timezone.utc).timestamp())
    lo, hi = days.index(timestamp(start)), days.index(timestamp(end))
    lookback = 100 if rule == "sma100" else 30
    if lo < lookback or any(b - a != 86400 for a, b in zip(days[lo - lookback:lo], days[lo - lookback + 1:lo + 1])):
        raise ValueError("insufficient contiguous signal warmup")
    cash, units = 1000.0, {}
    curve, exposure = [(days[lo], cash)], []
    for i in range(lo + 1, hi + 1):
        previous = i - 1
        sunday = dt.datetime.fromtimestamp(days[previous], dt.timezone.utc).weekday() == 6
        due = previous == lo or (sunday and rule != "hold_btc")
        if due:
            target = namespace["target"](rule, previous)
            opens = {asset: raw[asset][days[i]][1] for asset in raw}
            cash, units = rebalance(cash, units, opens, target, fee, .0005)
        marked = cash + sum(units.get(a, 0) * namespace["P"][a][i] for a in raw)
        curve.append((days[i], marked))
        exposure.append((marked - cash) / marked)
    stats = namespace["stats"](curve, exposure)
    liquidation = cash + sum(units.get(a, 0) * namespace["P"][a][hi] * .9995 * (1 - fee) for a in raw)
    return {"rule": rule, "fee_bps": fee * 10000, "window": [start, end],
            "marked_stats": stats, "terminal_liquidation_usd": round(liquidation, 2),
            "daily_equity": curve}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    namespace, rules, raw, hashes = load_frozen()
    receipt = ROOT / "research/coinbase_fee_observation_20261008.json"
    observation = json.loads(receipt.read_text())
    if observation["taker_bps"] != 50:
        raise ValueError("fee observation changed: review scenario before rerun")
    hashes[str(receipt.relative_to(ROOT))] = hashlib.sha256(receipt.read_bytes()).hexdigest()
    hashes[str(Path(__file__).relative_to(ROOT))] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    helper = ROOT / "scripts/research/corrected_research_math.py"
    hashes[str(helper.relative_to(ROOT))] = hashlib.sha256(helper.read_bytes()).hexdigest()
    windows = [("2016-07-01", "2019-12-31"), ("2020-01-01", "2023-12-31"),
               ("2024-01-01", "2026-10-08")]
    output = {"artifact_type": "corrected_frozen_majors_diagnostic_v1", "not_promotion_evidence": True,
              "original_verdicts_unchanged": True, "source_hashes": hashes,
              "execution": "prior completed close target; following daily open; no maker-fill claim",
              "account_policy": "fresh 1000 per original diagnostic window; carry within window; not the prospective account",
              "primary_fee_bps": 50, "other_scenarios_bps": [60, 120],
              "correction_script": Path(__file__).read_text(),
              "correction_math": helper.read_text(), "frozen_target_source": (SOURCE / "majors.py").read_text(),
              "product_specific_fees": "UNVERIFIED", "results": []}
    for rule in rules:
        for fee in (.005, .006, .012):
            for start, end in windows:
                try:
                    output["results"].append(run(namespace, raw, rule, fee, start, end))
                except ValueError as exc:
                    output["results"].append({"rule": rule, "fee_bps": fee * 10000,
                                               "window": [start, end], "status": "INCOMPLETE", "reason": str(exc)})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(output, stream, allow_nan=False)
    print(json.dumps({"file": str(args.out), "runs": len(output["results"]), "not_promotion_evidence": True}))


if __name__ == "__main__":
    main()
