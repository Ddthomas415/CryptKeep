"""Research-only strategy search with an out-of-sample check, Coinbase spot, long only, every USD coin.
Data: hourly candles 2025-10-09 to 2026-10-09. TRAIN = entries before 2026-06-09, TEST = entries from 2026-06-09.
All strategy families, parameters, exits and the selection rule were fixed before the first run.
Entry: open of the hour after the signal hour (signal uses only completed hours). Exits use hourly high/low;
if target and stop fall in the same hour the stop is counted. Costs per side: fee (0.6% maker base case; 1.2%
taker stress case) plus slippage 0.1% at >=$2M/day traded, 0.5% below."""
import json, os, sys, math, statistics, datetime as dt, hashlib, itertools
import numpy as np
S = sys.argv[1]
START = int(dt.datetime(2025, 10, 9, tzinfo=dt.timezone.utc).timestamp()); END = int(dt.datetime(2026, 10, 9, tzinfo=dt.timezone.utc).timestamp())
SPLIT = int(dt.datetime(2026, 6, 9, tzinfo=dt.timezone.utc).timestamp())
NH = (END - START) // 3600
def load(d):
    out = {}
    for f in os.listdir(d):
        for r in json.load(open(f"{d}/{f}")): out.setdefault(f[:-5], {})[r[0]] = r
    return out
raw = load(f"{S}/cb2/h1"); r2 = load(f"{S}/cb/h1")
for k, v in r2.items(): raw.setdefault(k, {}).update(v)
coins = sorted(k for k, v in raw.items() if len(v) >= 24 * 40)
C = len(coins)
O = np.full((C, NH), np.nan); Hh = O.copy(); Lw = O.copy(); Cl = O.copy(); V = np.zeros((C, NH))
for ci, pid in enumerate(coins):
    for ts, o, h, l, c, v in raw[pid].values():
        i = (ts - START) // 3600
        if 0 <= i < NH: O[ci, i], Hh[ci, i], Lw[ci, i], Cl[ci, i], V[ci, i] = o, h, l, c, v * c
P = Cl.copy()   # forward-filled close for return calculations
for i in range(1, NH):
    m = np.isnan(P[:, i]); P[m, i] = P[m, i - 1]
PRES = ~np.isnan(Cl)
def lag(a, k):
    out = np.full_like(a, np.nan); out[:, k:] = a[:, :-k]; return out
def rollsum(a, w):
    cs = np.cumsum(np.nan_to_num(a), axis=1); out = np.full_like(a, np.nan, dtype=float)
    out[:, w:] = cs[:, w:] - cs[:, :-w]; out[:, w - 1] = cs[:, w - 1]; return out
def rollmax(a, w):
    out = np.full_like(a, np.nan)
    for i in range(w, a.shape[1]): out[:, i] = np.nanmax(a[:, i - w:i], axis=1)
    return out
USD7 = rollsum(V, 168) / 7                       # avg daily $ volume over the last 7 days (incl. hour i)
PRES7 = rollsum(PRES.astype(float), 168)
R1 = P / lag(P, 1) - 1; R24 = P / lag(P, 24) - 1; R7D = P / lag(P, 168) - 1; R30 = P / lag(P, 720) - 1
HI72 = rollmax(P, 72); HI720 = rollmax(P, 720)
V24 = rollsum(V, 24); V7prior = (rollsum(V, 168) - V24) / 6
bi = coins.index("BTC-USD")
btc = P[bi]; btc_ma50 = np.array([np.nan if i < 1200 else np.nanmean(btc[i - 1200:i + 1]) for i in range(NH)])
BTC_UP = btc > btc_ma50
MA20 = np.full_like(P, np.nan)
cs = np.cumsum(np.nan_to_num(P), axis=1); MA20[:, 480:] = (cs[:, 480:] - cs[:, :-480]) / 480
SIGNALS = {}
for x in (0.05, 0.10, 0.20): SIGNALS[f"pump_1h_ge_{int(x*100)}pct"] = R1 >= x
for t, d in itertools.product((0.10, 0.30), (0.05, 0.10, 0.20)): SIGNALS[f"dip_{int(d*100)}pct_in_30d_uptrend_ge_{int(t*100)}pct"] = (R30 >= t) & (P <= HI72 * (1 - d))
for x in (0.10, 0.20): SIGNALS[f"drop_24h_ge_{int(x*100)}pct"] = R24 <= -x
for m in (2, 3): SIGNALS[f"breakout_30d_high_vol_{m}x"] = (P > HI720) & (V24 >= m * V7prior)
for x in (0.08, 0.15): SIGNALS[f"lags_btc_24h_by_{int(x*100)}pct"] = (R24 - R24[bi]) <= -x
SIGNALS["trend_above_20d_avg_and_7d_up"] = (P > MA20) & (R7D > 0) & ~((lag(P, 24) > lag(MA20, 24)) & (lag(R7D, 24) > 0))
EXITS = {"hold_24h": (None, None, 24, None), "hold_72h": (None, None, 72, None), "tp10_sl5_24h": (0.10, 0.05, 24, None),
         "tp10_sl10_7d": (0.10, 0.10, 168, None), "tp20_sl10_3d": (0.20, 0.10, 72, None), "trail8_3d": (None, None, 72, 0.08), "trail15_7d": (None, None, 168, 0.15)}
