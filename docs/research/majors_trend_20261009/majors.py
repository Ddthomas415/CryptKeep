"""PRE-REGISTERED before the first run (2026-10-09). Research only.
Primary rule (from the time-series momentum literature and the one rule that survived the Binance test):
  Assets BTC and ETH (Coinbase USD daily closes). Every Sunday close (00:00 UTC):
  for each asset, if its 28-day return > 0, weight = 0.5 * min(1, 0.50 / annualised 30-day volatility); else 0.
  Cash otherwise. No leverage. Costs on turnover: fee per side 0.1% and 0.6%, plus 0.05% slippage.
Windows: A 2016-07-01..2019-12-31 (never examined before this run), B 2020-01-01..2023-12-31, C 2024-01-01..2026-10-08.
Secondary rules (reported, not used to choose): 100-day-average signal instead of 28-day return; Bitcoin only;
no volatility sizing. Benchmarks: hold BTC; hold 50/50 BTC/ETH rebalanced weekly.
Decision rule set in advance: the primary rule is worth a paper test only if, in window A, it has a lower maximum
drawdown than holding BTC and a positive return after the 0.6% fee."""
import json, sys, math, statistics, datetime as dt, hashlib
S = sys.argv[1]
def load(p):
    return {r[0]: r[4] for r in json.load(open(f"{S}/maj/{p}_d1.json")) if r[0] < int(dt.datetime(2026, 10, 9, tzinfo=dt.timezone.utc).timestamp())}
px = {"BTC": load("BTC-USD"), "ETH": load("ETH-USD")}
days = sorted(set(px["BTC"]) & set(px["ETH"]))
def series(a): 
    return [px[a][d] for d in days]
P = {a: series(a) for a in px}
def ret(a, i, L): return P[a][i] / P[a][i - L] - 1
def sma(a, i, L): return sum(P[a][i - L + 1:i + 1]) / L
def vol(a, i): 
    r = [P[a][k] / P[a][k - 1] - 1 for k in range(i - 29, i + 1)]; return statistics.pstdev(r) * math.sqrt(365)
def target(rule, i):
    w = {}
    for a in ("BTC", "ETH"):
        if rule in ("btc_only",) and a == "ETH": continue
        base = 1.0 if rule == "btc_only" else 0.5
        if rule == "hold_btc": return {"BTC": 1.0}
        if rule == "hold_5050": w[a] = 0.5; continue
        on = (P[a][i] > sma(a, i, 100)) if rule == "sma100" else ret(a, i, 28) > 0
        if not on: continue
        w[a] = base if rule == "no_vol_sizing" else base * min(1.0, 0.5 / vol(a, i))
    return w
def run(rule, fee, lo, hi, slip=0.0005):
    i0 = next(i for i, d in enumerate(days) if d >= lo); i1 = max(i for i, d in enumerate(days) if d <= hi)
    eq = 1000.0; w = {}; curve = [(days[i0], eq)]; expo = []
    for i in range(i0, i1):
        if dt.datetime.fromtimestamp(days[i], dt.timezone.utc).weekday() == 6 or i == i0:
            nw = target(rule, i); t = sum(abs(nw.get(a, 0) - w.get(a, 0)) for a in set(nw) | set(w)); eq *= 1 - t * (fee + slip); w = nw
        r = sum(wt * (P[a][i + 1] / P[a][i] - 1) for a, wt in w.items()); eq *= 1 + r
        w = {a: wt * (P[a][i + 1] / P[a][i]) / (1 + r) for a, wt in w.items()}
        curve.append((days[i + 1], eq)); expo.append(sum(w.values()))
    return curve, expo
def stats(curve, expo):
    v = [x for _, x in curve]; dr = [v[k] / v[k - 1] - 1 for k in range(1, len(v))]
    yrs = len(dr) / 365; pk = v[0]; mdd = 0
    for x in v: pk = max(pk, x); mdd = max(mdd, 1 - x / pk)
    sd = statistics.pstdev(dr)
    mo = {}; wk = {}
    for (t, _), r in zip(curve[1:], dr):
        d = dt.datetime.fromtimestamp(t, dt.timezone.utc); mo.setdefault(d.strftime("%Y-%m"), []).append(r); wk.setdefault(d.isocalendar()[:2], []).append(r)
    mr = [math.prod(1 + x for x in m) - 1 for m in mo.values()]; wr = [math.prod(1 + x for x in m) - 1 for m in wk.values()]
    return {"start_usd": 1000, "end_usd": round(v[-1], 2), "total_pct": round((v[-1] / 1000 - 1) * 100, 1), "cagr_pct": round(((v[-1] / 1000) ** (1 / yrs) - 1) * 100, 1),
            "max_drawdown_pct": round(mdd * 100, 1), "sharpe": round(statistics.mean(dr) / sd * math.sqrt(365), 2) if sd else None,
            "mean_daily_pct": round(statistics.mean(dr) * 100, 3), "mean_weekly_pct": round(statistics.mean(wr) * 100, 2), "mean_monthly_pct": round(statistics.mean(mr) * 100, 2),
            "positive_weeks_pct": round(100 * sum(1 for x in wr if x > 0) / len(wr), 1), "positive_months_pct": round(100 * sum(1 for x in mr if x > 0) / len(mr), 1),
            "worst_month_pct": round(min(mr) * 100, 1), "best_month_pct": round(max(mr) * 100, 1), "avg_invested_pct": round(100 * statistics.mean(expo), 1),
            "monthly_pct": {k: round((math.prod(1 + x for x in m) - 1) * 100, 2) for k, m in mo.items()}}
TS = lambda s: int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())
WIN = {"A_2016-07_to_2019": (TS("2016-07-01"), TS("2019-12-31")), "B_2020_to_2023": (TS("2020-01-01"), TS("2023-12-31")), "C_2024_to_2026-10": (TS("2024-01-01"), TS("2026-10-08"))}
RULES = ["primary_28d_trend_vol_sized", "sma100", "btc_only", "no_vol_sizing", "hold_btc", "hold_5050"]
out = {"artifact_type": "research_only_preregistered_majors_trend", "not_promotion_evidence": True,
       "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "results": []}
for rule in RULES:
    for fee in (0.001, 0.006):
        for wn, (lo, hi) in WIN.items():
            c, e = run(rule, fee, lo, hi); out["results"].append({"rule": rule, "fee": fee, "window": wn, **stats(c, e)})
A = {(r["rule"], r["fee"]): r for r in out["results"] if r["window"].startswith("A_")}
p = A[("primary_28d_trend_vol_sized", 0.006)]; b = A[("hold_btc", 0.006)]
out["preregistered_decision"] = {"primary_A_drawdown_lower_than_btc": p["max_drawdown_pct"] < b["max_drawdown_pct"], "primary_A_return_positive_at_0.6pct_fee": p["total_pct"] > 0}
print(json.dumps(out))
