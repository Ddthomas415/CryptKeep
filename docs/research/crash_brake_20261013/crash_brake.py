"""E7 funding-rate crash brake, implementing PREREGISTRATION.md exactly. Research only.
Usage: python3 -B crash_brake.py DIR_WITH_maj"""
import bisect, hashlib, json, math, statistics, sys, datetime as dt
from pathlib import Path
from statistics import NormalDist
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECT = {"scripts/research/rerun_frozen_stress.py": "1f98513ae63c4f84819327746872a9dd0a73b3bc35e5e67364c57458ca395907",
          "docs/research/majors_trend_20261009/BTC-USD_d1.json": "64cab2cf912244babb251485a9949a266be30fb80840e95b80d4478a9cde07c0",
          "docs/research/majors_trend_20261009/ETH-USD_d1.json": "9fa81ca8395321dddc5453a2144b5081ada012e74ed3132c9c2c039e5e6206b8"}
FUND = ROOT / "research/crash_brake_20261013/binance_funding_raw.jsonl"
got = {k: sha(ROOT / k) for k in EXPECT}
if got != EXPECT: raise SystemExit(f"hash mismatch {got}")
from scripts.research.rerun_frozen_stress import load_frozen, run
ns = load_frozen(sys.argv[1]); days = ns["days"]; st = ns["stats"]

