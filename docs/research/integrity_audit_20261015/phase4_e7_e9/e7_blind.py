#!/usr/bin/env python3
"""E7 blind independent reimplementation (stdlib only). Spec: PREREGISTRATION.md."""
import json, math, hashlib, os, statistics, datetime as dt, bisect
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
FUND_SHA = "15edda37d3119f1cdadcbfa8ec10ed938fe359c9dd89e920384471bd167db3a9"
DAY = 86400
SLIP = 0.0005
V_DSR = 0.0004636024000905694
GAMMA = 0.5772156649015329
ROUND_FUNDING_TIMES = bool(int(os.environ.get("E7_ROUND", "0")))  # variant check only


def ts(s):
    return int(dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())


def iso(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d")


# ---------------- data ----------------
def load_prices(name):
    rows = json.load(open(os.path.join(DATA, name)))
    out = {}
    for r in rows:
        assert r[0] % DAY == 0
        out[r[0]] = (float(r[1]), float(r[2]), float(r[3]), float(r[4]))
    return out


PX = {"BTC": load_prices("BTC-USD_d1.json"), "ETH": load_prices("ETH-USD_d1.json")}


def px(a, day, field):
    if day not in PX[a]:
        raise SystemExit(f"missing data refused: {a} {iso(day)}")
    return PX[a][day][{"open": 0, "close": 3}[field]]


fpath = os.path.join(DATA, "binance_funding_raw.jsonl")
sha = hashlib.sha256(open(fpath, "rb").read()).hexdigest()
if sha != FUND_SHA:
    raise SystemExit("funding sha256 mismatch " + sha)
FUND = {"BTC": [], "ETH": []}
for line in open(fpath):
    if not line.strip():
        continue
    o = json.loads(line)
    if o.get("type") == "error" or "error" in o:
        raise SystemExit("error line in funding file")
    if o.get("type") != "funding":
        continue
    a = {"BTCUSDT": "BTC", "ETHUSDT": "ETH"}[o["symbol"]]
    t = int(o["fundingTime"])
    if ROUND_FUNDING_TIMES:
        t = int(round(t / 28800000.0)) * 28800000
    FUND[a].append((t, float(o["fundingRate"])))
for a in FUND:
    FUND[a].sort()
    tt = [t for t, _ in FUND[a]]
    assert len(set(tt)) == len(tt)
    gaps = [b - x for x, b in zip(tt, tt[1:])]
    assert all(abs(g - 28800000) < 1000 for g in gaps), "funding gap"

# rolling 21-print means (annualised) at each print i>=20
ROLL = {}
for a in FUND:
    rates = [r for _, r in FUND[a]]
    times = [t for t, _ in FUND[a]]
    lv = []
    for i in range(20, len(rates)):
        lv.append((times[i], sum(rates[i - 20:i + 1]) / 21.0 * 3 * 365))
    ROLL[a] = lv


def pct_linear(sorted_vals, q):
    # type-7 (linear interpolation) percentile
    n = len(sorted_vals)
    h = (n - 1) * q
    lo = math.floor(h)
    hi = min(lo + 1, n - 1)
    return sorted_vals[lo] + (h - lo) * (sorted_vals[hi] - sorted_vals[lo])


_cache = {}


def brake_state(fa, decision_close_ms, q):
    """Return (available, extreme, level, threshold) for funding asset fa."""
    key = (fa, decision_close_ms, q)
    if key in _cache:
        return _cache[key]
    first = FUND[fa][0][0]
    if decision_close_ms - first < 365 * DAY * 1000:
        res = (False, False, None, None)
    else:
        times = [t for t, _ in ROLL[fa]]
        k = bisect.bisect_left(times, decision_close_ms)  # strictly before
        hist = sorted(v for _, v in ROLL[fa][:k])
        level = ROLL[fa][k - 1][1]
        thr = pct_linear(hist, q)
        res = (True, level >= thr, level, thr)
    _cache[key] = res
    return res


# ---------------- candidate ----------------
def candidate_weight(a, day):
    c = [px(a, day - i * DAY, "close") for i in range(30, -1, -1)]  # 31 closes, t-30..t
    c28 = px(a, day - 28 * DAY, "close")
    if c[-1] / c28 - 1 <= 0:
        return 0.0
    rets = [c[i] / c[i - 1] - 1 for i in range(1, 31)]
    vol = statistics.pstdev(rets) * math.sqrt(365)
    return 0.5 * min(1.0, 0.50 / vol)


def make_rule(kind, q=0.90, mult=0.5, btc_for_both=False):
    def rule(day, counts):
        w = {}
        for a in ("BTC", "ETH"):
            base = candidate_weight(a, day)
            if kind == "candidate":
                w[a] = base
                continue
            fa = "BTC" if btc_for_both else a
            avail, ext, _, _ = brake_state(fa, (day + DAY) * 1000, q)
            if ext:
                counts[a] += 1
                w[a] = base * mult
            else:
                w[a] = base
        return w
    return rule


def hold_btc(first):
    def rule(day, counts):
        return None if day != first else {"BTC": 1.0, "ETH": 0.0}
    return rule


def mix(day, counts):
    return {"BTC": 0.25, "ETH": 0.25}


def cost_of(delta, fee):
    if delta >= 0:
        return delta * ((1 + SLIP) * (1 + fee) - 1)
    return -delta * (1 - (1 - SLIP) * (1 - fee))


def solve_E(nav, held_val, w, fee):
    f = lambda E: E + sum(cost_of(w[a] * E - held_val[a], fee) for a in w) - nav
    lo, hi = 0.0, nav
    if f(hi) <= 0:
        return hi
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2


def first_sunday_on_or_after(d):
    while dt.datetime.fromtimestamp(d, dt.timezone.utc).weekday() != 6:
        d += DAY
    return d


def run(rule_factory, start_day, end_day, fee):
    """start_day: first decision day (Sunday bar start). NAV marked at closes through end_day."""
    days = list(range(start_day, end_day + DAY, DAY))
    cash, units = 1000.0, {"BTC": 0.0, "ETH": 0.0}
    nav = [1000.0]
    counts = {"BTC": 0, "ETH": 0}
    rule = rule_factory
    pending = None
    first = True
    for i, d in enumerate(days):
        if not first:
            if pending is not None:
                o = {a: px(a, d, "open") for a in units}
                held = {a: units[a] * o[a] for a in units}
                navo = cash + sum(held.values())
                E = solve_E(navo, held, pending, fee)
                units = {a: pending[a] * E / o[a] for a in units}
                cash = E * (1 - sum(pending.values()))
                pending = None
            nav.append(cash + sum(units[a] * px(a, d, "close") for a in units))
        first = False
        is_sunday = dt.datetime.fromtimestamp(d, dt.timezone.utc).weekday() == 6
        if is_sunday and d != end_day:
            w = rule(d, counts)
            if w is not None:
                pending = w
    return nav, counts


def stats(nav):
    r = [b / a - 1 for a, b in zip(nav, nav[1:])]
    sd = statistics.pstdev(r)
    sh = statistics.mean(r) / sd * math.sqrt(365) if sd > 0 else None
    peak, mdd = nav[0], 0.0
    for v in nav:
        peak = max(peak, v)
        mdd = max(mdd, 1 - v / peak)
    return {"end_usd": round(nav[-1], 2), "sharpe": None if sh is None else round(sh, 4),
            "max_drawdown_pct": round(mdd * 100, 2), "sharpe_raw": sh, "max_drawdown_raw": mdd}, r


def dsr(r, N):
    T = len(r)
    m = statistics.mean(r)
    sd = statistics.pstdev(r)
    sr = m / sd
    skew = sum((x - m) ** 3 for x in r) / T / sd ** 3
    kurt = sum((x - m) ** 4 for x in r) / T / sd ** 4
    nd = NormalDist()
    sr0 = math.sqrt(V_DSR) * ((1 - GAMMA) * nd.inv_cdf(1 - 1 / N) + GAMMA * nd.inv_cdf(1 - 1 / (N * math.e)))
    z = (sr - sr0) * math.sqrt(T - 1) / math.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr ** 2)
    return {"N": N, "dsr": round(nd.cdf(z), 4), "sr_daily": round(sr, 6), "sr0_daily": round(sr0, 6),
            "T": T, "skew": round(skew, 4), "kurtosis": round(kurt, 4)}


