"""Diagnostics and portfolio simulation for the one family that passed training:
breakout to a new 30-day high with 24h volume >= 3x (and 2x) the prior 6-day daily average, BTC above its
50-day average, coin trading >= $2M/day. Hold 72 hours. Everything else as in search.py."""
import sys, json, math, statistics, random, datetime as dt
S = sys.argv[1]; sys.argv = ["search.py", S]
src = open(f"{S}/code/search.py").read().split("EXITS = {")[0]
exec(src)
def events(mult):
    ok = (P > HI720) & (V24 >= mult * V7prior) & (USD7 >= 2e6) & (PRES7 >= 0.9 * 168) & PRES & BTC_UP[None, :]
    ok[:, :721] = False; ok[:, NH - 2:] = False; ok[bi, :] = False
    ev = []
    for ci in range(C):
        last = -10 ** 9
        for i in np.nonzero(ok[ci])[0]:
            if i - last >= 24: ev.append((int(i), ci)); last = i
    return sorted(ev)
def trade(ci, i, hold, fee):
    e = O[ci, i + 1]; j = i + hold
    if j >= NH or not (e > 0): return None
    x = P[ci, j] / e
    s = 0.001
    return x * (1 - s) * (1 - fee) / ((1 + s) * (1 + fee)) - 1
out = {}
for mult in (3, 2):
    ev = events(mult)
    for fee in (0.006, 0.012):
        for part, lo, hi in (("train", 0, (SPLIT - START) // 3600), ("test", (SPLIT - START) // 3600, NH)):
            xs = [(i, ci, trade(ci, i, 72, fee)) for i, ci in ev if lo <= i < hi]
            xs = [x for x in xs if x[2] is not None]
            r = sorted((x[2] for x in xs), reverse=True)
            random.seed(1); bs = sorted(statistics.mean(random.choices(r, k=len(r))) for _ in range(5000))
            days = {}
            for i, ci, x in xs: days.setdefault(i // 24, []).append(x)
            out[f"vol{mult}x_fee{fee}_{part}"] = {"n": len(r), "mean_pct": round(statistics.mean(r) * 100, 2), "median_pct": round(statistics.median(r) * 100, 2),
                "win_pct": round(100 * sum(1 for x in r if x > 0) / len(r), 1), "mean_without_top5_pct": round(statistics.mean(r[5:]) * 100, 2),
                "bootstrap_95pct_interval_of_mean": [round(bs[125] * 100, 2), round(bs[4875] * 100, 2)],
                "distinct_entry_days": len(days), "best_pct": round(r[0] * 100, 1), "worst_pct": round(r[-1] * 100, 1),
                "top5": [(coins[ci], dt.datetime.fromtimestamp(START + i * 3600, dt.timezone.utc).strftime("%Y-%m-%d %H:00"), round(x * 100, 1)) for i, ci, x in sorted(xs, key=lambda t: -t[2])[:5]]}
# portfolio: up to 5 positions, 20% of equity each at entry, exit after 72h, $1,000 start
def portfolio(mult, fee, lo, hi, slots=5):
    ev = [e for e in events(mult) if lo <= e[0] < hi]; evs = {}
    for i, ci in ev: evs.setdefault(i, []).append(ci)
    cash = 1000.0; pos = []; eq = []
    for i in range(lo, min(hi + 72, NH - 1)):
        for p in [p for p in pos if i >= p["exit"]]:
            cash += p["q"] * P[p["ci"], i] * (1 - 0.001) * (1 - fee); pos.remove(p)
        if i < hi:
            for ci in evs.get(i - 1, []):     # signal at i-1, enter at open of i
                if len(pos) >= slots or any(p["ci"] == ci for p in pos): continue
                val = cash + sum(p["q"] * P[p["ci"], i - 1] for p in pos)
                usd = min(cash, val / slots); e = O[ci, i]
                if not (e > 0) or usd < 1: continue
                pos.append({"ci": ci, "q": usd / (1 + fee) / (e * 1.001), "exit": i + 71}); cash -= usd
        eq.append((START + i * 3600, cash + sum(p["q"] * P[p["ci"], i] for p in pos)))
    by = {}
    for t, v in eq: by[dt.datetime.fromtimestamp(t, dt.timezone.utc).date()] = v
    ds = sorted(by); prev = 1000.0; dr = []
    for d in ds: dr.append(by[d] / prev - 1); prev = by[d]
    wk = {}; mo = {}
    for d, r in zip(ds, dr): wk.setdefault(d.isocalendar()[:2], []).append(r); mo.setdefault(d.strftime("%Y-%m"), []).append(r)
    comp = lambda v: (math.prod(1 + x for x in v) - 1) * 100
    pk = 0; mdd = 0
    for _, v in eq: pk = max(pk, v); mdd = max(mdd, (pk - v) / pk)
    wr = [comp(v) for v in wk.values()]
    return {"start": str(ds[0]), "end": str(ds[-1]), "final_usd": round(eq[-1][1], 2), "net_pct": round((eq[-1][1] / 1000 - 1) * 100, 2), "max_drawdown_pct": round(mdd * 100, 1),
            "days_in_market_pct": None, "mean_daily_pct": round(statistics.mean(dr) * 100, 3), "median_daily_pct": round(statistics.median(dr) * 100, 3),
            "positive_days_pct": round(100 * sum(1 for x in dr if x > 0) / len(dr), 1), "flat_days_pct": round(100 * sum(1 for x in dr if x == 0) / len(dr), 1),
            "best_day_pct": round(max(dr) * 100, 2), "worst_day_pct": round(min(dr) * 100, 2), "mean_weekly_pct": round(statistics.mean(wr), 2),
            "positive_weeks": f"{sum(1 for x in wr if x > 0)}/{len(wr)}", "monthly_pct": {k: round(comp(v), 2) for k, v in mo.items()},
            "daily_usd": {str(d): round(by[d], 2) for d in ds}}
split = (SPLIT - START) // 3600
port = {}
for mult in (3, 2):
    for fee in (0.006, 0.012):
        port[f"vol{mult}x_fee{fee}_test"] = portfolio(mult, fee, split, NH - 73)
        port[f"vol{mult}x_fee{fee}_full_year"] = portfolio(mult, fee, 721, NH - 73)
btc_test = (P[bi, NH - 74] / P[bi, split] - 1) * 100; btc_full = (P[bi, NH - 74] / P[bi, 721] - 1) * 100
print(json.dumps({"trade_stats": out, "portfolio": port, "btc_hold_pct": {"test": round(btc_test, 2), "full_year": round(btc_full, 2)},
                  "btc_regime_on_pct": {"train": round(100 * float(np.nanmean(BTC_UP[1200:split])), 1), "test": round(100 * float(np.nanmean(BTC_UP[split:])), 1)}}))
