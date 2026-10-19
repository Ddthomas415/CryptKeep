"""Research-only: momentum and hybrid strategies from published crypto research, on Binance spot daily data.
Strategies, parameters, train/test split and costs were fixed before the first run.
Point-in-time universe: at each weekly rebalance (Sunday close, 00:00 UTC) the top coins by trailing 30-day USDT
volume among pairs with at least 120 days of history. Weights set at that close earn the following days' returns.
Costs on turnover: fee per side (0.1% Binance base, 0.6% Coinbase maker) + 0.05% slippage.
Limit: only pairs trading today are included (delisted coins missing), which flatters results."""
import json, os, sys, math, statistics, datetime as dt, hashlib
import numpy as np
S = sys.argv[1]
files = sorted(os.listdir(f"{S}/bn/d1")); syms = [f[:-5] for f in files]
D0 = int(dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc).timestamp()); D1 = int(dt.datetime(2026, 10, 9, tzinfo=dt.timezone.utc).timestamp())
ND = (D1 - D0) // 86400
C = np.full((ND, len(syms)), np.nan); QV = np.zeros((ND, len(syms)))
for j, f in enumerate(files):
    for ts, o, h, l, c, qv in json.load(open(f"{S}/bn/d1/{f}")):
        i = (ts - D0) // 86400
        if 0 <= i < ND: C[i, j] = c; QV[i, j] = qv
R = np.full_like(C, np.nan); R[1:] = C[1:] / C[:-1] - 1
R = np.where(np.abs(R) > 5, np.nan, R)      # drop data errors above +500% in a day
AGE = np.cumsum(~np.isnan(C), axis=0)
def trail_ret(i, L): return C[i] / C[i - L] - 1
def vol30(i): return np.nanstd(R[i - 29:i + 1], axis=0) * math.sqrt(365)
BTC = syms.index("BTCUSDT")
def universe(i, n):
    ok = (AGE[i] >= 120) & ~np.isnan(C[i])
    v = np.where(ok, np.nanmean(QV[i - 29:i + 1], axis=0), -1)
    idx = np.argsort(-v)[:n]; return [j for j in idx if v[j] > 0]
def btc_up(i): return C[i, BTC] > np.nanmean(C[i - 99:i + 1, BTC])
def weights(name, L, i):
    if name == "btc_hold": return {BTC: 1.0}
    if name == "equal_weight_top20":
        u = universe(i, 20); return {j: 1 / len(u) for j in u}
    if name.startswith("trend_each_coin"):
        u = universe(i, 20); r = trail_ret(i, L); vol = vol30(i); w = {}
        for j in u:
            if r[j] > 0:
                w[j] = 1 / 20 * (min(1.0, 0.5 / vol[j]) if "vol_scaled" in name and vol[j] > 0 else 1.0)
        return w
    if name.startswith("top5_momentum"):
        if "btc_filter" in name and not btc_up(i): return {}
        u = universe(i, 30); r = C[i - 1] / C[i - 1 - L] - 1   # skip the most recent day
        ranked = sorted((r[j], j) for j in u if not np.isnan(r[j]))[::-1][:5]
        return {j: 1 / 5 for _, j in ranked if _ > 0}
    if name.startswith("hybrid"):
        if not btc_up(i): return {}
        u = universe(i, 30); r = C[i - 1] / C[i - 1 - L] - 1; rL = trail_ret(i, L); vol = vol30(i)
        ranked = [j for _, j in sorted((r[j], j) for j in u if not np.isnan(r[j]))[::-1][:5] if rL[j] > 0]
        return {j: 1 / 5 * min(1.0, 0.5 / vol[j]) for j in ranked if vol[j] > 0}
STRATS = [("btc_hold", 0), ("equal_weight_top20", 0)] + [(f"{n}_{L}d", L) for L in (28, 90) for n in
          ("trend_each_coin", "trend_each_coin_vol_scaled", "top5_momentum", "top5_momentum_btc_filter", "hybrid_momentum_trend_btc_filter_vol_scaled")]
