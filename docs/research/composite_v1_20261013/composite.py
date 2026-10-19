"""E8 CryptKeep Composite v1, implementing PREREGISTRATION.md. Research only. Usage: python3 -B composite.py DIR_WITH_maj"""
import hashlib, json, math, statistics, sys, datetime as dt
from pathlib import Path
from statistics import NormalDist
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT)); HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECT = {"scripts/research/rerun_frozen_stress.py": "1f98513ae63c4f84819327746872a9dd0a73b3bc35e5e67364c57458ca395907",
          "scripts/research/corrected_research_math.py": "d07ae7171e2293cbe60d15ae9bc0973d3ef8bd31b9c7b99105f928c029e29047",
          "docs/research/majors_trend_20261009/BTC-USD_d1.json": "64cab2cf912244babb251485a9949a266be30fb80840e95b80d4478a9cde07c0",
          "docs/research/majors_trend_20261009/ETH-USD_d1.json": "9fa81ca8395321dddc5453a2144b5081ada012e74ed3132c9c2c039e5e6206b8"}
got = {k: sha(ROOT / k) for k in EXPECT}
if got != EXPECT: raise SystemExit(f"hash mismatch {got}")
from scripts.research.rerun_frozen_stress import load_frozen, run as harness_run
from scripts.research.corrected_research_math import rebalance
ns = load_frozen(sys.argv[1]); days, P, O, WD, VOL, st = ns["days"], ns["P"], ns["OPEN"], ns["WD"], ns["VOL"], ns["stats"]
A = ("BTC", "ETH"); SLIP = 0.0005

def t_candidate(i): return ns["target"]("rule", i, 28, 0.5, A, None)
def t_composite(i, volscale=True):
    w = {}
    for a in A:
        score = sum(P[a][i] > P[a][i - L] for L in (20, 50, 100, 200)) / 4
        if score > 0: w[a] = 0.5 * score * (min(1.0, 0.5 / VOL[a][i]) if volscale else 1.0)
    return w
def t_hold(i): return {"BTC": 1.0}
def t_mix(i): return {"BTC": 0.25, "ETH": 0.25}

def sim(tfun, lo, hi, fee, band=0.0, hold_once=False):
    """Decide at close i (Sundays; first decision at lo, which is a Sunday), execute at open i+1, mark at closes.
    Band: assets with |target - current weight| < band are not traded. Out-of-band assets are rebalanced with the shared
    rebalance() helper over the sub-account (cash + those assets), so band = 0 is identical to the reviewed harness."""
    cash, units = 1000.0, {}; curve = [1000.0]; traded = 0.0; trades = 0; navs = []
    pending = tfun(lo)
    for k in range(lo + 1, hi + 1):
        if pending is not None:
            prices = {a: O[a][k] for a in A}
            nav = cash + sum(q * prices[a] for a, q in units.items())
            cur = {a: units.get(a, 0) * prices[a] / nav for a in A}
            move = [a for a in A if abs(pending.get(a, 0) - cur[a]) >= band - 1e-12] if band > 0 else list(A)
            if move:
                sub_units = {a: units.get(a, 0) for a in move}
                eq_sub = cash + sum(sub_units[a] * prices[a] for a in move)
                want = {a: pending.get(a, 0) * nav for a in move}
                s = sum(want.values())
                scale = min(1.0, eq_sub / s) if s > 0 else 1.0
                wts = {a: (want[a] * scale) / eq_sub for a in move if want[a] > 0} if eq_sub > 0 else {}
                before = {a: sub_units[a] * prices[a] for a in move}
                c2, u2 = rebalance(cash, sub_units, {a: prices[a] for a in move}, wts, fee, SLIP)
                after = {a: u2.get(a, 0) * prices[a] for a in move}
                tv = sum(abs(after[a] - before[a]) for a in move)
                if tv > 1e-9: trades += 1; traded += tv / nav
                cash = c2
                for a in move:
                    if u2.get(a, 0) > 0: units[a] = u2[a]
                    else: units.pop(a, None)
            pending = None
        nav = cash + sum(q * P[a][k] for a, q in units.items())
        curve.append(nav)
        if k < hi and not hold_once and WD[k] == 6: pending = tfun(k)
    out = st(curve); yrs = (hi - lo) / 365
    out["turnover_per_year_x"] = round(traded / yrs, 2); out["rebalances_per_year"] = round(trades / yrs, 1)
    return out, curve

def ixs(lo, hi):
    ts = lambda s: int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())
    a = next(i for i, d in enumerate(days) if d >= ts(lo) and WD[i] == 6); b = max(i for i, d in enumerate(days) if d <= ts(hi))
    return a, b
PER = {"D": ixs("2017-01-01", "2023-12-31"), "H": ixs("2024-01-01", "2026-10-08")}

