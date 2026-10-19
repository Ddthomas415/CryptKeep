"""PRE-REGISTERED before the first run (2026-10-09). Research only. Not promotion evidence.
Question: does applying the rule that passed (majors.py: 28-day trend, volatility-sized, weekly) to the 10 largest coins
add profit over applying it to BTC+ETH only?
Data: Binance spot daily USDT pairs, EVERY pair ever listed including delisted ones (fetch_bn_all.py), 2017-08-01..2026-10-08.
"Largest" = highest 30-day average traded volume in USDT (market-cap history is not available from a free source),
among coins with a candle that day and >= 60 days of history. Stablecoins, fiat, wrapped and leveraged tokens excluded.
Rule, at the close of every Sunday daily candle: universe = top N coins by 30-day volume. For each coin in the universe,
  if its 28-day return > 0: weight = (1/N) * min(1, 0.50 / annualised 30-day volatility); else 0. Rest in cash. No leverage.
  Coins leaving the universe are sold. A delisted coin is valued at its last close until the next Sunday, then sold there.
Primary: N = 10. Secondary (reported, not used to decide): N = 5, N = 20.
Comparisons: the same rule on BTC+ETH only (0.5 each, as majors.py); hold BTC; hold the top-N equal-weighted, weekly.
Costs per side on traded amount: fee 0.1% and 0.6%; slippage 0.10% for top-N versions, 0.05% for BTC/ETH.
Windows: A 2018-01-01..2019-12-31, B 2020-01-01..2023-12-31, C 2024-01-01..2026-10-08.
Decision set in advance, at 0.6% fee: top-10 is worth adding only if (1) its end value beats the BTC+ETH rule in at least
2 of the 3 windows, one of which must be C, and (2) its worst drop is at most 10 points worse than the BTC+ETH rule
in every window."""
import json, os, sys, math, statistics, datetime as dt, hashlib
import numpy as np
S = sys.argv[1]
files = sorted(os.listdir(f"{S}/bn_all/d1")); syms = [f[:-5] for f in files]
D0 = int(dt.datetime(2017, 8, 1, tzinfo=dt.timezone.utc).timestamp()); D1 = int(dt.datetime(2026, 10, 9, tzinfo=dt.timezone.utc).timestamp())
ND = (D1 - D0) // 86400; NS = len(syms)
C = np.full((ND, NS), np.nan); QV = np.zeros((ND, NS))
for j, f in enumerate(files):
    for ts, o, h, l, c, qv in json.load(open(f"{S}/bn_all/d1/{f}")):
        i = (ts - D0) // 86400
        if 0 <= i < ND: C[i, j] = c; QV[i, j] = qv
P = C.copy()
for i in range(1, ND):
    m = np.isnan(P[i]); P[i, m] = P[i - 1, m]
AGE = np.cumsum(~np.isnan(C), axis=0)
cs = np.cumsum(QV, axis=0); V30 = np.full_like(QV, np.nan); V30[30:] = (cs[30:] - cs[:-30]) / 30
R28 = np.full_like(P, np.nan); R28[28:] = P[28:] / P[:-28] - 1
DR = np.full_like(P, np.nan); DR[1:] = P[1:] / P[:-1] - 1
VOL = np.full_like(P, np.nan)
for i in range(31, ND):
    VOL[i] = np.nanstd(DR[i - 29:i + 1], axis=0) * math.sqrt(365)
BTC, ETH = syms.index("BTCUSDT"), syms.index("ETHUSDT")
SUN = [dt.datetime.fromtimestamp(D0 + i * 86400, dt.timezone.utc).weekday() == 6 for i in range(ND)]
def topn(i, N):
    ok = ~np.isnan(C[i]) & (AGE[i] >= 60) & ~np.isnan(V30[i])
    idx = np.nonzero(ok)[0]
    return list(idx[np.argsort(-V30[i, idx])][:N])
def target(rule, N, i):
    if rule == "hold_btc": return {BTC: 1.0}
    if rule == "btc_eth_trend": members, base = [BTC, ETH], 0.5
    else: members, base = topn(i, N), 1.0 / N
    if rule == "hold_topn": return {j: base for j in members}
    w = {}
    for j in members:
        if R28[i, j] > 0 and VOL[i, j] > 0: w[j] = base * min(1.0, 0.5 / VOL[i, j])
    return w
