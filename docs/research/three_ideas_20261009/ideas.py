"""PRE-REGISTERED before the first run (2026-10-09). Research only. Three remaining ideas, Binance spot daily, every USDT pair.
Common: $1,000 start; costs per side fee 0.1% or 0.6% + 0.3% slippage; TRAIN 2020-01-01..2023-12-31, TEST 2024-01-01..2026-10-08.
Selection per idea set in advance: highest TRAIN Sharpe at 0.6% fee. That version PASSES only if TEST return > 0,
TEST worst drop < 60%, and TEST end value beats BTC buy-and-hold over TEST. Coins delisted before today are missing (flatters
all three, most of all new listings, where many coins die).

IDEA 1 NEW LISTINGS. A coin's first Binance daily candle after 2019-03-01 is its listing day.
  Buy at the close of its E-th trading day (E = 1, 7 or 30). Variant H: only if that close is above the listing-day close.
  Liquidity: average daily volume since listing >= $1M. Up to 10 positions, 10% of equity each, ranked by volume.
  Exit after N days (N = 30 or 90). Grid 3 x 2 x 2 = 12.
IDEA 2 EARLY ACCUMULATION (volume rising before price moves). Signal: 30-day average volume >= K x the average of the
  90 days before that (K = 2 or 3); 30-day price change within +/-B (B = 10% or 20%); close above 50-day average;
  >= 365 days history; 30-day volume >= $1M/day. Up to 10 positions at 10%, ranked by volume ratio.
  Exit: trailing stop T from highest close (T = 20% or 35%) or 90 days. Grid 2 x 2 x 2 = 8.
IDEA 3 SMALL-COIN TREND BASKET, STRICT SIZING. Universe each day: coins ranked R by 30-day volume (R = 51-150 or 151-300),
  >= 365 days history. Hold a coin when its L-day return > 0 and close > 50-day average (L = 28 or 56).
  Weight = min(5%, 0.4% / its 30-day daily volatility); total capped at 100%, rest in cash. Rebalance every 7 days;
  costs charged on traded amount. Grid 2 x 2 = 4."""
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

B = syms.index("BTCUSDT")
TS = lambda s: (int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp()) - D0) // 86400
TRAIN = (TS("2020-01-01"), TS("2023-12-31")); TEST = (TS("2024-01-01"), TS("2026-10-08"))
FIRST = np.array([int(np.argmax(~np.isnan(C[:, j]))) for j in range(NS)])
CQ = np.cumsum(QV, axis=0)
SLIP = 0.003
def events(sigfn, keyfn, T, H, fee, lo, hi):
    cash = 1000.0; pos = {}; eq = []; trades = []
    for i in range(lo, hi + 1):
        for j in list(pos):
            p = pos[j]; px = P[i, j]; p["peak"] = max(p["peak"], px)
            if (T and px <= p["peak"] * (1 - T)) or i - p["in"] >= H:
                got = p["q"] * px * (1 - SLIP) * (1 - fee); cash += got
                trades.append({"sym": syms[j], "in": p["in"], "out": i, "ret": got / p["cost"] - 1, "max_gain": p["peak"] / p["entry_px"] - 1}); del pos[j]
        if len(pos) < 10:
            val = cash + sum(p["q"] * P[i, j] for j, p in pos.items())
            for j in sorted(sigfn(i), key=lambda j: -keyfn(i, j)):
                if len(pos) >= 10 or j in pos: continue
                usd = min(cash, val * 0.10)
                if usd < 1: break
                px = P[i, j]; pos[j] = {"q": usd / (1 + fee) / (px * (1 + SLIP)), "cost": usd, "in": i, "peak": px, "entry_px": px}; cash -= usd
        eq.append((i, cash + sum(p["q"] * P[i, j] for j, p in pos.items()), len(pos)))
    return eq, trades
# IDEA 1
def listing_sig(E, hold_up):
    def f(i):
        ok = (AGE[i] == E) & ~np.isnan(C[i]) & (FIRST > TS("2019-03-01"))
        js = np.nonzero(ok)[0]; res = []
        for j in js:
            avgv = (CQ[i, j] - (CQ[FIRST[j] - 1, j] if FIRST[j] > 0 else 0)) / E
            if avgv < 1e6: continue
            if hold_up and not C[i, j] > C[FIRST[j], j]: continue
            res.append(j)
        return res
    return f
# IDEA 2
V90p = np.full_like(QV, np.nan); V90p[120:] = (cs[90:-30] - cs[:-120]) / 90
R30 = np.full_like(P, np.nan); R30[30:] = P[30:] / P[:-30] - 1
def accum_sig(K, Bd):
    def f(i):
        with np.errstate(invalid="ignore", divide="ignore"):
            ok = (AGE[i] >= 365) & ~np.isnan(C[i]) & (V30[i] >= K * V90p[i]) & (V90p[i] > 0) & (np.abs(R30[i]) <= Bd) & (C[i] > SMA50[i]) & (V30[i] >= 1e6)
        return np.nonzero(ok)[0]
    return f