# simulator check: candidate, band 0 must reproduce the reviewed harness exactly
for p, (lo, hi) in PER.items():
    _, mine = sim(t_candidate, lo, hi, 0.005)
    ref, _ = harness_run(ns, "rule", lo, hi, fee=0.005)
    diff = max(abs(x - y) for x, y in zip(mine, ref))
    if len(mine) != len(ref) or diff > 1e-6: raise SystemExit(f"simulator check FAILED {p}: diff {diff}")
check = "new simulator reproduces reviewed harness (candidate, band 0) within 1e-6 USD in D and H"

out = {"artifact_type": "research_only_preregistered_test_E8", "prereg_sha256": sha(HERE / "PREREGISTRATION.md"), "script_sha256": sha(__file__),
       "inputs_sha256": got, "simulator_check": check,
       "periods": {k: [str(dt.date.fromtimestamp(days[a])), str(dt.date.fromtimestamp(days[b]))] for k, (a, b) in PER.items()}, "results": {}}
curves = {}
for fee in (0.005, 0.009):
    R = out["results"][str(fee)] = {}
    for p, (lo, hi) in PER.items():
        comp, cc = sim(t_composite, lo, hi, fee, band=0.10)
        R[p] = {"composite_v1": comp, "candidate": sim(t_candidate, lo, hi, fee)[0], "hold_btc": sim(t_hold, lo, hi, fee, hold_once=True)[0],
                "mix_25_25_50": sim(t_mix, lo, hi, fee)[0], "cash": {"end_usd": 1000.0, "sharpe": 0.0, "max_drawdown_pct": 0.0}}
        if fee == 0.005: curves[p] = cc
def checks(R):
    D, H = R["D"], R["H"]
    return {"D_sharpe_ge_incumbent": D["composite_v1"]["sharpe"] >= D["candidate"]["sharpe"],
            "D_turnover_le_0.75x": D["composite_v1"]["turnover_per_year_x"] <= 0.75 * D["candidate"]["turnover_per_year_x"],
            "H_sharpe_ge_incumbent_minus_0.05": H["composite_v1"]["sharpe"] >= H["candidate"]["sharpe"] - 0.05,
            "H_maxdd_le_incumbent_plus_2pp": H["composite_v1"]["max_drawdown_pct"] <= H["candidate"]["max_drawdown_pct"] + 2}
out["pass_checks"] = {f: checks(out["results"][f]) for f in ("0.005", "0.009")}
out["verdict"] = "PASS" if all(all(v.values()) for v in out["pass_checks"].values()) else "FAIL"
Z = NormalDist(); G = 0.5772156649
def dsr(r, N, V=0.0004636024000905694):
    T = len(r); m = statistics.mean(r); s = statistics.pstdev(r); sr = m / s
    sk = sum(((x - m) / s) ** 3 for x in r) / T; ku = sum(((x - m) / s) ** 4 for x in r) / T
    s0 = 0 if N <= 1 else math.sqrt(V) * ((1 - G) * Z.inv_cdf(1 - 1 / N) + G * Z.inv_cdf(1 - 1 / (N * math.e)))
    return round(Z.cdf((sr - s0) * math.sqrt(T - 1) / math.sqrt(1 - sk * sr + (ku - 1) / 4 * sr ** 2)), 4)
rr = [c[k] / c[k - 1] - 1 for c in (curves["D"], curves["H"]) for k in range(1, len(c))]
out["dsr_composite_DH_fee0.50"] = {f"N={n}": dsr(rr, n) for n in (15, 120)}
sens = []
for label, f, band in (("band0", t_composite, 0.0), ("band0.20", t_composite, 0.20), ("no_volscale", lambda i: t_composite(i, False), 0.10)):
    row = {"variant": label}
    for p, (lo, hi) in PER.items():
        for fee in (0.005, 0.009): row[f"{p}_{fee}"] = sim(f, lo, hi, fee, band=band)[0]
    sens.append(row)
out["sensitivity_reported_only"] = sens
json.dump(out, open(HERE / "composite_result.json", "x"), indent=1)
print(check); print(json.dumps({k: out[k] for k in ("periods", "pass_checks", "verdict", "dsr_composite_DH_fee0.50")}, indent=1))
for fee in ("0.005", "0.009"):
    for p in ("D", "H"):
        R = out["results"][fee][p]
        print(fee, p, " | ".join(f"{k}: ${v['end_usd']:,.0f} SR {v['sharpe']} DD {v['max_drawdown_pct']}% TO {v.get('turnover_per_year_x','-')}" for k, v in R.items() if k != "cash"))
for s in sens: print(s["variant"], {k: (v["end_usd"], v["sharpe"], v["max_drawdown_pct"], v["turnover_per_year_x"]) for k, v in s.items() if k != "variant"})
