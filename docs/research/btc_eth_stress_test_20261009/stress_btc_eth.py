"""PRE-REGISTERED before the first run (2026-10-09), agreed with the operator. Research only. Not promotion evidence.
Stress test of the one rule that passed (majors.py primary): BTC+ETH, 28-day trend, volatility-sized, weekly.
Data: Coinbase daily closes BTC-USD and ETH-USD (maj/*.json), days where both exist, up to 2026-10-08.
Periods: A 2016-08-01..2019-12-31 (starts a month later than majors.py so a 56-day lookback has history;
the baseline on majors.py's 2016-07-01 start is also reported), B 2020-01-01..2023-12-31, C 2024-01-01..2026-10-08,
FULL 2016-08-01..2026-10-08.
Rule(L, V, weekday, assets): at the close of the daily candle whose start falls on `weekday` (6 = Sunday, the baseline),
for each asset: if its L-day return > 0, weight = (1/n_assets) * min(1, V / annualised 30-day volatility), else 0.
Cash otherwise. Baseline L=28, V=50%, weekday=6, assets BTC+ETH.
Costs: primary 1.2% fee (Coinbase taker) + 0.05% slippage per side on traded amount; 0.6% also reported.
Benchmarks:
  hold_btc  - buy BTC at the period start, hold.
  fixed_mix - 50/50 BTC/ETH at a constant total exposure equal to the rule's own average invested share over the same
              period (hindsight given to the benchmark, which makes the test harder for the rule), rebalanced on the same
              weekday, same costs.
  btc_only  - the same trend rule on BTC alone (weight = min(1, V / vol)).
Required 1: at 1.2%, the baseline beats BOTH hold_btc and fixed_mix on worst drop AND on Sharpe in at least 2 of the 3
  periods, one of which must be A.
Required 2: of the 13 one-at-a-time variants (L = 14, 21, 42, 56; V = 30%, 70%; the 6 other weekdays; BTC-only),
  at least 10 have a higher FULL-period Sharpe than their own fixed_mix at 1.2%.
Reported, not required: paired block bootstrap (weekly returns, block 8 weeks; 4 and 13 also shown, 5,000 resamples,
  seed 7) of FULL-period Sharpe(baseline) - Sharpe(fixed_mix), 90% range; the combined grid L x V x weekday
  (5 x 3 x 7 = 105) at 1.2%: share beating its fixed_mix on FULL Sharpe.
Verdict: both required pass -> continue paper validation; exactly one passes -> keep researching; neither passes, or the
  baseline does not beat fixed_mix on FULL Sharpe -> reject (no timing edge, only lower exposure).
Validation: the baseline at 0.6% on majors.py's period A (2016-07-01 start) must reproduce majors.py ($5,146)."""
import json, sys, math, statistics, random, hashlib, datetime as dt
S = sys.argv[1]
CUT = int(dt.datetime(2026, 10, 9, tzinfo=dt.timezone.utc).timestamp())
def load(p): return {r[0]: r[4] for r in json.load(open(f"{S}/maj/{p}_d1.json")) if r[0] < CUT}
px = {"BTC": load("BTC-USD"), "ETH": load("ETH-USD")}
days = sorted(set(px["BTC"]) & set(px["ETH"]))
P = {a: [px[a][d] for d in days] for a in px}
WD = [dt.datetime.fromtimestamp(d, dt.timezone.utc).weekday() for d in days]
DR = {a: [0.0] + [P[a][i] / P[a][i - 1] - 1 for i in range(1, len(days))] for a in P}
VOL = {a: [None] * 31 + [statistics.pstdev(DR[a][i - 29:i + 1]) * math.sqrt(365) for i in range(31, len(days))] for a in P}
TS = lambda s: int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())
def idx(lo, hi): return next(i for i, d in enumerate(days) if d >= TS(lo)), max(i for i, d in enumerate(days) if d <= TS(hi))
PER = {"A": idx("2016-08-01", "2019-12-31"), "B": idx("2020-01-01", "2023-12-31"), "C": idx("2024-01-01", "2026-10-08"), "FULL": idx("2016-08-01", "2026-10-08")}
A_ORIG = idx("2016-07-01", "2019-12-31")
def target(kind, i, L, V, assets, expo=None):
    if kind == "hold_btc": return {"BTC": 1.0}
    if kind == "fixed_mix": return {"BTC": expo / 2, "ETH": expo / 2}
    w = {}
    for a in assets:
        assert i - L >= 0 and VOL[a][i] is not None
        if P[a][i] / P[a][i - L] - 1 > 0: w[a] = (1 / len(assets)) * min(1.0, V / VOL[a][i])
    return w
