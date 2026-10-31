#!/usr/bin/env python3
"""Group A scoring for the live paper simulation (spec v2 sections 7.2-7.4). Written before the start; frozen by hash.

Standard library only. Inputs follow the data contract in README.md (fills, hourly quotes, validity flags) and the
rules file `evaluation_rules.json`. Two price bases are computed from the recorded quotes, independent of the engine's
own booking: "bidask" (buys at the ask, sells at the bid, fee on each side; decides pass/fail) and "mid" (reported).

Usage:
  python3 -I score_group_a.py --fills fills.csv --hourly hourly.csv --validity validity.json --rules evaluation_rules.json \
      --start 2026-11-16T00:00:00Z --end 2027-05-17T00:00:00Z --stage 26 --out report_week26.json
  stage 52 also needs --week26 report_week26.json and judges only strategies extended at week 26.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import random
import sys
from collections import defaultdict

BASES = ("bidask", "mid")
STRATEGIES = ("breakout_default", "ema_cross_default", "mean_reversion_default")


def parse_ts(text: str) -> dt.datetime:
    t = text.strip().replace("Z", "+00:00")
    out = dt.datetime.fromisoformat(t)
    if out.tzinfo is None:
        raise ValueError(f"timestamp without timezone: {text}")
    return out.astimezone(dt.timezone.utc)


def week_index(ts: dt.datetime, start: dt.datetime) -> int:
    return int((ts - start).total_seconds() // (7 * 86400))


def load_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def fill_price(row: dict, basis: str) -> float:
    if basis == "mid":
        return float(row["mid"])
    return float(row["ask"]) if row["side"] == "buy" else float(row["bid"])


def account_result(fills: list[dict], hourly: list[dict], basis: str, start: dt.datetime, end: dt.datetime,
                   starting_cash: float) -> dict:
    """Rebuild one account on one basis: cash, holding, round trips, hourly equity."""
    fills = sorted((f for f in fills if start <= parse_ts(f["ts_utc"]) < end), key=lambda f: parse_ts(f["ts_utc"]))
    hourly = sorted((h for h in hourly if start <= parse_ts(h["ts_utc"]) < end), key=lambda h: parse_ts(h["ts_utc"]))
    if not hourly:
        raise ValueError("no hourly marks in the window")
    cash, qty = starting_cash, 0.0
    trip_cost = trip_proceeds = 0.0
    trades, fees, buy_notional, buy_minutes = [], 0.0, 0.0, []
    fi = 0
    equity, held_marks = [], 0

    def apply(f: dict) -> None:
        nonlocal cash, qty, trip_cost, trip_proceeds, fees, buy_notional
        q, fee_rate, px = float(f["qty"]), float(f["fee_rate"]), fill_price(f, basis)
        notional = q * px
        if f["side"] == "buy":
            cash -= notional * (1 + fee_rate)
            trip_cost += notional * (1 + fee_rate)
            qty += q
            buy_notional += notional
            buy_minutes.append(parse_ts(f["ts_utc"]).minute)
        elif f["side"] == "sell":
            if q > qty + 1e-12:
                raise ValueError(f"sell larger than holding in {f.get('account_id')} at {f['ts_utc']}")
            cash += notional * (1 - fee_rate)
            trip_proceeds += notional * (1 - fee_rate)
            qty -= q
            if qty <= 1e-12:
                qty = 0.0
                trades.append({"exit_ts": f["ts_utc"], "pnl": trip_proceeds - trip_cost,
                               "ret": (trip_proceeds - trip_cost) / trip_cost, "exit_rule": f.get("exit_rule", "")})
                trip_cost = trip_proceeds = 0.0
        else:
            raise ValueError(f"unknown side {f['side']!r}")
        fees += notional * fee_rate

    for h in hourly:
        ts = parse_ts(h["ts_utc"])
        while fi < len(fills) and parse_ts(fills[fi]["ts_utc"]) <= ts:
            apply(fills[fi])
            fi += 1
        mark = float(h["mid"]) if basis == "mid" else float(h["bid"])
        equity.append((ts, cash + qty * mark))
        held_marks += 1 if qty > 0 else 0
    while fi < len(fills):
        apply(fills[fi])
        fi += 1

    last = hourly[-1]
    fee_last = float(fills[-1]["fee_rate"]) if fills else 0.0
    exit_px = float(last["mid"]) if basis == "mid" else float(last["bid"])
    final_value = cash + qty * exit_px * (1 - fee_last)  # an open position is valued as if sold at the end
    peak, max_dd = equity[0][1], 0.0
    for _, v in equity:
        peak = max(peak, v)
        max_dd = max(max_dd, (peak - v) / peak if peak > 0 else 0.0)
    monthly, month_end = {}, {}
    for ts, v in equity:
        month_end[f"{ts.year}-{ts.month:02d}"] = v
    prev = starting_cash
    for m in sorted(month_end):
        monthly[m] = month_end[m] / prev - 1
        prev = month_end[m]
    wins = [t["ret"] for t in trades if t["pnl"] > 0]
    losses = [t["ret"] for t in trades if t["pnl"] <= 0]
    gross_win = sum(t["pnl"] for t in trades if t["pnl"] > 0)
    gross_loss = -sum(t["pnl"] for t in trades if t["pnl"] <= 0)
    minute_buckets = {"00-14": 0, "15-29": 0, "30-44": 0, "45-59": 0}
    for mnt in buy_minutes:
        minute_buckets[("00-14", "15-29", "30-44", "45-59")[min(3, mnt // 15)]] += 1
    return {
        "net_return": final_value / starting_cash - 1,
        "pnl": final_value - starting_cash,
        "max_drawdown": max_dd,
        "closed_trades": len(trades),
        "open_at_end": qty > 0,
        "win_rate": (len(wins) / len(trades)) if trades else None,
        "avg_win": (sum(wins) / len(wins)) if wins else None,
        "avg_loss": (sum(losses) / len(losses)) if losses else None,
        "profit_factor": (gross_win / gross_loss) if gross_loss > 0 else None,
        "fees": fees,
        "time_invested": held_marks / len(hourly),
        "turnover": buy_notional / starting_cash,
        "monthly_returns": monthly,
        "entry_minute_of_hour": minute_buckets,
        "trades": trades,
    }


def hold_result(hourly: list[dict], start: dt.datetime, end: dt.datetime, fee_rate: float) -> dict:
    marks = sorted((h for h in hourly if start <= parse_ts(h["ts_utc"]) < end), key=lambda h: parse_ts(h["ts_utc"]))
    first, last = marks[0], marks[-1]
    ret = float(last["bid"]) * (1 - fee_rate) / (float(first["ask"]) * (1 + fee_rate)) - 1
    peak, max_dd = float(marks[0]["mid"]), 0.0
    for h in marks:
        v = float(h["mid"])
        peak = max(peak, v)
        max_dd = max(max_dd, (peak - v) / peak)
    return {"net_return_bidask": ret, "max_drawdown_mid": max_dd}


def bootstrap_p(trades: list[dict], start: dt.datetime, n_weeks: int, resamples: int, seed: int) -> dict:
    """One-sided p for mean per-trade return > 0; calendar weeks resampled whole (all coins of a week together)."""
    by_week = defaultdict(list)
    for t in trades:
        by_week[week_index(parse_ts(t["exit_ts"]), start)].append(t["ret"])
    rets = [t["ret"] for t in trades]
    obs = sum(rets) / len(rets)
    rng = random.Random(seed)
    weeks = list(range(n_weeks))
    hits = 0
    for _ in range(resamples):
        sample = []
        for _w in weeks:
            sample.extend(by_week.get(rng.choice(weeks), ()))
        mean = (sum(sample) / len(sample)) if sample else 0.0
        if mean - obs >= obs:  # null imposed by centring on the observed mean
            hits += 1
    return {"mean_ret": obs, "p_one_sided": (hits + 1) / (resamples + 1)}


def classify(strategy: str, accounts: list[dict], rules: dict, stage: int, p: float | None, pooled_net: float,
             n_closed: int) -> tuple[str, str]:
    if any(not a["valid"] for a in accounts):
        return "Inconclusive", "operational validity failed: " + ", ".join(a["account_id"] for a in accounts if not a["valid"])
    breaches = [a["account_id"] for a in accounts if a["drawdown_breach"]]
    if breaches:
        return "Fail", "drawdown limit breached: " + ", ".join(breaches)
    minimum = int(rules["minimum_closed_trades"][strategy])
    if n_closed < minimum:
        if stage == 26:
            return "Extend to week 52", f"{n_closed} closed trades, minimum {minimum}"
        return "Inconclusive", f"{n_closed} closed trades at week 52, minimum {minimum}"
    if pooled_net <= 0:
        return "Fail", f"pooled net return {pooled_net:.4%} on the bid/ask basis"
    if p is not None and p < float(rules["alpha_per_strategy"]):
        return "Pass", f"p {p:.4f} below {rules['alpha_per_strategy']}"
    return "Promising but unproven", f"p {p:.4f} not below {rules['alpha_per_strategy']}"


def drawdown_breach(rule: dict, account_dd: float, hold_dd: float) -> bool:
    kind = rule.get("type", "hold")
    fixed = rule.get("max_drawdown")
    if kind == "hold":
        return account_dd > hold_dd
    if kind == "fixed":
        return account_dd > float(fixed)
    if kind == "both":
        return account_dd > hold_dd or account_dd > float(fixed)
    raise ValueError(f"unknown drawdown rule {kind!r}")


def run(args) -> dict:
    rules = json.load(open(args.rules, encoding="utf-8"))
    validity = json.load(open(args.validity, encoding="utf-8"))
    start, end = parse_ts(args.start), parse_ts(args.end)
    n_weeks = max(1, math.ceil((end - start).total_seconds() / (7 * 86400)))
    if args.stage == 52 and not args.week26:
        raise SystemExit("stage 52 needs --week26")
    prior = json.load(open(args.week26, encoding="utf-8")) if args.stage == 52 else None
    fills, hourly = load_csv(args.fills), load_csv(args.hourly)
    fills_by, hourly_by, meta = defaultdict(list), defaultdict(list), {}
    for f in fills:
        fills_by[f["account_id"]].append(f)
        meta[f["account_id"]] = (f["strategy"], f["coin"])
    for h in hourly:
        hourly_by[h["account_id"]].append(h)
    for acc, info in validity.items():
        meta.setdefault(acc, (info["strategy"], info["coin"]))
    fee = float(rules["fee_rate_per_side"])
    report = {"stage": args.stage, "start": args.start, "end": args.end, "rules": rules, "accounts": {}, "strategies": {}}
    for acc in sorted(meta):
        strategy, coin = meta[acc]
        res = {b: account_result(fills_by[acc], hourly_by[acc], b, start, end, float(rules["starting_cash"]))
               for b in BASES}
        hold = hold_result(hourly_by[acc], start, end, fee)
        v = validity.get(acc, {"valid": False, "reasons": ["missing from validity file"]})
        report["accounts"][acc] = {
            "strategy": strategy, "coin": coin, "valid": bool(v.get("valid")), "validity_reasons": v.get("reasons", []),
            "hold": hold, "drawdown_breach": drawdown_breach(rules["drawdown_rule"], res["bidask"]["max_drawdown"],
                                                             hold["max_drawdown_mid"]),
            **{b: {k: val for k, val in res[b].items() if k != "trades"} for b in BASES},
            "_trades_bidask": res["bidask"]["trades"],
        }
    for strategy in STRATEGIES:
        accs = [dict(account_id=a, **r) for a, r in report["accounts"].items() if r["strategy"] == strategy]
        if not accs:
            continue
        if prior is not None and prior["strategies"].get(strategy, {}).get("classification") != "Extend to week 52":
            report["strategies"][strategy] = {"classification": prior["strategies"][strategy]["classification"],
                                              "reason": "judged at week 26; not judged again"}
            continue
        trades = [t for a in accs for t in a["_trades_bidask"]]
        pooled_net = sum(a["bidask"]["pnl"] for a in accs) / (float(rules["starting_cash"]) * len(accs))
        pooled_mid = sum(a["mid"]["pnl"] for a in accs) / (float(rules["starting_cash"]) * len(accs))
        boot = bootstrap_p(trades, start, n_weeks, int(rules["bootstrap_resamples"]), int(rules["seed"])) if trades else \
            {"mean_ret": None, "p_one_sided": None}
        label, reason = classify(strategy, accs, rules, args.stage, boot["p_one_sided"], pooled_net, len(trades))
        report["strategies"][strategy] = {
            "classification": label, "reason": reason, "closed_trades": len(trades),
            "pooled_net_bidask": pooled_net, "pooled_net_mid": pooled_mid, **boot,
        }
    for r in report["accounts"].values():
        r.pop("_trades_bidask")
    return report


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    for name in ("fills", "hourly", "validity", "rules", "start", "end", "out"):
        ap.add_argument(f"--{name}", required=True)
    ap.add_argument("--stage", type=int, choices=(26, 52), required=True)
    ap.add_argument("--week26")
    args = ap.parse_args(argv)
    report = run(args)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1, sort_keys=True, default=str)
    for s, r in report["strategies"].items():
        print(f"{s}: {r['classification']} ({r['reason']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
