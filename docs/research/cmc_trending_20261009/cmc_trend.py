"""PRE-REGISTERED before the first run (2026-10-09). Research only. Not promotion evidence.
Question: CoinMarketCap's "trending" list has no history, so it cannot be backtested directly. This tests the three
things CMC says drive trending that DO have history (price moves, trade activity, rising rank), plus the opposite of one.
Data: CMC weekly snapshots (every Sunday 00:00 UTC) of the top 1000 coins by market cap, 2018-11-04..2026-10-04,
INCLUDING coins that later collapsed or vanished (no survivorship bias). Excluded: stablecoins, wrapped, tokenized
stocks/gold, liquid-staking tokens (by CMC tags; first 12 tags kept), any coin priced $0.97-$1.03 that moved
less than 1% in 7 days (stablecoin catch-all), and coins with < $1M 24h volume.
Universe each Sunday: the top 100 by CMC rank after exclusions.
Signals (pick the top K = 10, equal weight):
  climb   = biggest CMC rank improvement over the last 4 weeks (not in the top 1000 then = rank 1001);
  gain7d  = biggest 7-day % gain (CMC's "top gainers");
  volsurge= highest 24h volume / market cap;
  lose7d  = biggest 7-day % loss (the opposite of gain7d, as a check).
Hold H = 1 or 4 weeks, then re-pick. Regime R: off, or on = invest only when BTC's snapshot price is above its 30-week
average (else cash). Grid 4 x 2 x 2 = 16.
Prices: buy and sell at snapshot prices. A coin missing from the top 1000 at exit is valued at -50% (selected version
also reported at 0% and -90%).
Costs per side on traded amount: fee 0.6% (and 0.1%) + 0.3% slippage.
TRAIN 2019-01-06..2023-12-31, TEST 2024-01-07..2026-10-04.
Selection set in advance: highest TRAIN Sharpe at 0.6% fee. PASSES only if TEST return > 0, TEST worst drop < 60%, and
TEST end value beats holding BTC over TEST.
Benchmarks: hold BTC; equal-weight the whole universe (top 100 after exclusions), re-picked every H weeks."""
import json, os, sys, math, statistics, hashlib
S = sys.argv[1]; W = f"{S}/cmc/weekly"
days = sorted(f[:-5] for f in os.listdir(W))
EXCL_TAGS = {"stablecoin", "asset-backed-stablecoin", "fiat-stablecoin", "algorithmic-stablecoin", "usd-stablecoin", "eur-stablecoin",
             "wrapped-tokens", "tokenized-gold", "tokenized-stock", "tokenized-assets", "tokenized-commodities", "liquid-staking-derivatives",
             "bridged-tokens", "xstocks-ecosystem"}
snap = []
for d in days:
    rows = json.load(open(f"{W}/{d}.json"))
    snap.append({r[0]: {"sym": r[1], "rank": r[3], "px": r[4], "vol": r[5], "mc": r[6], "c7": r[7], "tags": set(r[9])} for r in rows})
def universe(t):
    u = [(v["rank"], i) for i, v in snap[t].items() if not (v["tags"] & EXCL_TAGS) and (v["vol"] or 0) >= 1e6 and (v["px"] or 0) > 0 and (v["mc"] or 0) > 0
         and not (0.97 <= v["px"] <= 1.03 and abs(v["c7"] or 0) < 1)]
    return [i for _, i in sorted(u)[:100]]
BTCPX = [s[1]["px"] for s in snap]
def regime_on(t):
    if t < 30: return False
    return BTCPX[t] > sum(BTCPX[t - 29:t + 1]) / 30
def pick(sig, t, K=10):
    U = universe(t)
    if sig == "all": return U
    if sig == "climb":
        if t < 4: return []
        key = lambda i: snap[t - 4].get(i, {"rank": 1001})["rank"] - snap[t][i]["rank"]
    elif sig == "gain7d": key = lambda i: snap[t][i]["c7"] if snap[t][i]["c7"] is not None else -1e9
    elif sig == "lose7d": key = lambda i: -(snap[t][i]["c7"] if snap[t][i]["c7"] is not None else 1e9)
    elif sig == "volsurge": key = lambda i: snap[t][i]["vol"] / snap[t][i]["mc"]
    return sorted(U, key=key, reverse=True)[:K]
