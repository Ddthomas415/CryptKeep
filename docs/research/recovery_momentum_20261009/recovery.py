"""PRE-REGISTERED before the first run (2026-10-09). Research only. Binance spot daily, every USDT pair trading today.
Idea under test (the operator's): coins that were highly valued, crashed, and are now recovering with momentum.
Signal on a coin, using only data up to that day's close:
  - at least 365 days of history;
  - close is at least D below its highest close so far (D = 70% or 85%);
  - [variant] on the day of that highest close it ranked in the top 50 coins by 30-day average traded volume;
  - momentum: 28-day return >= M (M = +15% or +30%) and close above its 50-day average;
  - it trades at least $1M a day on average over the last 30 days.
Portfolio: $1,000 start, up to 10 positions, 10% of equity each at entry, entries at the signal day's close.
Exits: trailing stop T below the highest close since entry (T = 20% or 35%), or after 180 days.
Costs per side: fee 0.1% (Binance) and 0.6% (Coinbase limit orders) + 0.3% slippage.
Grid: 2 x 2 x 2 x 2 = 16 versions. TRAIN 2020-01-01..2023-12-31, TEST 2024-01-01..2026-10-08.
Selection rule set in advance: the version with the highest TRAIN return/risk (Sharpe) at the 0.6% fee is the one
judged on TEST. It counts as working only if its TEST return is positive and its TEST worst drop is under 60%.
Also reported: for every signal, the largest gain reached within 180 days, to show how often +100% / +300% happened.
Limits: coins delisted before today are missing (flatters results); highs before a coin's Binance history are unknown."""
import json, os, sys, math, statistics, datetime as dt, hashlib
import numpy as np
S = sys.argv[1]
files = sorted(os.listdir(f"{S}/bn/d1")); syms = [f[:-5] for f in files]
D0 = int(dt.datetime(2019, 1, 1, tzinfo=dt.timezone.utc).timestamp()); D1 = int(dt.datetime(2026, 10, 9, tzinfo=dt.timezone.utc).timestamp())
ND = (D1 - D0) // 86400; NS = len(syms)
C = np.full((ND, NS), np.nan); QV = np.zeros((ND, NS))
for j, f in enumerate(files):
    for ts, o, h, l, c, qv in json.load(open(f"{S}/bn/d1/{f}")):
        i = (ts - D0) // 86400
        if 0 <= i < ND: C[i, j] = c; QV[i, j] = qv
# forward-fill short gaps for marking
P = C.copy()
for i in range(1, ND):
    m = np.isnan(P[i]); P[i, m] = P[i - 1, m]
AGE = np.cumsum(~np.isnan(C), axis=0)
cs = np.cumsum(QV, axis=0); V30 = np.full_like(QV, np.nan); V30[30:] = (cs[30:] - cs[:-30]) / 30
RANK = np.full((ND, NS), 9999)
for i in range(30, ND):
    order = np.argsort(-np.nan_to_num(V30[i], nan=-1)); RANK[i, order] = np.arange(NS)
RMAX = np.full_like(P, np.nan); RANK_AT_MAX = np.full((ND, NS), 9999)
cur = np.full(NS, -np.inf); rk = np.full(NS, 9999)
for i in range(ND):
    c = C[i]; up = ~np.isnan(c) & (c > cur)
    cur[up] = c[up]; rk[up] = RANK[i, up]
    RMAX[i] = np.where(np.isinf(cur), np.nan, cur); RANK_AT_MAX[i] = rk
SMA50 = np.full_like(P, np.nan); cp = np.cumsum(np.nan_to_num(P), axis=0); SMA50[50:] = (cp[50:] - cp[:-50]) / 50
R28 = np.full_like(P, np.nan); R28[28:] = P[28:] / P[:-28] - 1
def signal(i, D, M, need_top50):
    ok = (AGE[i] >= 365) & ~np.isnan(C[i]) & (C[i] <= RMAX[i] * (1 - D)) & (R28[i] >= M) & (C[i] > SMA50[i]) & (V30[i] >= 1e6)
    if need_top50: ok &= RANK_AT_MAX[i] < 50
    return np.nonzero(ok)[0]
TS = lambda s: (int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp()) - D0) // 86400
def run(D, M, T, need_top50, fee, lo, hi, slip=0.003):
    cash = 1000.0; pos = {}; eq = []; trades = []
    for i in range(lo, hi + 1):
        for j in list(pos):
            p = pos[j]; px = P[i, j]; p["peak"] = max(p["peak"], px)
            if px <= p["peak"] * (1 - T) or i - p["in"] >= 180:
                got = p["q"] * px * (1 - slip) * (1 - fee); cash += got
                trades.append({"sym": syms[j], "in": p["in"], "out": i, "ret": got / p["cost"] - 1, "max_gain": p["peak"] / p["entry_px"] - 1}); del pos[j]
        if len(pos) < 10:
            val = cash + sum(p["q"] * P[i, j] for j, p in pos.items())
            for j in sorted(signal(i, D, M, need_top50), key=lambda j: -R28[i, j]):
                if len(pos) >= 10 or j in pos: continue
                usd = min(cash, val * 0.10)
                if usd < 1: break
                px = P[i, j]; pos[j] = {"q": usd / (1 + fee) / (px * (1 + slip)), "cost": usd, "in": i, "peak": px, "entry_px": px}; cash -= usd
        eq.append((i, cash + sum(p["q"] * P[i, j] for j, p in pos.items()), len(pos)))
    return eq, trades