START = (int(dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc).timestamp()) - D0) // 86400
SPLIT = int(dt.datetime(2024, 1, 1, tzinfo=dt.timezone.utc).timestamp())
def run(name, L, fee, slip=0.0005):
    w = {}; eq = 1000.0; curve = []; turnover = 0.0; expo = []
    for i in range(START, ND - 1):
        day = dt.datetime.fromtimestamp(D0 + i * 86400, dt.timezone.utc)
        if day.weekday() == 6 or i == START:                 # Sunday close
            nw = weights(name.rsplit("_", 1)[0] if L else name, L, i)
            if name == "btc_hold" and w: nw = w
            t = sum(abs(nw.get(j, 0) - w.get(j, 0)) for j in set(nw) | set(w))
            eq *= 1 - t * (fee + slip); turnover += t; w = nw
        r = sum(wt * (R[i + 1, j] if not np.isnan(R[i + 1, j]) else 0.0) for j, wt in w.items())
        eq *= 1 + r
        tot = sum(w.values()); w = {j: wt * (1 + (R[i + 1, j] if not np.isnan(R[i + 1, j]) else 0.0)) / (1 + r) for j, wt in w.items()} if tot else {}
        curve.append((D0 + (i + 1) * 86400, eq)); expo.append(tot)
    return curve, turnover, expo
def stats(curve, lo, hi):
    pts = [(t, v) for t, v in curve if lo <= t < hi]
    if len(pts) < 30: return None
    base = [v for t, v in curve if t < lo]; v0 = base[-1] if base else 1000.0
    vals = [v0] + [v for _, v in pts]; dr = [vals[k] / vals[k - 1] - 1 for k in range(1, len(vals))]
    yrs = len(dr) / 365; cagr = (vals[-1] / vals[0]) ** (1 / yrs) - 1
    pk = vals[0]; mdd = 0
    for v in vals: pk = max(pk, v); mdd = max(mdd, 1 - v / pk)
    sd = statistics.pstdev(dr); sharpe = statistics.mean(dr) / sd * math.sqrt(365) if sd else 0
    mo = {}
    for (t, _), r in zip(pts, dr): mo.setdefault(dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m"), []).append(r)
    mr = {k: (math.prod(1 + x for x in v) - 1) * 100 for k, v in mo.items()}
    wk = {}
    for (t, _), r in zip(pts, dr): wk.setdefault(dt.datetime.fromtimestamp(t, dt.timezone.utc).isocalendar()[:2], []).append(r)
    wr = [math.prod(1 + x for x in v) - 1 for v in wk.values()]
    return {"total_pct": round((vals[-1] / vals[0] - 1) * 100, 1), "cagr_pct": round(cagr * 100, 1), "max_drawdown_pct": round(mdd * 100, 1),
            "sharpe": round(sharpe, 2), "mean_daily_pct": round(statistics.mean(dr) * 100, 3), "median_daily_pct": round(statistics.median(dr) * 100, 3),
            "mean_weekly_pct": round(statistics.mean(wr) * 100, 2), "positive_weeks_pct": round(100 * sum(1 for x in wr if x > 0) / len(wr), 1),
            "mean_monthly_pct": round(statistics.mean(mr.values()), 2), "positive_months_pct": round(100 * sum(1 for x in mr.values() if x > 0) / len(mr), 1),
            "worst_month_pct": round(min(mr.values()), 1), "best_month_pct": round(max(mr.values()), 1), "monthly_pct": {k: round(v, 2) for k, v in mr.items()}}
T0 = D0 + START * 86400; TEND = D1
out = {"artifact_type": "research_only_hybrid_momentum", "not_promotion_evidence": True, "pairs": len(syms),
       "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "train": "2020-01-01..2023-12-31", "test": "2024-01-01..2026-10-08", "results": []}
for name, L in STRATS:
    for fee in (0.001, 0.006):
        curve, to, ex = run(name, L, fee)
        out["results"].append({"strategy": name, "fee": fee, "avg_exposure_pct": round(100 * statistics.mean(ex), 1), "annual_turnover": round(to / (len(curve) / 365), 1),
                               "train": stats(curve, T0, SPLIT), "test": stats(curve, SPLIT, TEND), "full": stats(curve, T0, TEND),
                               "equity_month_end": {dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m"): round(v, 2) for t, v in curve}})
    print(name, file=sys.stderr, flush=True)
print(json.dumps(out))