def exit_ret(ci, i, tp, sl, max_h, trail):
    """Entry at open of hour i+1. Returns gross return or None."""
    e = O[ci, i + 1]
    if not (e > 0): return None
    peak = e
    for j in range(i + 1, min(NH, i + 1 + max_h)):
        if not PRES[ci, j]: continue
        stop = e * (1 - sl) if sl else None
        if trail: stop = max(stop or 0.0, peak * (1 - trail))
        if stop and Lw[ci, j] <= stop: return min(stop, O[ci, j]) / e - 1 if O[ci, j] < stop else stop / e - 1
        if tp and Hh[ci, j] >= e * (1 + tp): return tp
        peak = max(peak, Hh[ci, j])
    j = min(NH - 1, i + max_h)
    if i + 1 + max_h > NH - 1: return None
    return P[ci, j] / e - 1
def month(i): return dt.datetime.fromtimestamp(START + i * 3600, dt.timezone.utc).strftime("%Y-%m")
results = []
for sname, sig in SIGNALS.items():
    for regime in ("any", "btc_above_50d"):
        for liq in (2e6, 2.5e5):
            ok = sig & (USD7 >= liq) & (PRES7 >= 0.9 * 168) & PRES
            if regime == "btc_above_50d": ok &= BTC_UP[None, :]
            ok[:, :721] = False; ok[:, NH - 2:] = False
            ok[bi, :] = ok[bi, :] if sname.startswith("trend") else False
            ev = []
            for ci in range(C):
                idx = np.nonzero(ok[ci])[0]; last = -10 ** 9
                for i in idx:
                    if i - last >= 24: ev.append((ci, int(i))); last = i
            if not ev: continue
            for ename, spec in EXITS.items():
                rows = []
                for ci, i in ev:
                    g = exit_ret(ci, i, *spec)
                    if g is None: continue
                    slip = 0.001 if USD7[ci, i] >= 2e6 else 0.005
                    rows.append((i, g, slip))
                for fee in (0.006, 0.012):
                    rec = {"signal": sname, "regime": regime, "min_daily_usd": liq, "exit": ename, "fee": fee}
                    for part, sel in (("train", lambda i: START + i * 3600 < SPLIT), ("test", lambda i: START + i * 3600 >= SPLIT)):
                        xs = [((1 + g) * (1 - s) * (1 - fee)) / ((1 + s) * (1 + fee)) - 1 for i, g, s in rows if sel(i)]
                        mon = {}
                        for (i, g, s), x in zip([r for r in rows if sel(r[0])], xs): mon.setdefault(month(i), []).append(x)
                        rec[part] = {"n": len(xs), "mean_pct": round(statistics.mean(xs) * 100, 3) if xs else None,
                                     "median_pct": round(statistics.median(xs) * 100, 3) if xs else None,
                                     "win_pct": round(100 * sum(1 for x in xs if x > 0) / len(xs), 1) if xs else None,
                                     "months": len(mon), "months_positive": sum(1 for v in mon.values() if sum(v) > 0),
                                     "sum_pct": round(sum(xs) * 100, 1)}
                    results.append(rec)
    print(sname, file=sys.stderr, flush=True)
def passes(r):
    t = r["train"]; return t["n"] >= 40 and t["mean_pct"] > 0 and t["months"] > 0 and t["months_positive"] / t["months"] >= 0.6
base = [r for r in results if r["fee"] == 0.006]
sel = [r for r in base if passes(r)]
out = {"artifact_type": "research_only_strategy_search", "not_promotion_evidence": True, "coins": C,
       "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "combinations_tested": len(base),
       "selection_rule": "train: n>=40, mean net > 0, positive in >=60% of months (0.6% fee base case)",
       "selected": sel, "results": results}
print(json.dumps(out))
