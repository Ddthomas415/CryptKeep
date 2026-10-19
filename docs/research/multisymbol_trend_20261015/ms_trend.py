"""E10 slow-trend portfolio across the Coinbase core pairs, implementing PREREGISTRATION.md. Research only.
Usage: python3 -B ms_trend.py DIR_WITH_maj   (maj/ = hash-checked majors files, used only for the simulator check)"""
import datetime as dt, hashlib, json, math, statistics, sys
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
DATA = ROOT / "research/multisymbol_trend_20261015/data"
sums = dict(reversed(l.split()) for l in (DATA / "SHA256SUMS").read_text().splitlines())
for f, h in sums.items():
    if sha(DATA / f) != h: raise SystemExit(f"data hash mismatch {f}")
from scripts.research.corrected_research_math import rebalance
from scripts.research.rerun_frozen_stress import load_frozen, run as harness_run
D = 86400; UTC = dt.timezone.utc
CORE = ["BTC", "ETH", "SOL", "DOGE", "LTC", "LINK", "AVAX", "ADA", "XRP", "DOT"]
def load_api(p):     # Coinbase API rows: time, low, high, open, close, volume
    return {int(r[0]) // D: (float(r[3]), float(r[4])) for r in json.load(open(p)) if float(r[3]) > 0 and float(r[4]) > 0}
def load_majors(p):  # majors files: time, open, high, low, close, volume
    return {int(r[0]) // D: (float(r[1]), float(r[4])) for r in json.load(open(p))}
sunday = lambda d: dt.datetime.fromtimestamp(d * D, UTC).weekday() == 6
iso = lambda d: dt.datetime.fromtimestamp(d * D, UTC).date().isoformat()

def eligible(px, s, d): return all(k in px[s] for k in range(d - 60, d + 1))
def vol30(px, s, d): return statistics.pstdev([px[s][k][1] / px[s][k - 1][1] - 1 for k in range(d - 29, d + 1)]) * math.sqrt(365)
def ret28(px, s, d): return px[s][d][1] / px[s][d - 28][1] - 1
def last_close(px, s, d):
    for k in range(d, min(px[s]) - 1, -1):
        if k in px[s]: return px[s][k][1]
    raise ValueError(f"no close for {s} on or before {iso(d)}")

def target(kind, px, syms, d, volscale=True):
    el = [s for s in syms if eligible(px, s, d)]
    if kind == "trend":
        n = len(el)
        return {s: (1 / n) * (min(1.0, 0.5 / vol30(px, s, d)) if volscale else 1.0) for s in el if ret28(px, s, d) > 0} if n else {}
    if kind == "equal":
        return {s: 1 / len(el) for s in el} if el else {}
    if kind == "hold":
        return {syms[0]: 1.0} if syms[0] in el else {}
    raise ValueError(kind)

def sim(kind, px, syms, lo, hi, fee, slip, band=0.0, volscale=True):
    """First decision at Sunday `lo` close; execute at next open over the tradable sub-account; mark at closes."""
    cash, units = 1000.0, {}; curve = [1000.0]; traded = 0.0; frozen_days = 0
    pending = target(kind, px, syms, lo, volscale)
    for d in range(lo + 1, hi + 1):
        if pending is not None:
            tradable = [s for s in sorted(set(units) | set(pending)) if d in px[s]]
            frozen = [s for s in units if d not in px[s]]
            prices = {s: px[s][d][0] for s in tradable}
            nav = cash + sum(units[s] * prices[s] for s in units if s in prices) + sum(units[s] * last_close(px, s, d - 1) for s in frozen)
            cur = {s: units.get(s, 0) * prices[s] / nav for s in tradable}
            move = [s for s in tradable if abs(pending.get(s, 0) - cur[s]) >= band - 1e-12] if band > 0 else tradable
            if move:
                sub = {s: units.get(s, 0) for s in move}
                eq_sub = cash + sum(sub[s] * prices[s] for s in move)
                want = {s: pending.get(s, 0) * nav for s in move}; tot = sum(want.values())
                scale = min(1.0, eq_sub / tot) if tot > 0 else 1.0
                wts = {s: want[s] * scale / eq_sub for s in move if want[s] > 0} if eq_sub > 0 else {}
                before = {s: sub[s] * prices[s] for s in move}
                cash, u2 = rebalance(cash, sub, {s: prices[s] for s in move}, wts, fee, slip)
                traded += sum(abs(u2.get(s, 0) * prices[s] - before[s]) for s in move) / nav
                for s in move:
                    if u2.get(s, 0) > 0: units[s] = u2[s]
                    else: units.pop(s, None)
            pending = None
        frozen_days += any(d not in px[s] for s in units)
        curve.append(cash + sum(q * last_close(px, s, d) for s, q in units.items()))
        if d < hi and kind != "hold" and sunday(d): pending = target(kind, px, syms, d, volscale)
    return curve, traded / ((hi - lo) / 365), frozen_days

def stats(curve, to=None):
    r = [curve[k] / curve[k - 1] - 1 for k in range(1, len(curve))]; sd = statistics.pstdev(r); yrs = len(r) / 365
    pk = curve[0]; mdd = 0
    for x in curve: pk = max(pk, x); mdd = max(mdd, 1 - x / pk)
    out = {"end_usd": round(curve[-1], 2), "cagr_pct": round(((curve[-1] / 1000) ** (1 / yrs) - 1) * 100, 1),
           "sharpe": round(statistics.mean(r) / sd * math.sqrt(365), 3) if sd else 0.0, "max_drawdown_pct": round(mdd * 100, 1), "days": len(r)}
    if to is not None: out["turnover_per_year_x"] = round(to, 2)
    return out

# ---- simulator check against the reviewed harness (majors BTC/ETH, fee 0.50%, slip 0.05%, Sunday 2020-01-05) ----
ns = load_frozen(sys.argv[1]); hdays = ns["days"]
lo_i = next(i for i, d in enumerate(hdays) if d >= 1578182400); hi_i = len(hdays) - 1
maj = {a: load_majors(ROOT / f"docs/research/majors_trend_20261009/{a}-USD_d1.json") for a in ("BTC", "ETH")}
mine, _, _ = sim("trend", maj, ["BTC", "ETH"], hdays[lo_i] // D, hdays[hi_i] // D, 0.005, 0.0005)
ref, _ = harness_run(ns, "rule", lo_i, hi_i, fee=0.005)
diff = max(abs(x - y) for x, y in zip(mine, ref))
if len(mine) != len(ref) or diff > 1e-6: raise SystemExit(f"simulator check FAILED: diff {diff} len {len(mine)} vs {len(ref)}")
check = f"new simulator reproduces reviewed harness (BTC+ETH, Sunday 2020-01-05..{iso(hdays[hi_i] // D)}) max diff {diff:.2e} USD"

px = {s: load_api(DATA / f"{s}-USD.json") for s in CORE}
end_day = min(max(px[s]) for s in CORE)
def first_sunday(day):
    while not sunday(day): day += 1
    return day
dnum = lambda s: int(dt.datetime.fromisoformat(s).replace(tzinfo=UTC).timestamp()) // D
PER = {"D": (first_sunday(dnum("2019-01-01")), dnum("2023-12-31")), "H": (first_sunday(dnum("2024-01-01")), end_day)}
SLIP = 0.001
out = {"artifact_type": "research_only_preregistered_test_E10", "prereg_sha256": sha(HERE / "PREREGISTRATION.md"), "script_sha256": sha(__file__),
       "inputs_sha256": got, "data_sha256": sums, "simulator_check": check, "slippage": SLIP,
       "periods": {k: [iso(a), iso(b)] for k, (a, b) in PER.items()}, "results": {}}
curves = {}
for fee in (0.005, 0.009):
    R = out["results"][str(fee)] = {}
    for p, (lo, hi) in PER.items():
        c, to, fz = sim("trend", px, CORE, lo, hi, fee, SLIP); curves[(fee, p)] = c
        ci, toi, _ = sim("trend", px, ["BTC", "ETH"], lo, hi, fee, SLIP)
        ch, _, _ = sim("hold", px, ["BTC"], lo, hi, fee, SLIP)
        ce, toe, _ = sim("equal", px, CORE, lo, hi, fee, SLIP)
        R[p] = {"portfolio_core10": {**stats(c, to), "days_with_frozen_holding": fz}, "incumbent_btc_eth": stats(ci, toi),
                "hold_btc": stats(ch), "equal_weight_core": stats(ce, toe), "cash": {"end_usd": 1000.0, "sharpe": 0.0, "max_drawdown_pct": 0.0}}
def checks(R):
    Dd, H = R["D"], R["H"]; P, I = "portfolio_core10", "incumbent_btc_eth"
    return {"D_sharpe_ge_incumbent": Dd[P]["sharpe"] >= Dd[I]["sharpe"],
            "D_maxdd_le_incumbent_plus_2": Dd[P]["max_drawdown_pct"] <= Dd[I]["max_drawdown_pct"] + 2,
            "H_sharpe_ge_incumbent_minus_0.05": H[P]["sharpe"] >= H[I]["sharpe"] - 0.05,
            "H_maxdd_le_incumbent_plus_2": H[P]["max_drawdown_pct"] <= H[I]["max_drawdown_pct"] + 2}
out["pass_checks"] = {f: checks(out["results"][f]) for f in ("0.005", "0.009")}
out["verdict"] = "PASS" if all(all(v.values()) for v in out["pass_checks"].values()) else "FAIL"
# secondary: per-symbol standalone (fee 0.50%)
stand = {}
for s in CORE:
    row = {}
    for p, (lo, hi) in PER.items():
        start = lo
        while start <= hi and not (sunday(start) and eligible(px, s, start)): start += 1
        if start > hi: row[p] = None; continue
        cs, tos, fz = sim("trend", px, [s], start, hi, 0.005, SLIP)
        ch, _, _ = sim("hold", px, [s], start, hi, 0.005, SLIP)
        row[p] = {"start": iso(start), "trend": {**stats(cs, tos), "days_with_frozen_holding": fz}, "hold": stats(ch)}
    Dd, H = row["D"], row["H"]
    if Dd is None or Dd["trend"]["days"] < 365 or H is None: cls = "INCONCLUSIVE"
    elif all(row[p]["trend"]["sharpe"] >= row[p]["hold"]["sharpe"] and row[p]["trend"]["max_drawdown_pct"] < row[p]["hold"]["max_drawdown_pct"] for p in ("D", "H")): cls = "CANDIDATE"
    elif all(row[p]["trend"]["sharpe"] < row[p]["hold"]["sharpe"] for p in ("D", "H")): cls = "REJECTED_UNDER_TESTED_CONDITIONS"
    else: cls = "INCONCLUSIVE"
    row["classification"] = cls; stand[s] = row
out["standalone_fee0.50"] = stand
Z = NormalDist(); G = 0.5772156649
def dsr(r, N, V=0.0004636024000905694):
    T = len(r); m = statistics.mean(r); sd = statistics.pstdev(r); sr = m / sd
    sk = sum(((x - m) / sd) ** 3 for x in r) / T; ku = sum(((x - m) / sd) ** 4 for x in r) / T
    s0 = 0 if N <= 1 else math.sqrt(V) * ((1 - G) * Z.inv_cdf(1 - 1 / N) + G * Z.inv_cdf(1 - 1 / (N * math.e)))
    return round(Z.cdf((sr - s0) * math.sqrt(T - 1) / math.sqrt(1 - sk * sr + (ku - 1) / 4 * sr ** 2)), 4)
rr = [c[k] / c[k - 1] - 1 for c in (curves[(0.005, "D")], curves[(0.005, "H")]) for k in range(1, len(c))]
out["dsr_portfolio_DH_fee0.50"] = {f"N={n}": dsr(rr, n) for n in (26, 120)}
sens = []
for label, kw in (("band0.05", {"band": 0.05}), ("no_volscale", {"volscale": False})):
    row = {"variant": label}
    for p, (lo, hi) in PER.items():
        c, to, _ = sim("trend", px, CORE, lo, hi, 0.005, SLIP, **kw); row[p] = stats(c, to)
    sens.append(row)
out["sensitivity_reported_only_fee0.50"] = sens
json.dump(out, open(HERE / "ms_trend_result.json", "x"), indent=1)
print(check); print(json.dumps({k: out[k] for k in ("periods", "pass_checks", "verdict", "dsr_portfolio_DH_fee0.50")}, indent=1))
for fee in ("0.005", "0.009"):
    for p in ("D", "H"):
        R = out["results"][fee][p]
        print(fee, p, " | ".join(f"{k}: ${v['end_usd']:,.0f} SR {v['sharpe']} DD {v['max_drawdown_pct']}%" + (f" TO {v['turnover_per_year_x']}" if 'turnover_per_year_x' in v else "") for k, v in R.items() if k != "cash"))
for s, row in stand.items():
    print(s, row["classification"], {p: (row[p]["start"], row[p]["trend"]["sharpe"], row[p]["hold"]["sharpe"], row[p]["trend"]["max_drawdown_pct"], row[p]["hold"]["max_drawdown_pct"]) if row[p] else None for p in ("D", "H")})
for r in sens: print(r["variant"], {p: (r[p]["end_usd"], r[p]["sharpe"], r[p]["max_drawdown_pct"]) for p in ("D", "H")})
