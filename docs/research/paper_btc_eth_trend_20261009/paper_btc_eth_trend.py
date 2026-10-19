"""Forward paper test for the one rule that passed its pre-registered test (majors.py, 2026-10-09). Research only.
It places NO orders, reads no keys and touches no CryptKeep config, state or account. It only reads public Coinbase
daily candles and writes two files into --out.

Rule (identical to majors.py "primary_28d_trend_vol_sized"):
  Assets BTC-USD and ETH-USD, Coinbase daily closes (00:00 UTC candles; only completed days are used).
  At the close of every Sunday daily candle (Monday 00:00 UTC): for each asset, if its 28-day return > 0, weight = 0.5 * min(1, 0.50 / annualised 30-day
  volatility), else 0. Rest in cash. No leverage. Costs on traded amount: 0.6% fee + 0.05% slippage per side.
Paper account: $1,000 from the first Sunday close on/after --start (default 2026-10-11), compared with holding BTC.

Usage:  python3 paper_btc_eth_trend.py --out DIR [--start YYYY-MM-DD] [--fee 0.006]
Re-running is safe: the whole paper history is recomputed from public candles each time, so the files never drift."""
import argparse, csv, json, math, os, statistics, time, urllib.request, datetime as dt

API = "https://api.exchange.coinbase.com/products/{}/candles?granularity=86400&start={}&end={}"
UTC = dt.timezone.utc

def day(ts):
    return dt.datetime.fromtimestamp(ts, UTC).strftime("%Y-%m-%d")

def fetch(product, start_ts, end_ts):
    out = {}
    t = start_ts
    while t < end_ts:
        e = min(t + 299 * 86400, end_ts)
        url = API.format(product, dt.datetime.fromtimestamp(t, UTC).isoformat(), dt.datetime.fromtimestamp(e, UTC).isoformat())
        req = urllib.request.Request(url, headers={"User-Agent": "cryptkeep-paper-research"})
        for attempt in range(4):
            try:
                rows = json.load(urllib.request.urlopen(req, timeout=30)); break
            except Exception:
                if attempt == 3: raise
                time.sleep(2 * (attempt + 1))
        for ts, lo, hi, op, cl, vol in rows:
            out[int(ts)] = float(cl)
        t = e + 86400
        time.sleep(0.25)
    return out

def target(P, i):
    w = {}
    for a in ("BTC", "ETH"):
        r28 = P[a][i] / P[a][i - 28] - 1
        if r28 <= 0:
            continue
        rets = [P[a][k] / P[a][k - 1] - 1 for k in range(i - 29, i + 1)]
        vol = statistics.pstdev(rets) * math.sqrt(365)
        w[a] = 0.5 * min(1.0, 0.5 / vol)
    return w