def run(kind, lo, hi, L=28, V=0.5, wd=6, assets=("BTC", "ETH"), fee=0.012, slip=0.0005, expo=None):
    eq = 1000.0; w = {}; curve = [eq]; ex = []
    for i in range(lo, hi):
        if i == lo or (kind != "hold_btc" and WD[i] == wd):
            nw = target(kind, i, L, V, assets, expo); t = sum(abs(nw.get(a, 0) - w.get(a, 0)) for a in set(nw) | set(w)); eq *= 1 - t * (fee + slip); w = nw
        r = sum(x * DR[a][i + 1] for a, x in w.items()); eq *= 1 + r
        w = {a: x * (1 + DR[a][i + 1]) / (1 + r) for a, x in w.items()}
        curve.append(eq); ex.append(sum(w.values()))
    return curve, statistics.mean(ex)
def stats(curve):
    dr = [curve[k] / curve[k - 1] - 1 for k in range(1, len(curve))]; pk = curve[0]; mdd = 0; uw = 0; uwmax = 0
    for x in curve:
        if x >= pk: pk = x; uw = 0
        else: uw += 1; uwmax = max(uwmax, uw)
        mdd = max(mdd, 1 - x / pk)
    sd = statistics.pstdev(dr); yrs = len(dr) / 365
    down = math.sqrt(sum(min(0, x) ** 2 for x in dr) / len(dr)) * math.sqrt(365)
    return {"end_usd": round(curve[-1], 2), "cagr_pct": round(((curve[-1] / 1000) ** (1 / yrs) - 1) * 100, 1), "max_drawdown_pct": round(mdd * 100, 1),
            "longest_underwater_days": uwmax, "vol_pct": round(sd * math.sqrt(365) * 100, 1), "downside_vol_pct": round(down * 100, 1),
            "sharpe": round(statistics.mean(dr) / sd * math.sqrt(365), 3) if sd else 0}
def evaluate(lo, hi, fee, **kw):
    c, e = run("rule", lo, hi, fee=fee, **kw); m, _ = run("fixed_mix", lo, hi, wd=kw.get("wd", 6), fee=fee, expo=e); h, _ = run("hold_btc", lo, hi, fee=fee)
    return {"rule": {**stats(c), "avg_exposure_pct": round(e * 100, 1)}, "fixed_mix": stats(m), "hold_btc": stats(h)}, c, m