# ---- funding: per asset, rolling 21-print mean (annualised) at each print time ----
raw = {"BTC": [], "ETH": []}
for line in open(FUND):
    r = json.loads(line)
    if r.get("type") == "error": raise SystemExit("funding file contains errors")
    if r.get("type") == "funding":
        raw[{"BTCUSDT": "BTC", "ETHUSDT": "ETH"}[r["symbol"]]].append((r["fundingTime"] // 1000, float(r["fundingRate"])))
ROLL = {}
for a, L in raw.items():
    L.sort(); t = [x[0] for x in L]; v = [x[1] for x in L]
    times, lev = [], []
    for k in range(20, len(L)):
        times.append(t[k]); lev.append(statistics.fmean(v[k - 20:k + 1]) * 3 * 365)
    ROLL[a] = (times, lev, t[0])

def brake_state(asset, i, pct, src=None):
    """Extreme flag at decision index i: level = last rolling mean with print time < decision close; percentile vs history so far."""
    times, lev, first = ROLL[src or asset]
    close = days[i] + 86400
    k = bisect.bisect_left(times, close)            # rolling means strictly before the close
    if k == 0 or close - first < 365 * 86400: return None
    hist = sorted(lev[:k]); level = lev[k - 1]
    q = hist[min(len(hist) - 1, int(math.ceil(pct * len(hist))) - 1)]
    return level >= q, level, q

def make_ns(pct=0.90, factor=0.5, btc_for_both=False, log=None):
    base = ns["target"]
    def target(kind, i, L, V, assets, expo=None):
        w = base(kind, i, L, V, assets, expo)
        if kind != "rule": return w
        out = {}
        for a, x in w.items():
            s = brake_state(a, i, pct, "BTC" if btc_for_both else None)
            on = bool(s and s[0])
            out[a] = x * factor if on else x
            if log is not None: log.append({"day": str(dt.date.fromtimestamp(days[i])), "asset": a, "brake": on, "weight_before": round(x, 4)})
        if log is not None:
            for a in ("BTC", "ETH"):
                if a not in w:
                    s = brake_state(a, i, pct, "BTC" if btc_for_both else None)
                    log.append({"day": str(dt.date.fromtimestamp(days[i])), "asset": a, "brake": bool(s and s[0]), "weight_before": 0.0})
        return out
    n2 = dict(ns); n2["target"] = target; return n2

def ix_sunday(lo, hi):
    ts = lambda s: int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())
    a = next(i for i, d in enumerate(days) if d >= ts(lo) and dt.datetime.fromtimestamp(d, dt.timezone.utc).weekday() == 6)
    b = max(i for i, d in enumerate(days) if d <= ts(hi))
    return a, b
PER = {"D": ix_sunday("2020-12-01", "2023-12-31"), "H": ix_sunday("2024-01-01", "2026-10-08")}
out = {"artifact_type": "research_only_preregistered_test_E7", "prereg_sha256": sha(HERE / "PREREGISTRATION.md"), "script_sha256": sha(__file__),
       "funding_sha256": sha(FUND), "inputs_sha256": got,
       "periods": {k: [str(dt.date.fromtimestamp(days[a])), str(dt.date.fromtimestamp(days[b]))] for k, (a, b) in PER.items()}, "results": {}}
curves = {}
for fee in (0.005, 0.009):
    R = out["results"][str(fee)] = {}
    for p, (lo, hi) in PER.items():
        log = []
        b, eb = run(make_ns(log=log), "rule", lo, hi, fee=fee)
        c, ec = run(ns, "rule", lo, hi, fee=fee)
        h, _ = run(ns, "hold_btc", lo, hi, fee=fee)
        m, _ = run(ns, "fixed_mix", lo, hi, fee=fee, expo=0.5)
        weeks = sorted({x["day"] for x in log})
        R[p] = {"braked": {**st(b), "avg_exposure_pct": round(eb * 100, 1)}, "candidate": {**st(c), "avg_exposure_pct": round(ec * 100, 1)},
                "hold_btc": st(h), "mix_25_25_50": st(m), "cash": {"end_usd": 1000.0, "sharpe": 0.0, "max_drawdown_pct": 0.0},
                "decision_weeks": len(weeks), "weeks_brake_flag_any": len({x["day"] for x in log if x["brake"]}),
                "weeks_brake_cut_exposure": len({x["day"] for x in log if x["brake"] and x["weight_before"] > 0}),
                "brake_flag_days": sorted({x["day"] for x in log if x["brake"]})}
        if fee == 0.005: curves[p] = b
r5, r9 = out["results"]["0.005"], out["results"]["0.009"]
def ok(r):
    D, H = r["D"], r["H"]
    return {"D_sharpe_higher_and_dd_lower": D["braked"]["sharpe"] > D["candidate"]["sharpe"] and D["braked"]["max_drawdown_pct"] < D["candidate"]["max_drawdown_pct"],
            "H_sharpe_not_lower_by_0.05_and_dd_not_higher": H["braked"]["sharpe"] >= H["candidate"]["sharpe"] - 0.05 and H["braked"]["max_drawdown_pct"] <= H["candidate"]["max_drawdown_pct"]}
c5, c9 = ok(r5), ok(r9)
out["pass_checks"] = {"fee0.50": c5, "fee0.90": c9}
inconclusive = r5["D"]["weeks_brake_cut_exposure"] < 4
out["verdict"] = "INCONCLUSIVE" if inconclusive else ("PASS" if all(c5.values()) and all(c9.values()) else "FAIL")
# DSR on braked daily returns over D then H (0.50% fee)
Z = NormalDist(); G = 0.5772156649
def dsr(r, N, V=0.0004636024000905694):
    T = len(r); m = statistics.mean(r); s = statistics.pstdev(r); sr = m / s
    sk = sum(((x - m) / s) ** 3 for x in r) / T; ku = sum(((x - m) / s) ** 4 for x in r) / T
    s0 = 0 if N <= 1 else math.sqrt(V) * ((1 - G) * Z.inv_cdf(1 - 1 / N) + G * Z.inv_cdf(1 - 1 / (N * math.e)))
    return round(Z.cdf((sr - s0) * math.sqrt(T - 1) / math.sqrt(1 - sk * sr + (ku - 1) / 4 * sr ** 2)), 4)
rr = [c[k] / c[k - 1] - 1 for c in (curves["D"], curves["H"]) for k in range(1, len(c))]
out["dsr_braked_DH_fee0.50"] = {f"N={n}": dsr(rr, n) for n in (15, 120)}
sens = []
for label, kw in (("pct80", {"pct": 0.80}), ("pct95", {"pct": 0.95}), ("brake_to_zero", {"factor": 0.0}), ("btc_funding_both", {"btc_for_both": True})):
    row = {"variant": label}
    for p, (lo, hi) in PER.items():
        b, _ = run(make_ns(**kw), "rule", lo, hi, fee=0.005); row[p] = st(b)
    sens.append(row)
out["sensitivity_reported_only_fee0.50"] = sens
json.dump(out, open(HERE / "crash_brake_result.json", "x"), indent=1)
print(json.dumps({k: out[k] for k in ("periods", "pass_checks", "verdict", "dsr_braked_DH_fee0.50")}, indent=1))
for fee in ("0.005", "0.009"):
    for p in ("D", "H"):
        R = out["results"][fee][p]
        print(fee, p, " | ".join(f"{k}: ${v['end_usd']:,.0f} SR {v['sharpe']} DD {v['max_drawdown_pct']}%" for k, v in R.items() if isinstance(v, dict) and "end_usd" in v and k != "cash"),
              "| weeks flagged", R["weeks_brake_flag_any"], "cut", R["weeks_brake_cut_exposure"], "of", R["decision_weeks"])
for s in sens: print(s["variant"], {p: (s[p]["end_usd"], s[p]["sharpe"], s[p]["max_drawdown_pct"]) for p in ("D", "H")})
