#!/usr/bin/env python3
"""Dry run of score_group_a.py on the exit-parity replay (variant C_path_w60, BTC/ETH/SOL), to check the scorer
against figures already published in spec v2 7.5-7.6. Prices: the replay's own (5 bps slippage included); no spread,
so both bases coincide. Each trade uses the whole account. Not a test of any strategy; a test of the scorer.
Usage: python3 -I dryrun_on_replay.py <repo root> <out dir>"""
import csv
import datetime as dt
import json
import os
import sqlite3
import sys
import types

ROOT, OUT = sys.argv[1:3]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import score_group_a as S  # noqa: E402

TR = f"{ROOT}/docs/research/exit_parity_audit_20261031/exit_parity_trades.csv"
DB = f"{ROOT}/research/multisymbol_baseline_v1/public_archive.sqlite"
START, END = "2026-01-01T00:00:00Z", "2026-09-30T15:00:00Z"
FEE = 0.005


def iso(text):
    return dt.datetime.strptime(text, "%Y-%m-%d %H:%M").replace(tzinfo=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


os.makedirs(OUT, exist_ok=True)
rows = [r for r in csv.DictReader(open(TR)) if r["variant"] == "C_path_w60" and r["coin"] in ("BTC", "ETH", "SOL")]
db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
t0 = int(S.parse_ts(START).timestamp() * 1000)
t1 = int(S.parse_ts(END).timestamp() * 1000)
fills, hourly, validity = [], [], {}
for strategy in S.STRATEGIES:
    for coin in ("BTC", "ETH", "SOL"):
        acc = f"{strategy}:{coin}"
        validity[acc] = {"strategy": strategy, "coin": coin, "valid": True, "reasons": []}
        for ts_ms, cl in db.execute("select ts_ms, cl from market_ohlcv where exchange='okx' and symbol=? and "
                                    "timeframe='1h' and ts_ms between ? and ? order by ts_ms", (coin + "/USDT", t0, t1)):
            t = dt.datetime.fromtimestamp(ts_ms / 1000 + 3600, dt.timezone.utc)  # mark at the candle's close
            hourly.append({"account_id": acc, "ts_utc": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "mid": cl, "bid": cl, "ask": cl})
        cash = 1000.0
        for r in sorted((r for r in rows if r["strategy"] == strategy and r["coin"] == coin), key=lambda r: r["entry_utc"]):
            e, x = float(r["entry_px"]), float(r["exit_px"])
            qty = cash / (e * (1 + FEE))
            fills.append({"account_id": acc, "strategy": strategy, "coin": coin, "ts_utc": iso(r["entry_utc"]),
                          "side": "buy", "qty": qty, "mid": e, "bid": e, "ask": e, "fee_rate": FEE, "exit_rule": ""})
            fills.append({"account_id": acc, "strategy": strategy, "coin": coin, "ts_utc": iso(r["exit_utc"]),
                          "side": "sell", "qty": qty, "mid": x, "bid": x, "ask": x, "fee_rate": FEE,
                          "exit_rule": r["exit_rule"]})
            cash = qty * x * (1 - FEE)
for name, data in (("fills.csv", fills), ("hourly.csv", hourly)):
    with open(f"{OUT}/{name}", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(data[0]))
        w.writeheader()
        w.writerows(data)
json.dump(validity, open(f"{OUT}/validity.json", "w"))
args = types.SimpleNamespace(fills=f"{OUT}/fills.csv", hourly=f"{OUT}/hourly.csv", validity=f"{OUT}/validity.json",
                             rules=os.path.join(os.path.dirname(os.path.abspath(__file__)), "evaluation_rules.json"),
                             start=START, end=END, stage=26, week26=None, out=f"{OUT}/report.json")
rep = S.run(args)
json.dump(rep, open(args.out, "w"), indent=1, sort_keys=True, default=str)
summary = {"accounts": {a: {"net_return": round(r["bidask"]["net_return"], 4), "max_drawdown": round(r["bidask"]["max_drawdown"], 4),
                            "closed_trades": r["bidask"]["closed_trades"], "hold_dd": round(r["hold"]["max_drawdown_mid"], 4)}
                        for a, r in rep["accounts"].items()},
           "strategies": {s: {k: (round(v, 5) if isinstance(v, float) else v) for k, v in r.items()}
                          for s, r in rep["strategies"].items()}}
json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=1, sort_keys=True)
print(json.dumps(summary, indent=1, sort_keys=True))