def stats(eq, trades):
    v = [1000.0] + [x for _, x, _ in eq]; dr = [v[k] / v[k - 1] - 1 for k in range(1, len(v))]
    yrs = len(dr) / 365; pk = v[0]; mdd = 0
    for x in v: pk = max(pk, x); mdd = max(mdd, 1 - x / pk)
    sd = statistics.pstdev(dr); mo = {}
    for (i, _, _), r in zip(eq, dr): mo.setdefault(dt.datetime.fromtimestamp(D0 + i * 86400, dt.timezone.utc).strftime("%Y-%m"), []).append(r)
    mr = {k: (math.prod(1 + x for x in m) - 1) * 100 for k, m in mo.items()}
    rs = [t["ret"] for t in trades]; mg = [t["max_gain"] for t in trades]
    top = sorted(trades, key=lambda t: -t["ret"])[:8]
    f = lambda i: dt.datetime.fromtimestamp(D0 + i * 86400, dt.timezone.utc).strftime("%Y-%m-%d")
    return {"end_usd": round(v[-1], 2), "total_pct": round((v[-1] / 1000 - 1) * 100, 1), "cagr_pct": round(((v[-1] / 1000) ** (1 / yrs) - 1) * 100, 1),
            "max_drawdown_pct": round(mdd * 100, 1), "sharpe": round(statistics.mean(dr) / sd * math.sqrt(365), 2) if sd else 0,
            "positive_months_pct": round(100 * sum(1 for x in mr.values() if x > 0) / len(mr), 1), "worst_month_pct": round(min(mr.values()), 1), "best_month_pct": round(max(mr.values()), 1),
            "avg_positions": round(statistics.mean(n for _, _, n in eq), 1), "trades": len(rs),
            "win_pct": round(100 * sum(1 for r in rs if r > 0) / len(rs), 1) if rs else None, "avg_trade_pct": round(statistics.mean(rs) * 100, 1) if rs else None,
            "median_trade_pct": round(statistics.median(rs) * 100, 1) if rs else None,
            "trades_reaching_plus100pct": sum(1 for g in mg if g >= 1), "trades_reaching_plus300pct": sum(1 for g in mg if g >= 3),
            "trades_closed_above_plus100pct": sum(1 for r in rs if r >= 1),
            "monthly_pct": {k: round(x, 2) for k, x in mr.items()},
            "best_trades": [{"coin": t["sym"], "in": f(t["in"]), "out": f(t["out"]), "ret_pct": round(t["ret"] * 100, 1), "max_gain_pct": round(t["max_gain"] * 100, 1)} for t in top],
            "month_end_usd": {dt.datetime.fromtimestamp(D0 + i * 86400, dt.timezone.utc).strftime("%Y-%m"): round(x, 2) for i, x, _ in eq}}
TRAIN = (TS("2020-01-01"), TS("2023-12-31")); TEST = (TS("2024-01-01"), TS("2026-10-08"))
out = {"artifact_type": "research_only_recovery_momentum", "not_promotion_evidence": True, "pairs": NS,
       "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "results": []}
for D in (0.70, 0.85):
    for M in (0.15, 0.30):
        for T in (0.20, 0.35):
            for top in (True, False):
                for fee in (0.001, 0.006):
                    rec = {"drop_from_high": D, "momentum_28d": M, "trailing_stop": T, "former_top50": top, "fee": fee}
                    for part, (lo, hi) in (("train", TRAIN), ("test", TEST)):
                        e, t = run(D, M, T, top, fee, lo, hi); rec[part] = stats(e, t)
                    out["results"].append(rec)
        print(D, M, file=sys.stderr, flush=True)
cand = [r for r in out["results"] if r["fee"] == 0.006]
best = max(cand, key=lambda r: r["train"]["sharpe"])
out["selected"] = {k: best[k] for k in ("drop_from_high", "momentum_28d", "trailing_stop", "former_top50")}
out["selected_passes"] = best["test"]["total_pct"] > 0 and best["test"]["max_drawdown_pct"] < 60
# BTC benchmark over the same windows
b = syms.index("BTCUSDT")
out["btc_hold"] = {k: round((P[hi, b] / P[lo, b] - 1) * 100, 1) for k, (lo, hi) in (("train", TRAIN), ("test", TEST))}
print(json.dumps(out, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