PERIODS = {
    "D": (first_sunday_on_or_after(ts("2020-12-01")), ts("2023-12-31")),
    "H": (first_sunday_on_or_after(ts("2024-01-01")), ts("2026-10-08")),
}
FEES = {"0.50%": 0.005, "0.90%": 0.009}


def main():
    out = {"spec": "PREREGISTRATION.md (E7)", "funding_sha256": sha, "funding_sha256_ok": sha == FUND_SHA,
           "round_funding_times_variant": ROUND_FUNDING_TIMES,
           "periods": {k: {"first_decision_close_of_day": iso(s), "last_mark_day": iso(e)} for k, (s, e) in PERIODS.items()},
           "results": {}, "brake_weeks": {}}
    braked_returns = {}
    for fname, fee in FEES.items():
        out["results"][fname] = {}
        for p, (s, e) in PERIODS.items():
            res = {}
            nav, cnt = run(make_rule("braked"), s, e, fee)
            res["braked"], rb = stats(nav)
            if fname == "0.50%":
                out["brake_weeks"][p] = cnt
                braked_returns[p] = rb
            nav, _ = run(make_rule("candidate"), s, e, fee)
            res["candidate"], _ = stats(nav)
            nav, _ = run(hold_btc(s), s, e, fee)
            res["hold_btc"], _ = stats(nav)
            nav, _ = run(mix, s, e, fee)
            res["mix_25_25_50"], _ = stats(nav)
            res["cash"] = {"end_usd": 1000.0, "sharpe": None, "max_drawdown_pct": 0.0}
            out["results"][fname][p] = res

    # brake weeks: weeks (executed decisions) with brake on for either asset, D
    def any_weeks(s, e):
        n = 0
        d = s
        while d < e:
            if dt.datetime.fromtimestamp(d, dt.timezone.utc).weekday() == 6:
                if any(brake_state(a, (d + DAY) * 1000, 0.90)[1] for a in ("BTC", "ETH")):
                    n += 1
            d += DAY
        return n
    for p, (s, e) in PERIODS.items():
        out["brake_weeks"][p]["either_asset"] = any_weeks(s, e)
        out["brake_weeks"][p]["executed_decisions"] = sum(
            1 for d in range(s, e, DAY) if dt.datetime.fromtimestamp(d, dt.timezone.utc).weekday() == 6)

    # PASS checks
    checks = {}
    for fname in FEES:
        R = out["results"][fname]
        bD, cD, bH, cH = R["D"]["braked"], R["D"]["candidate"], R["H"]["braked"], R["H"]["candidate"]
        # compared unrounded, with a 1e-9 tolerance so float noise (~1e-16) counts as a tie
        TOL = 1e-9
        c1 = bD["sharpe_raw"] > cD["sharpe_raw"] + TOL and bD["max_drawdown_raw"] < cD["max_drawdown_raw"] - TOL
        c2 = bH["sharpe_raw"] >= cH["sharpe_raw"] - 0.05 - TOL and bH["max_drawdown_raw"] <= cH["max_drawdown_raw"] + TOL
        checks[fname + "_detail"] = {
            "D_sharpe_braked_minus_candidate": bD["sharpe_raw"] - cD["sharpe_raw"],
            "D_mdd_braked_minus_candidate": bD["max_drawdown_raw"] - cD["max_drawdown_raw"],
            "H_sharpe_braked_minus_candidate": bH["sharpe_raw"] - cH["sharpe_raw"],
            "H_mdd_braked_minus_candidate": bH["max_drawdown_raw"] - cH["max_drawdown_raw"]}
        checks[fname] = {"cond1_D": c1, "cond2_H": c2}
    checks = {k: v for k, v in checks.items()}
    passed = checks["0.50%"]["cond1_D"] and checks["0.50%"]["cond2_H"] and checks["0.90%"]["cond1_D"] and checks["0.90%"]["cond2_H"]
    inconclusive = out["brake_weeks"]["D"]["either_asset"] < 4
    out["pass_checks"] = checks
    out["verdict"] = "INCONCLUSIVE" if inconclusive else ("PASS" if passed else "FAIL")

    # sensitivities (0.50% fee, reported only)
    sens = {"q80": make_rule("braked", q=0.80), "q95": make_rule("braked", q=0.95),
            "brake_to_zero": make_rule("braked", mult=0.0), "btc_funding_both": make_rule("braked", btc_for_both=True)}
    out["sensitivities_fee_0.50%"] = {}
    for k, rule in sens.items():
        out["sensitivities_fee_0.50%"][k] = {}
        for p, (s, e) in PERIODS.items():
            nav, cnt = run(rule, s, e, 0.005)
            st, _ = stats(nav)
            st["brake_weeks"] = cnt
            out["sensitivities_fee_0.50%"][k][p] = st

    r = braked_returns["D"] + braked_returns["H"]
    out["dsr_braked_D_plus_H_fee_0.50%"] = [dsr(r, 15), dsr(r, 120)]
    out["shared_assumptions_from_auditor"] = [
        "Frozen candidate: w=0.5*min(1,0.50/vol30) if close[t]/close[t-28]-1>0 else 0; vol30=pstdev of 30 daily simple returns ending t * sqrt(365)",
        "Execution: bisection for post-cost E with E+cost(E)=NAV at opens; buy cost delta*((1+slip)(1+fee)-1), sell cost -delta*(1-(1-slip)(1-fee)); hold w*E/open units, cash E*(1-sum w)",
        "NAV: $1,000 at first decision close (first NAV point), marked at every daily close through period end; decision on period's last day not executed; Sharpe=mean/pstdev daily*sqrt(365); MDD on daily NAV",
        "Hold BTC: 100% BTC at open after first decision, same costs; mix: weekly to 25/25/50, same timing/costs",
        "DSR: Bailey & Lopez de Prado formula, per-day SR, ordinary kurtosis, V=0.0004636024000905694",
    ]
    out["choices"] = CHOICES
    return out