def run(rule, N, fee, lo, hi):
    slip = 0.0005 if rule in ("btc_eth_trend", "hold_btc") else 0.001
    eq = 1000.0; w = {}; curve = [eq]; expo = []; held = {}; months = {}
    for i in range(lo, hi):
        if SUN[i] or i == lo:
            nw = target(rule, N, i); t = sum(abs(nw.get(j, 0) - w.get(j, 0)) for j in set(nw) | set(w)); eq *= 1 - t * (fee + slip); w = nw
            for j in w: held[syms[j]] = held.get(syms[j], 0) + 1
        r = sum(wt * (P[i + 1, j] / P[i, j] - 1) for j, wt in w.items()); eq *= 1 + r
        w = {j: wt * (P[i + 1, j] / P[i, j]) / (1 + r) for j, wt in w.items()} if 1 + r > 0 else {}
        curve.append(eq); expo.append(sum(w.values()))
        months[dt.datetime.fromtimestamp(D0 + (i + 1) * 86400, dt.timezone.utc).strftime("%Y-%m")] = eq
    return curve, expo, held, months
def stats(curve, expo, held, months, lo):
    v = curve; dr = [v[k] / v[k - 1] - 1 for k in range(1, len(v))]; yrs = len(dr) / 365
    pk = v[0]; mdd = 0
    for x in v: pk = max(pk, x); mdd = max(mdd, 1 - x / pk)
    sd = statistics.pstdev(dr); wk = {}; mo = {}
    for k, r in enumerate(dr):
        d = dt.datetime.fromtimestamp(D0 + (lo + k + 1) * 86400, dt.timezone.utc)
        wk.setdefault(d.isocalendar()[:2], []).append(r); mo.setdefault(d.strftime("%Y-%m"), []).append(r)
    wr = [math.prod(1 + x for x in m) - 1 for m in wk.values()]; mr = {k: math.prod(1 + x for x in m) - 1 for k, m in mo.items()}
    return {"end_usd": round(v[-1], 2), "total_pct": round((v[-1] / 1000 - 1) * 100, 1), "cagr_pct": round(((v[-1] / 1000) ** (1 / yrs) - 1) * 100, 1),
            "max_drawdown_pct": round(mdd * 100, 1), "sharpe": round(statistics.mean(dr) / sd * math.sqrt(365), 2) if sd else None,
            "mean_daily_pct": round(statistics.mean(dr) * 100, 3), "mean_weekly_pct": round(statistics.mean(wr) * 100, 2),
            "mean_monthly_pct": round(statistics.mean(mr.values()) * 100, 2), "positive_weeks_pct": round(100 * sum(1 for x in wr if x > 0) / len(wr), 1),
            "positive_months_pct": round(100 * sum(1 for x in mr.values() if x > 0) / len(mr), 1),
            "best_month_pct": round(max(mr.values()) * 100, 1), "worst_month_pct": round(min(mr.values()) * 100, 1),
            "avg_invested_pct": round(100 * statistics.mean(expo), 1),
            "most_held": sorted(held.items(), key=lambda x: -x[1])[:15],
            "monthly_pct": {k: round(x * 100, 2) for k, x in mr.items()}, "month_end_usd": {k: round(x, 2) for k, x in months.items()}}
TS = lambda s: (int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp()) - D0) // 86400
WIN = {"A_2018_to_2019": (TS("2018-01-01"), TS("2019-12-31")), "B_2020_to_2023": (TS("2020-01-01"), TS("2023-12-31")), "C_2024_to_2026-10": (TS("2024-01-01"), TS("2026-10-08"))}
out = {"artifact_type": "research_only_preregistered_topn_trend", "not_promotion_evidence": True, "pairs_incl_delisted": NS,
       "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "results": []}
ever = set()
for i in range(TS("2018-01-01"), ND):
    if SUN[i]: ever |= {syms[j] for j in topn(i, 10)}
out["coins_ever_in_top10"] = sorted(ever)
for rule, N in (("topn_trend", 10), ("topn_trend", 5), ("topn_trend", 20), ("btc_eth_trend", 2), ("hold_btc", 1), ("hold_topn", 10)):
    for fee in (0.001, 0.006):
        for wn, (lo, hi) in WIN.items():
            out["results"].append({"rule": rule, "N": N, "fee": fee, "window": wn, **stats(*run(rule, N, fee, lo, hi), lo)})
    print(rule, N, file=sys.stderr, flush=True)
g = {(r["rule"], r["N"], r["fee"], r["window"]): r for r in out["results"]}
beats = {wn: g[("topn_trend", 10, 0.006, wn)]["end_usd"] > g[("btc_eth_trend", 2, 0.006, wn)]["end_usd"] for wn in WIN}
dd_ok = {wn: g[("topn_trend", 10, 0.006, wn)]["max_drawdown_pct"] <= g[("btc_eth_trend", 2, 0.006, wn)]["max_drawdown_pct"] + 10 for wn in WIN}
out["decision"] = {"beats_btc_eth_rule_by_window": beats, "drawdown_within_10pts_by_window": dd_ok,
                   "passes": bool(sum(beats.values()) >= 2 and beats["C_2024_to_2026-10"] and all(dd_ok.values()))}
print(json.dumps(out, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