def run(sig, H, R, fee, lo, hi, miss=-0.5, slip=0.003):
    eq = 1000.0; curve = [(days[lo], eq)]; picks_log = []; missing = 0; w = {}
    t = lo
    while t + H <= hi:
        new = pick(sig, t) if (R == "off" or regime_on(t)) else []
        nw = {i: 1 / len(new) for i in new} if new else {}
        turn = sum(abs(nw.get(i, 0) - w.get(i, 0)) for i in set(nw) | set(w))
        eq *= 1 - turn * (fee + slip)
        rets = {}
        for i in nw:
            p0 = snap[t][i]["px"]; p1 = snap[t + H].get(i, {}).get("px")
            if p1 is None or p1 <= 0: rets[i] = miss; missing += 1
            else: rets[i] = p1 / p0 - 1
        r = sum(nw[i] * rets[i] for i in nw); eq *= 1 + r
        w = {i: nw[i] * (1 + rets[i]) / (1 + r) for i in nw} if 1 + r > 0 else {}
        if nw: picks_log.append({"date": days[t], "picks": [(snap[t][i]["sym"], round(rets[i] * 100, 1)) for i in nw]})
        t += H; curve.append((days[t], eq))
    return curve, picks_log, missing
def stats(curve, H, picks_log, missing):
    v = [x for _, x in curve]; pr = [v[k] / v[k - 1] - 1 for k in range(1, len(v))]
    yrs = len(pr) * H / 52.18; pk = v[0]; mdd = 0
    for x in v: pk = max(pk, x); mdd = max(mdd, 1 - x / pk)
    sd = statistics.pstdev(pr) if len(pr) > 1 else 0
    mo = {}
    for (d, x) in curve: mo[d[:7]] = x
    ms = list(mo.items()); mret = {ms[k][0]: (ms[k][1] / ms[k - 1][1] - 1) * 100 for k in range(1, len(ms))}
    allp = [p for pl in picks_log for _, p in pl["picks"]]
    return {"end_usd": round(v[-1], 2), "total_pct": round((v[-1] / 1000 - 1) * 100, 1), "cagr_pct": round(((v[-1] / 1000) ** (1 / yrs) - 1) * 100, 1) if v[-1] > 0 else -100,
            "max_drawdown_pct": round(mdd * 100, 1), "sharpe": round(statistics.mean(pr) / sd * math.sqrt(52.18 / H), 2) if sd else 0,
            "mean_period_pct": round(statistics.mean(pr) * 100, 2), "mean_weekly_pct_equiv": round(((1 + statistics.mean(pr)) ** (1 / H) - 1) * 100, 2),
            "positive_periods_pct": round(100 * sum(1 for x in pr if x > 0) / len(pr), 1), "best_period_pct": round(max(pr) * 100, 1), "worst_period_pct": round(min(pr) * 100, 1),
            "positive_months_pct": round(100 * sum(1 for x in mret.values() if x > 0) / max(1, len(mret)), 1),
            "pick_count": len(allp), "pick_win_pct": round(100 * sum(1 for p in allp if p > 0) / len(allp), 1) if allp else None,
            "pick_median_pct": round(statistics.median(allp), 1) if allp else None, "pick_mean_pct": round(statistics.mean(allp), 1) if allp else None,
            "picks_missing_at_exit": missing, "periods_invested_pct": round(100 * len(picks_log) / len(pr), 1),
            "monthly_pct": {k: round(x, 2) for k, x in mret.items()}, "month_end_usd": {k: round(x, 2) for k, x in mo.items()},
            "last_picks": picks_log[-3:]}
ix = {d: k for k, d in enumerate(days)}
TRAIN = (ix["2019-01-06"], ix["2023-12-31"]); TEST = (ix["2024-01-07"], ix["2026-10-04"])
out = {"artifact_type": "research_only_preregistered_cmc_trending_proxies", "not_promotion_evidence": True, "snapshots": len(days),
       "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "results": []}
for sig in ("climb", "gain7d", "volsurge", "lose7d", "all"):
    for H in (1, 4):
        for R in ("off", "on"):
            for fee in (0.001, 0.006):
                rec = {"signal": sig, "hold_weeks": H, "regime": R, "fee": fee}
                for part, (lo, hi) in (("train", TRAIN), ("test", TEST)):
                    rec[part] = stats(*((lambda c, p, m: (c, H, p, m))(*run(sig, H, R, fee, lo, hi))))
                out["results"].append(rec)
out["btc_hold_pct"] = {k: round((BTCPX[hi] / BTCPX[lo] - 1) * 100, 1) for k, (lo, hi) in (("train", TRAIN), ("test", TEST))}
cand = [r for r in out["results"] if r["fee"] == 0.006 and r["signal"] != "all"]
best = max(cand, key=lambda r: r["train"]["sharpe"])
out["selected"] = {k: best[k] for k in ("signal", "hold_weeks", "regime")}
out["selected_passes"] = bool(best["test"]["total_pct"] > 0 and best["test"]["max_drawdown_pct"] < 60 and best["test"]["total_pct"] > out["btc_hold_pct"]["test"])
out["selected_missing_sensitivity"] = {str(m): run(best["signal"], best["hold_weeks"], best["regime"], 0.006, *TEST, miss=m)[0][-1][1] for m in (0.0, -0.5, -0.9)}
print(json.dumps(out, default=lambda o: o.item() if hasattr(o, "item") else (sorted(o) if isinstance(o, set) else str(o))))