def detail(P, i):
    d = {}
    for a in ("BTC", "ETH"):
        rets = [P[a][k] / P[a][k - 1] - 1 for k in range(i - 29, i + 1)]
        d[a] = {"close": P[a][i], "return_28d_pct": round((P[a][i] / P[a][i - 28] - 1) * 100, 2),
                "vol_30d_annual_pct": round(statistics.pstdev(rets) * math.sqrt(365) * 100, 1)}
    return d

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--start", default="2026-10-11")
    ap.add_argument("--fee", type=float, default=0.006)
    ap.add_argument("--slip", type=float, default=0.0005)
    a = ap.parse_args()
    now = int(time.time())
    last_complete = (now // 86400) * 86400 - 86400          # start of the last fully closed UTC day
    start_ts = int(dt.datetime.strptime(a.start, "%Y-%m-%d").replace(tzinfo=UTC).timestamp())
    from_ts = min(start_ts, last_complete) - 70 * 86400
    px = {"BTC": fetch("BTC-USD", from_ts, last_complete), "ETH": fetch("ETH-USD", from_ts, last_complete)}
    days = sorted(t for t in set(px["BTC"]) & set(px["ETH"]) if t <= last_complete)
    P = {k: [px[k][t] for t in days] for k in px}
    i_now = len(days) - 1
    w_now = target(P, i_now)
    state = {"artifact_type": "research_only_forward_paper_test", "places_orders": False,
             "rule": "BTC+ETH 28-day trend, vol-sized, weekly Sunday rebalance (majors.py primary)",
             "generated_utc": dt.datetime.fromtimestamp(now, UTC).isoformat(timespec="seconds"),
             "last_completed_day": day(days[i_now]),
             "today_signal": {"weights_if_rebalanced_now": {k: round(v, 4) for k, v in w_now.items()},
                              "cash_pct": round(100 * (1 - sum(w_now.values())), 1), "inputs": detail(P, i_now)},
             "fee": a.fee, "slippage": a.slip}
    i0 = next((i for i, t in enumerate(days) if t >= start_ts and dt.datetime.fromtimestamp(t, UTC).weekday() == 6), None)
    rows = []
    if i0 is None:
        state["paper"] = {"status": "waiting", "starts_at_close_of": "first Sunday on/after " + a.start}
    else:
        eq = 1000.0; w = {}; btc_units = 1000.0 / P["BTC"][i0]
        for i in range(i0, i_now + 1):
            if i > i0:
                r = sum(wt * (P[k][i] / P[k][i - 1] - 1) for k, wt in w.items()); eq *= 1 + r
                w = {k: wt * (P[k][i] / P[k][i - 1]) / (1 + r) for k, wt in w.items()}
            reb = dt.datetime.fromtimestamp(days[i], UTC).weekday() == 6
            cost = 0.0
            if reb:
                nw = target(P, i); turn = sum(abs(nw.get(k, 0) - w.get(k, 0)) for k in set(nw) | set(w))
                cost = eq * turn * (a.fee + a.slip); eq -= cost; w = nw
            rows.append({"date": day(days[i]), "btc_close": P["BTC"][i], "eth_close": P["ETH"][i], "rebalance": reb,
                         "w_btc": round(w.get("BTC", 0), 4), "w_eth": round(w.get("ETH", 0), 4), "cost_usd": round(cost, 2),
                         "equity_usd": round(eq, 2), "btc_hold_usd": round(btc_units * P["BTC"][i], 2)})
        v = [1000.0] + [r["equity_usd"] for r in rows]
        def pct(n):
            return round((v[-1] / v[-1 - n] - 1) * 100, 2) if len(v) > n else None
        pk = v[0]; mdd = 0
        for x in v: pk = max(pk, x); mdd = max(mdd, 1 - x / pk)
        state["paper"] = {"status": "running", "started_at_close_of": rows[0]["date"], "days": len(rows) - 1,
                          "equity_usd": rows[-1]["equity_usd"], "total_pct": round((v[-1] / 1000 - 1) * 100, 2),
                          "last_day_pct": pct(1), "last_7d_pct": pct(7), "last_30d_pct": pct(30),
                          "max_drawdown_pct": round(mdd * 100, 2), "btc_hold_usd": rows[-1]["btc_hold_usd"],
                          "holding_now": {"BTC": rows[-1]["w_btc"], "ETH": rows[-1]["w_eth"]},
                          "next_rebalance": "close of next Sunday daily candle (Monday 00:00 UTC)"}
    os.makedirs(a.out, exist_ok=True)
    json.dump(state, open(os.path.join(a.out, "paper_state.json"), "w"), indent=2)
    with open(os.path.join(a.out, "paper_ledger.csv"), "w", newline="") as f:
        cw = csv.DictWriter(f, fieldnames=["date", "btc_close", "eth_close", "rebalance", "w_btc", "w_eth", "cost_usd", "equity_usd", "btc_hold_usd"])
        cw.writeheader(); cw.writerows(rows)
    print(json.dumps(state, indent=2))

if __name__ == "__main__":
    main()