CHOICES = [
    "Decision close = close of the Sunday UTC daily bar (bar start Sunday 00:00, close = Monday 00:00 UTC); trade at Monday open (same instant), mark at closes.",
    "Funding level = mean of the last 21 prints with raw fundingTime (ms) strictly < decision close, x3x365. Raw ms timestamps jitter by up to ~50ms around the 8h slot; a variant rounding times to the slot gave identical results (same verdict, same numbers).",
    "Percentile history = the series of rolling 21-print annualised means ending at every print strictly before the decision close (includes the current level). Ambiguous: prereg could also mean raw prints; not tested.",
    "90th percentile = linear interpolation (type 7, numpy default); 'extreme' iff level >= that value (ties count as extreme, per 'at or above').",
    "365-day requirement = decision close >= first print time of that asset + 365 days (BTC: from 2020-09-09 08:00; ETH: from 2020-11-26 08:00).",
    "INCONSISTENCY: prereg says D starts when 'the BTC brake becomes available' (2020-12-01), but by the 365-day rule BTC is available from 2020-09-09; 2020-12-01 actually matches ETH availability (~2020-11-27, which the prereg also states). Both brakes are therefore available for all of D; 'before that, ETH is unbraked' never binds in D or H.",
    "Periods: D first decision = first Sunday >= 2020-12-01 = 2020-12-06, marked through 2023-12-31 close (a Sunday; its decision not executed). H first decision = first Sunday >= 2024-01-01 = 2024-01-07 (NAV starts there; 2024-01-01..06 not in H), marked through 2026-10-08 close.",
    "Brake weeks = executed Sunday decisions (excluding the unexecuted last-day decision) at which the asset's brake was on. INCONCLUSIVE test uses weeks with the brake on for EITHER asset in D (11); per-asset counts (BTC 10, ETH 8) are also >= 4, so the choice does not matter.",
    "Brake multiplies the candidate target only; when candidate weight is 0 the brake still counts as 'on' in the week counts if the funding condition holds (counts reflect the signal, not binding exposure cuts).",
    "PASS comparisons made on unrounded values with 1e-9 tolerance. D max drawdown of braked and candidate are identical (32.772097% at 0.50%, 35.329349% at 0.90%; differences ~3e-16 / 8e-16 are float noise, sign differs between fees) because the brake was not active over the D drawdown. Without tolerance, cond1 at 0.50% would spuriously read True; verdict is FAIL either way since cond1 fails at 0.90% (tie or float-noise 'higher').",
    "Sensitivities run at the 0.50% fee for D and H, each changing one parameter of the primary setting (q=0.80; q=0.95; multiplier 0; BTC funding level and BTC percentile/availability used for ETH).",
    "DSR on concatenated braked daily returns D then H at 0.50% fee (T=2125); population skew and ordinary (non-excess) kurtosis; gamma = Euler-Mascheroni.",
    "Cash benchmark: $1,000 flat, Sharpe undefined (null).",
    "ETH price file has a 3-day gap at 2016-05-20, far outside all lookbacks; any missing day needed raises an abort ('missing data refused'). No funding gaps (all spacings within 1s of 8h); no error lines.",
]


if __name__ == "__main__":
    o = main()
    name = "e7_blind_result.json" if not ROUND_FUNDING_TIMES else "e7_blind_result_roundedtimes_variant.json"
    with open(os.path.join(HERE, name), "w") as f:
        json.dump(o, f, indent=2)
    print(json.dumps(o, indent=1))