out = {"artifact_type": "research_only_preregistered_stress_test", "not_promotion_evidence": True,
       "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "periods": {k: [dt.datetime.fromtimestamp(days[a], dt.timezone.utc).date().isoformat(), dt.datetime.fromtimestamp(days[b], dt.timezone.utc).date().isoformat()] for k, (a, b) in PER.items()}}
# baseline
out["baseline"] = {}
for fee in (0.012, 0.006):
    out["baseline"][str(fee)] = {k: evaluate(lo, hi, fee)[0] for k, (lo, hi) in PER.items()}
out["baseline_majors_A_start_2016-07-01_fee0.006"] = evaluate(*A_ORIG, 0.006)[0]
# required 1
b = out["baseline"]["0.012"]
def beats(p): r = b[p]; return all(r["rule"]["max_drawdown_pct"] < r[x]["max_drawdown_pct"] and r["rule"]["sharpe"] > r[x]["sharpe"] for x in ("hold_btc", "fixed_mix"))
r1 = {p: beats(p) for p in ("A", "B", "C")}
out["required_1"] = {"by_period": r1, "passes": bool(r1["A"] and sum(r1.values()) >= 2)}
# required 2
VARS = [("lookback", {"L": L}) for L in (14, 21, 42, 56)] + [("vol_target", {"V": V}) for V in (0.30, 0.70)] + \
       [("weekday", {"wd": d}) for d in (0, 1, 2, 3, 4, 5)] + [("btc_only", {"assets": ("BTC",)})]
out["variants"] = []
for name, kw in VARS:
    res = {p: evaluate(lo, hi, 0.012, **kw)[0] for p, (lo, hi) in PER.items()}
    out["variants"].append({"change": name, "setting": {k: (list(v) if isinstance(v, tuple) else v) for k, v in kw.items()}, "results": res,
                            "beats_fixed_mix_full_sharpe": res["FULL"]["rule"]["sharpe"] > res["FULL"]["fixed_mix"]["sharpe"]})
n2 = sum(v["beats_fixed_mix_full_sharpe"] for v in out["variants"])
out["required_2"] = {"variants_beating": n2, "of": len(VARS), "passes": n2 >= 10}
# bootstrap
lo, hi = PER["FULL"]; _, c, m = evaluate(lo, hi, 0.012)
wk = lambda cur: [cur[k + 7] / cur[k] - 1 for k in range(0, len(cur) - 7, 7)]
wr, wm = wk(c), wk(m)
def sh(x): s = statistics.pstdev(x); return statistics.mean(x) / s * math.sqrt(52.18) if s else 0
out["bootstrap"] = {"observed_weekly_sharpe_diff": round(sh(wr) - sh(wm), 3), "weeks": len(wr)}
rng = random.Random(7)
for blk in (4, 8, 13):
    diffs = []
    n = len(wr)
    for _ in range(5000):
        ii = []
        while len(ii) < n:
            s0 = rng.randrange(0, n - blk + 1); ii.extend(range(s0, s0 + blk))
        ii = ii[:n]; diffs.append(sh([wr[j] for j in ii]) - sh([wm[j] for j in ii]))
    diffs.sort()
    out["bootstrap"][f"block_{blk}w"] = {"p05": round(diffs[int(0.05 * 5000)], 3), "p50": round(diffs[2500], 3), "p95": round(diffs[int(0.95 * 5000)], 3),
                                         "share_above_zero_pct": round(100 * sum(1 for d in diffs if d > 0) / 5000, 1)}
# combined grid
grid = []
for L in (14, 21, 28, 42, 56):
    for V in (0.30, 0.50, 0.70):
        for d in range(7):
            r = evaluate(lo, hi, 0.012, L=L, V=V, wd=d)[0]
            grid.append({"L": L, "V": V, "weekday": d, "rule_sharpe": r["rule"]["sharpe"], "fixed_mix_sharpe": r["fixed_mix"]["sharpe"], "rule_mdd": r["rule"]["max_drawdown_pct"],
                         "fixed_mix_mdd": r["fixed_mix"]["max_drawdown_pct"], "rule_end": r["rule"]["end_usd"], "exposure": r["rule"]["avg_exposure_pct"]})
out["combined_grid"] = {"rows": grid, "share_beating_fixed_mix_sharpe_pct": round(100 * sum(1 for g in grid if g["rule_sharpe"] > g["fixed_mix_sharpe"]) / len(grid), 1)}
fb = b["FULL"]
reject = not (fb["rule"]["sharpe"] > fb["fixed_mix"]["sharpe"])
out["verdict"] = "reject" if reject else ("continue_paper_validation" if out["required_1"]["passes"] and out["required_2"]["passes"] else
                 ("keep_researching" if out["required_1"]["passes"] or out["required_2"]["passes"] else "reject"))
print(json.dumps(out))