accum_key = lambda i, j: V30[i, j] / V90p[i, j]
# IDEA 3
LR = np.log(P); DR = np.full_like(P, np.nan); DR[1:] = LR[1:] - LR[:-1]
VOL30 = np.full_like(P, np.nan)
for i in range(31, ND): VOL30[i] = np.nanstd(DR[i - 29:i + 1], axis=0)
def basket(L, rlo, rhi, fee, lo, hi):
    RL = np.full_like(P, np.nan); RL[L:] = P[L:] / P[:-L] - 1
    w = np.zeros(NS); val = 1000.0; eq = []; tcount = 0; hold_days = []
    for i in range(lo, hi + 1):
        if i > lo:
            r = np.nan_to_num(P[i] / P[i - 1] - 1); val *= 1 + float(w @ r)
            w = w * (1 + r) / (1 + float(w @ r)) if (1 + float(w @ r)) > 0 else w
        if (i - lo) % 7 == 0:
            with np.errstate(invalid="ignore", divide="ignore"):
                ok = (AGE[i] >= 365) & ~np.isnan(C[i]) & (RANK[i] >= rlo - 1) & (RANK[i] <= rhi - 1) & (RL[i] > 0) & (C[i] > SMA50[i]) & (VOL30[i] > 0)
                nw = np.where(ok, np.minimum(0.05, 0.004 / VOL30[i]), 0.0)
            nw = np.nan_to_num(nw)
            if nw.sum() > 1: nw /= nw.sum()
            turn = float(np.abs(nw - w).sum()); val *= 1 - turn * (fee + SLIP); tcount += int(((nw > 0) & (w == 0)).sum()); w = nw
            hold_days.append(int((w > 0).sum()))
        eq.append((i, val, int((w > 0).sum())))
    return eq, tcount, float(np.mean(w.sum() for _ in [0])) if False else statistics.mean(hold_days)
def bstats(eq, entries):
    v = [1000.0] + [x for _, x, _ in eq]; dr = [v[k] / v[k - 1] - 1 for k in range(1, len(v))]
    yrs = len(dr) / 365; pk = v[0]; mdd = 0
    for x in v: pk = max(pk, x); mdd = max(mdd, 1 - x / pk)
    sd = statistics.pstdev(dr); mo = {}
    for (i, _, _), r in zip(eq, dr): mo.setdefault(dt.datetime.fromtimestamp(D0 + i * 86400, dt.timezone.utc).strftime("%Y-%m"), []).append(r)
    mr = {k: (math.prod(1 + x for x in m) - 1) * 100 for k, m in mo.items()}
    return {"end_usd": round(v[-1], 2), "total_pct": round((v[-1] / 1000 - 1) * 100, 1), "cagr_pct": round(((v[-1] / 1000) ** (1 / yrs) - 1) * 100, 1),
            "max_drawdown_pct": round(mdd * 100, 1), "sharpe": round(statistics.mean(dr) / sd * math.sqrt(365), 2) if sd else 0,
            "positive_months_pct": round(100 * sum(1 for x in mr.values() if x > 0) / len(mr), 1), "worst_month_pct": round(min(mr.values()), 1), "best_month_pct": round(max(mr.values()), 1),
            "avg_positions": round(statistics.mean(n for _, _, n in eq), 1), "new_entries": entries,
            "monthly_pct": {k: round(x, 2) for k, x in mr.items()},
            "month_end_usd": {dt.datetime.fromtimestamp(D0 + i * 86400, dt.timezone.utc).strftime("%Y-%m"): round(x, 2) for i, x, _ in eq}}
out = {"artifact_type": "research_only_three_ideas", "not_promotion_evidence": True, "pairs": NS,
       "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "ideas": {}}
out["btc_hold"] = {k: round((P[hi, B] / P[lo, B] - 1) * 100, 1) for k, (lo, hi) in (("train", TRAIN), ("test", TEST))}
def finish(name, res):
    best = max([r for r in res if r["fee"] == 0.006], key=lambda r: r["train"]["sharpe"])
    t = best["test"]
    out["ideas"][name] = {"results": res, "selected": {k: v for k, v in best.items() if k not in ("train", "test", "fee")},
        "selected_passes": bool(t["total_pct"] > 0 and t["max_drawdown_pct"] < 60 and t["total_pct"] > out["btc_hold"]["test"])}
res = []
for E in (1, 7, 30):
    for hu in (False, True):
        for N in (30, 90):
            for fee in (0.001, 0.006):
                rec = {"entry_day": E, "only_if_above_listing_close": hu, "hold_days": N, "fee": fee}
                for part, (lo, hi) in (("train", TRAIN), ("test", TEST)):
                    e, t = events(listing_sig(E, hu), lambda i, j: V30[i, j] if not np.isnan(V30[i, j]) else QV[i, j], None, N, fee, lo, hi); rec[part] = stats(e, t)
                res.append(rec)
finish("new_listings", res); print("1", file=sys.stderr, flush=True)
res = []
for K in (2, 3):
    for Bd in (0.10, 0.20):
        for T in (0.20, 0.35):
            for fee in (0.001, 0.006):
                rec = {"volume_ratio": K, "flat_band": Bd, "trailing_stop": T, "fee": fee}
                for part, (lo, hi) in (("train", TRAIN), ("test", TEST)):
                    e, t = events(accum_sig(K, Bd), accum_key, T, 90, fee, lo, hi); rec[part] = stats(e, t)
                res.append(rec)
finish("early_accumulation", res); print("2", file=sys.stderr, flush=True)
res = []
for L in (28, 56):
    for rlo, rhi in ((51, 150), (151, 300)):
        for fee in (0.001, 0.006):
            rec = {"lookback": L, "volume_rank_band": f"{rlo}-{rhi}", "fee": fee}
            for part, (lo, hi) in (("train", TRAIN), ("test", TEST)):
                e, n, h = basket(L, rlo, rhi, fee, lo, hi); rec[part] = bstats(e, n); rec[part]["avg_coins_held"] = round(h, 1)
            res.append(rec)
finish("small_coin_basket", res); print("3", file=sys.stderr, flush=True)
print(json.dumps(out, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
