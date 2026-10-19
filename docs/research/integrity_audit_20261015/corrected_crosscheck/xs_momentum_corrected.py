"""Weekly cross-sectional momentum test, implementing PREREGISTRATION.md exactly. Research only.
Usage: python3 xs_momentum.py CANDLE_DIR OUT_JSON"""
import json, os, sys, math, statistics, hashlib, datetime as dt
from statistics import NormalDist
D = 86400
CANDLES, OUT = sys.argv[1], sys.argv[2]
STABLE = {"USDC","USDT","DAI","PYUSD","EURC","GUSD","PAX","USDS","WBTC","CBETH","UST","TUSD","BUSD","USDP","FDUSD","EURT","GYEN","USD1"}
def excluded(base): return base in STABLE or "USD" in base

px = {}   # pid -> {day: (open, close, usdvol)}
hashes = {}
for fn in sorted(os.listdir(CANDLES)):
    if not fn.endswith(".json") or fn.startswith("_"): continue
    pid = fn[:-5]; base = pid.split("-")[0]
    if excluded(base): continue
    raw = open(os.path.join(CANDLES, fn), "rb").read(); hashes[pid] = hashlib.sha256(raw).hexdigest()[:16]
    rows = json.loads(raw)
    d = {}
    for t, lo, hi, op, cl, vol in rows:
        if cl and cl > 0 and op and op > 0: d[int(t) // D] = (float(op), float(cl), float(cl) * float(vol))
    if len(d) >= 90: px[pid] = d
days_all = sorted({k for d in px.values() for k in d})
D0, D1 = days_all[0], days_all[-1]
first_day = {p: min(d) for p, d in px.items()}

def last_close(p, day):
    """Latest close on or before `day`. A coin that stops trading (e.g. delisted) stays valued at its last traded close
    and is sold at that price at the next rebalance (decided before any result was seen; not in the original prereg)."""
    d = px[p]
    for k in range(day, first_day[p] - 1, -1):
        if k in d: return d[k][1]
    return None

def universe(day, n):
    c = []
    for p, d in px.items():
        if day not in d or day - first_day[p] < 90: continue
        vols = [d[k][2] for k in range(day - 29, day + 1) if k in d]
        if len(vols) < 20: continue
        c.append((statistics.median(vols), p))
    c.sort(reverse=True)
    return [p for _, p in c[:n]]

def ret(p, day, L):
    d = px[p]
    if day in d and (day - L) in d: return d[day][1] / d[day - L][1] - 1
    return None

def is_sunday(day): return dt.datetime.fromtimestamp(day * D, dt.timezone.utc).weekday() == 6

def target_xs(day, L=28, K=5, N=20):
    u = universe(day, N)
    r = [(ret(p, day, L), p) for p in u]
    r = sorted([x for x in r if x[0] is not None and x[0] > 0], reverse=True)[:K]
    return {p: 1.0 / K for _, p in r}

def target_ew(day, N=20, **kw):
    u = universe(day, N)
    return {p: 1.0 / len(u) for p in u} if u else {}

def target_btc(day, **kw): return {"BTC-USD": 1.0}

def target_majors(day, **kw):
    w = {}
    for a in ("BTC-USD", "ETH-USD"):
        if a not in px: continue
        r28 = ret(a, day, 28)
        rs = [px[a][k][1] / px[a][k - 1][1] - 1 for k in range(day - 29, day + 1) if k in px[a] and k - 1 in px[a]]
        if r28 is None or r28 <= 0 or len(rs) < 25: continue
        vol = statistics.pstdev(rs) * math.sqrt(365)
        w[a] = 0.5 * min(1.0, 0.5 / vol) if vol > 0 else 0
    return w

def simulate(tfun, lo, hi, cost=0.0075, weekly=True, **kw):
    """Decide at close of decision day, trade at next day's open, mark at closes. BTC hold: buy once."""
    cash, units = 1000.0, {}
    curve = []; pending = None; turnover = 0.0
    start = lo
    while not is_sunday(start): start += 1
    pending = tfun(start, **kw)
    for day in range(start + 1, hi + 1):
        if pending is not None:
            # CORRECTED (pre-stated rule, integrity audit 2026-10-15): trade only at real opens.
            frozen = {p: q for p, q in units.items() if not (p in px and day in px[p])}
            prices = {p: px[p][day][0] for p in set(units) | set(pending) if p in px and day in px[p]}
            nav = cash + sum(q * prices[p] for p, q in units.items() if p not in frozen)   # tradable NAV
            tw = {p: w for p, w in pending.items() if p in prices and p not in frozen}
            want = {p: nav * w / prices[p] for p, w in tw.items()}
            traded = sum(abs(want.get(p, 0) - units.get(p, 0)) * prices[p] for p in (set(want) | set(units)) - set(frozen))
            fee = traded * cost; turnover += traded / nav if nav > 0 else 0
            nav -= fee
            units = {p: nav * tw[p] / prices[p] for p in tw}
            cash = nav - sum(units[p] * prices[p] for p in units)
            units.update(frozen)
            pending = None
        nav = cash + sum(q * (last_close(p, day) or 0) for p, q in units.items())
        curve.append(nav)
        if weekly and day < hi and is_sunday(day) and tfun is not target_btc:
            pending = tfun(day, **kw)
    return curve, turnover

def stats(curve, lo, hi):
    r = [curve[i] / curve[i - 1] - 1 for i in range(1, len(curve))]
    yrs = len(curve) / 365
    sd = statistics.pstdev(r)
    pk = curve[0]; mdd = 0
    for v in curve: pk = max(pk, v); mdd = max(mdd, 1 - v / pk)
    return {"end_usd": round(curve[-1], 2), "cagr_pct": round(((curve[-1] / 1000) ** (1 / yrs) - 1) * 100, 1),
            "sharpe": round(statistics.mean(r) / sd * math.sqrt(365), 3) if sd else 0,
            "max_drawdown_pct": round(mdd * 100, 1), "days": len(curve)}, r

def day_of(y, m, d): return int(dt.datetime(y, m, d, tzinfo=dt.timezone.utc).timestamp()) // D
PER = {"A": (day_of(2018, 1, 1), day_of(2021, 12, 31)), "B": (day_of(2022, 1, 1), D1), "FULL": (day_of(2018, 1, 1), D1)}
Z = NormalDist(); G = 0.5772156649
def dsr(r, N, V=0.0004636024000905694):
    T = len(r); m = statistics.mean(r); s = statistics.pstdev(r); sr = m / s
    sk = sum(((x - m) / s) ** 3 for x in r) / T; ku = sum(((x - m) / s) ** 4 for x in r) / T
    s0 = 0 if N <= 1 else math.sqrt(V) * ((1 - G) * Z.inv_cdf(1 - 1 / N) + G * Z.inv_cdf(1 - 1 / (N * math.e)))
    return round(Z.cdf((sr - s0) * math.sqrt(T - 1) / math.sqrt(1 - sk * sr + (ku - 1) / 4 * sr ** 2)), 4)

out = {"artifact_type": "research_only_preregistered_test", "prereg_sha256": hashlib.sha256(open(os.path.join(os.path.dirname(__file__), "PREREGISTRATION.md"), "rb").read()).hexdigest(),
       "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "products_used": len(px),
       "data_first_day": str(dt.date.fromtimestamp(D0 * D)), "data_last_day": str(dt.date.fromtimestamp(D1 * D)), "candle_file_sha256_16": hashes}
res = {}; rets = {}
for per, (lo, hi) in PER.items():
    res[per] = {}
    for name, f in (("xs_momentum", target_xs), ("hold_btc", target_btc), ("equal_weight_top20", target_ew), ("btc_eth_trend", target_majors)):
        c, to = simulate(f, lo, hi)
        s, r = stats(c, lo, hi); s["annual_turnover_x"] = round(to / (len(c) / 365), 1)
        res[per][name] = s
        if per == "FULL": rets[name] = r
out["primary"] = res
A, B = res["A"], res["B"]
checks = {
 "1_positive_cagr_A_and_B": A["xs_momentum"]["cagr_pct"] > 0 and B["xs_momentum"]["cagr_pct"] > 0,
 "2_sharpe_above_btc_A_and_B": A["xs_momentum"]["sharpe"] > A["hold_btc"]["sharpe"] and B["xs_momentum"]["sharpe"] > B["hold_btc"]["sharpe"],
 "3_sharpe_above_equal_weight_A_and_B": A["xs_momentum"]["sharpe"] > A["equal_weight_top20"]["sharpe"] and B["xs_momentum"]["sharpe"] > B["equal_weight_top20"]["sharpe"]}
d = {f"N={n}": dsr(rets["xs_momentum"], n) for n in (1, 4, 15, 120, 576)}
checks["4_dsr_N15_ge_0.90"] = d["N=15"] >= 0.90
out["dsr_full_broad_V"] = d; out["pass_checks"] = checks; out["verdict"] = "PASS" if all(checks.values()) else "FAIL"
sens = []
for label, kw, cost in [("L14", {"L": 14}, .0075), ("L56", {"L": 56}, .0075), ("K3", {"K": 3}, .0075), ("K10", {"K": 10}, .0075),
                        ("N10", {"N": 10}, .0075), ("N40", {"N": 40}, .0075), ("cost0.5", {}, .005), ("cost1.0", {}, .01)]:
    row = {"variant": label}
    for per in ("A", "B", "FULL"):
        lo, hi = PER[per]; c, _ = simulate(target_xs, lo, hi, cost=cost, **kw); row[per] = stats(c, lo, hi)[0]
    sens.append(row)
out["sensitivity_reported_only"] = sens
json.dump(out, open(OUT, "x"), indent=1)  # scratch copy, corrected execution
print(json.dumps({k: out[k] for k in ("products_used", "data_first_day", "data_last_day", "primary", "dsr_full_broad_V", "pass_checks", "verdict")}, indent=1))
for row in sens: print(row["variant"], {p: (row[p]["cagr_pct"], row[p]["sharpe"], row[p]["max_drawdown_pct"]) for p in ("A", "B", "FULL")})
