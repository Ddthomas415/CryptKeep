#!/usr/bin/env python3
"""E8 blind independent reimplementation (stdlib only).
Spec: PREREGISTRATION.md in this directory. Run: python3 -I e8_blind.py
"""
import json, math, os, statistics, datetime as dt
from statistics import NormalDist

HERE = os.path.dirname(os.path.abspath(__file__))
DAY = 86400
SLIP = 0.0005
FEES = [0.005, 0.009]
ASSETS = ["BTC", "ETH"]
V_DSR = 0.0004636024000905694
GAMMA = 0.5772156649015329


def load(name):
    rows = json.load(open(os.path.join(HERE, "data", name)))
    return {int(r[0]) // DAY: (float(r[1]), float(r[4])) for r in rows}  # day -> (open, close)


DATA = {"BTC": load("BTC-USD_d1.json"), "ETH": load("ETH-USD_d1.json")}


def dnum(s):
    return int(dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp()) // DAY


def dstr(d):
    return dt.datetime.fromtimestamp(d * DAY, dt.timezone.utc).strftime("%Y-%m-%d")


def is_sunday(d):  # 1970-01-01 (day 0) was a Thursday
    return (d + 4) % 7 == 0


def close(a, d):
    v = DATA[a].get(d)
    return None if v is None else v[1]


def vol30(a, t):
    cs = [close(a, t - k) for k in range(30, -1, -1)]
    if any(c is None for c in cs):
        return None
    r = [cs[i + 1] / cs[i] - 1 for i in range(30)]
    return statistics.pstdev(r) * math.sqrt(365)


def volscale(a, t):
    v = vol30(a, t)
    if v is None:
        return None
    return 1.0 if v == 0 else min(1.0, 0.50 / v)


def w_incumbent(a, t):
    c, c0 = close(a, t), close(a, t - 28)
    if c is None or c0 is None:
        return 0.0
    if c / c0 - 1 > 0:
        s = volscale(a, t)
        return 0.0 if s is None else 0.5 * s
    return 0.0


def score(a, t):
    c = close(a, t)
    votes = []
    for L in (20, 50, 100, 200):
        c0 = close(a, t - L)
        if c0 is None:
            return None
        votes.append(1.0 if c > c0 else 0.0)
    return sum(votes) / 4.0


def w_composite(a, t, vol_scaling=True):
    s = score(a, t)
    if s is None:
        return 0.0
    if not vol_scaling:
        return 0.5 * s
    k = volscale(a, t)
    return 0.0 if k is None else 0.5 * s * k


def simulate(target_fn, start, end, fee, band=None, buy_and_hold_btc=False, label=""):
    """Daily NAV from start (first decision close, $1000 cash) to end inclusive."""
    buy_mult = (1 + SLIP) * (1 + fee) - 1
    sell_mult = 1 - (1 - SLIP) * (1 - fee)
    cash = 1000.0
    units = {a: 0.0 for a in ASSETS}
    nav = []
    pending = None  # targets decided at previous close
    turnover_sum = 0.0
    n_exec = 0
    held_once = False
    for d in range(start, end + 1):
        # --- execution at today's open ---
        if pending is not None:
            opens = {a: DATA[a][d][0] for a in ASSETS}
            V = cash + sum(units[a] * opens[a] for a in ASSETS)
            traded = pending  # dict asset -> target weight (only traded assets)
            untouched_val = sum(units[a] * opens[a] for a in ASSETS if a not in traded)

            def cost(E, scale=1.0):
                c = 0.0
                for a, w in traded.items():
                    delta = w * scale * E - units[a] * opens[a]
                    c += delta * buy_mult if delta >= 0 else -delta * sell_mult
                return c

            def solve(scale):
                lo, hi = 0.0, V
                for _ in range(200):
                    mid = (lo + hi) / 2
                    if mid + cost(mid, scale) > V:
                        hi = mid
                    else:
                        lo = mid
                return lo

            E = solve(1.0)
            scale = 1.0
            # guard: band can leave untouched sleeve so large that traded targets need cash < 0
            if untouched_val + sum(traded.values()) * E > E + 1e-12 and sum(traded.values()) > 0:
                lo_s, hi_s = 0.0, 1.0
                for _ in range(100):
                    m = (lo_s + hi_s) / 2
                    Em = solve(m)
                    if untouched_val + sum(traded.values()) * m * Em > Em:
                        hi_s = m
                    else:
                        lo_s = m
                scale = lo_s
                E = solve(scale)
                CLAMP_EVENTS.append(f"{label}:{dstr(d)}")
            notional = 0.0
            for a, w in traded.items():
                tv = w * scale * E
                notional += abs(tv - units[a] * opens[a])
                units[a] = tv / opens[a]
            cash = E - untouched_val - sum(units[a] * opens[a] for a in traded)
            if notional > 0:
                n_exec += 1
                turnover_sum += notional / V
            pending = None
        # --- mark at close ---
        closes = {a: DATA[a][d][1] for a in ASSETS}
        N = cash + sum(units[a] * closes[a] for a in ASSETS)
        nav.append(N)
        # --- decision at Sunday close (not executed on last day) ---
        if is_sunday(d) and d < end:
            if buy_and_hold_btc:
                if not held_once:
                    pending = {"BTC": 1.0}
                    held_once = True
            else:
                tgt = {a: target_fn(a, d) for a in ASSETS}
                if band is None:
                    pending = tgt
                else:
                    cur = {a: units[a] * closes[a] / N for a in ASSETS}
                    tr = {a: tgt[a] for a in ASSETS if abs(tgt[a] - cur[a]) >= band}
                    pending = tr if tr else None
    years = (len(nav) - 1) / 365.0
    rets = [nav[i] / nav[i - 1] - 1 for i in range(1, len(nav))]
    sd = statistics.pstdev(rets)
    sharpe = statistics.fmean(rets) / sd * math.sqrt(365) if sd > 0 else 0.0
    peak, mdd = -1, 0.0
    for x in nav:
        peak = max(peak, x)
        mdd = max(mdd, 1 - x / peak)
    return {
        "end_usd": round(nav[-1], 6),
        "sharpe": round(sharpe, 6),
        "max_drawdown_pct": round(mdd * 100, 6),
        "turnover_per_year": round(turnover_sum / years, 6),
        "rebalance_count": n_exec,
        "_nav": nav,
        "_rets": rets,
    }


CLAMP_EVENTS = []


def first_sunday_on_or_after(s):
    d = dnum(s)
    while not is_sunday(d):
        d += 1
    return d


PERIODS = {
    "D": (first_sunday_on_or_after("2017-01-01"), dnum("2023-12-31")),
    "H": (first_sunday_on_or_after("2024-01-01"), dnum("2026-10-08")),
}


def strip(r):
    return {k: v for k, v in r.items() if not k.startswith("_")}


def dsr(rets, N):
    n = len(rets)
    mu = statistics.fmean(rets)
    sd = statistics.pstdev(rets)
    sr = mu / sd
    skew = sum(((x - mu) / sd) ** 3 for x in rets) / n
    kurt = sum(((x - mu) / sd) ** 4 for x in rets) / n
    nd = NormalDist()
    sr0 = math.sqrt(V_DSR) * ((1 - GAMMA) * nd.inv_cdf(1 - 1 / N) + GAMMA * nd.inv_cdf(1 - 1 / (N * math.e)))
    z = (sr - sr0) * math.sqrt(n - 1) / math.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr ** 2)
    return {"N": N, "dsr": nd.cdf(z), "sr_daily": sr, "sr0_daily": sr0, "T": n, "skew": skew, "kurtosis": kurt}


def main():
    out = {"results": {}, "sensitivities": {}, "checks": {}}
    comp_rets_050 = []
    sim_check = {}
    for fee in FEES:
        fk = f"fee_{fee*100:.2f}pct"
        out["results"][fk] = {}
        out["sensitivities"][fk] = {}
        for p, (s, e) in PERIODS.items():
            comp = simulate(w_composite, s, e, fee, band=0.10, label=f"primary_{fk}_{p}")
            inc = simulate(w_incumbent, s, e, fee, band=None)
            inc_b0 = simulate(w_incumbent, s, e, fee, band=0.0)
            sim_check[f"{fk}_{p}"] = max(abs(a - b) for a, b in zip(inc["_nav"], inc_b0["_nav"]))
            hold = simulate(None, s, e, fee, buy_and_hold_btc=True)
            mix = simulate(lambda a, t: 0.25, s, e, fee, band=None)
            out["results"][fk][p] = {
                "period": [dstr(s), dstr(e)],
                "composite": strip(comp), "incumbent": strip(inc),
                "hold_btc": strip(hold), "mix_25_25_50": strip(mix),
                "cash": {"end_usd": 1000.0, "sharpe": 0.0, "max_drawdown_pct": 0.0, "turnover_per_year": 0.0, "rebalance_count": 0},
            }
            if fee == 0.005:
                comp_rets_050 += comp["_rets"]
            out["sensitivities"][fk][p] = {
                "band_0_ensemble_only": strip(simulate(w_composite, s, e, fee, band=0.0)),
                "band_0_20": strip(simulate(w_composite, s, e, fee, band=0.20, label=f"band020_{fk}_{p}")),
                "no_vol_scaling_band_0_10": strip(simulate(lambda a, t: w_composite(a, t, False), s, e, fee, band=0.10, label=f"novol_{fk}_{p}")),
            }
    # PASS checks
    checks, all_pass = {}, True
    for fk, R in out["results"].items():
        D, H = R["D"], R["H"]
        c1a = D["composite"]["sharpe"] >= D["incumbent"]["sharpe"]
        c1b = D["composite"]["turnover_per_year"] <= 0.75 * D["incumbent"]["turnover_per_year"]
        c2a = H["composite"]["sharpe"] >= H["incumbent"]["sharpe"] - 0.05
        c2b = H["composite"]["max_drawdown_pct"] <= H["incumbent"]["max_drawdown_pct"] + 2.0
        checks[fk] = {
            "D_sharpe_ge_incumbent": [c1a, D["composite"]["sharpe"], D["incumbent"]["sharpe"]],
            "D_turnover_le_0.75x": [c1b, D["composite"]["turnover_per_year"], 0.75 * D["incumbent"]["turnover_per_year"]],
            "H_sharpe_ge_incumbent_minus_0.05": [c2a, H["composite"]["sharpe"], H["incumbent"]["sharpe"] - 0.05],
            "H_mdd_le_incumbent_plus_2pp": [c2b, H["composite"]["max_drawdown_pct"], H["incumbent"]["max_drawdown_pct"] + 2.0],
        }
        all_pass = all_pass and c1a and c1b and c2a and c2b
    out["checks"]["pass_criteria"] = checks
    out["verdict"] = "PASS" if all_pass else "FAIL"
    out["checks"]["simulator_internal_check_max_abs_usd_diff_band0_vs_noband_incumbent"] = sim_check
    out["checks"]["simulator_check_vs_reviewed_harness"] = "NOT PERFORMED: reviewed harness curve not available in blind scope"
    out["checks"]["band_overallocation_clamp_events"] = CLAMP_EVENTS
    out["dsr_composite_DplusH_fee_0.50pct"] = [dsr(comp_rets_050, 15), dsr(comp_rets_050, 120)]
    out["shared_conventions_assumed"] = [
        "Incumbent: per asset w=0.5*min(1,0.50/vol30) if close[t]/close[t-28]-1>0 else 0 (auditor-supplied, shared with original code).",
        "vol30 = pstdev of 30 daily simple close-to-close returns ending at t * sqrt(365) (auditor-supplied).",
        "Execution at next open; post-cost equity E found by bisection s.t. E + cost = value available; buy cost delta*((1+slip)(1+fee)-1), sell cost -delta*(1-(1-slip)(1-fee)) (auditor-supplied).",
        "Current weight = asset value / NAV at decision close (auditor-supplied).",
        "Turnover = sum(traded notional / NAV at execution open, pre-cost) / period years (auditor-supplied).",
        "NAV $1000 cash at first decision close; marked every daily close to period end; decision on last day not executed; Sharpe = mean/pstdev daily returns*sqrt(365); MDD on daily NAV (auditor-supplied).",
        "Hold BTC 100% at open after first decision; 25/25/50 weekly; same timing/costs (auditor-supplied).",
        "DSR formula with V=0.0004636024000905694, per-day SR, ordinary (non-excess) kurtosis, population moments (auditor-supplied).",
    ]
    out["choices"] = [
        "Decision days = UTC calendar Sundays (row timestamp = UTC day start); execution at Monday's open.",
        "D = 2017-01-01 (a Sunday) .. 2023-12-31; H = 2024-01-07 .. 2026-10-08. H starts from fresh $1000 cash (not carried from D).",
        "Lookbacks are calendar days via date-keyed lookup (close L days earlier = close on day t-L). ETH file has a gap 2016-05-21..22; it is before every lookback used, so index vs calendar makes no difference here.",
        "Vote = 1 iff close[t] > close[t-L] strictly. ETH 200d lookback exists from 2016-12-04; all 4 lookbacks available for both assets at every decision, so no missing-vote rule was exercised (rule coded: missing -> weight 0).",
        "Composite target = 0.5*score*min(1,0.50/vol30) with the same vol30 as incumbent; vol30==0 treated as scale 1 (never occurs).",
        "Band: per asset, trade iff |target - current| >= band (inclusive, no epsilon); traded assets go fully to target weight * post-cost equity E; untouched assets keep units and their open value counts in E. If no asset passes the band, no execution that week.",
        "Band edge: an asset with target 0 but current weight < band is NOT forced out (literal rule). Initial entry needs target >= band.",
        "Band + sizing: costs only from traded assets; if untouched sleeve + traded targets would exceed E (cash<0, leverage), traded targets are scaled down until cash=0 (clamp events listed in checks).",
        "Rebalance count = executions with nonzero traded notional (incumbent/mix: weekly unless exactly zero change; hold BTC: 1).",
        "Turnover denominator NAV = pre-trade value at the execution open; period years = (number of daily NAV points - 1)/365.",
        "Sensitivities run at both fees and both periods: band 0 (ensemble+vol scaling, trade every week), band 0.20, and no vol scaling (0.5*score) with the primary 0.10 band.",
        "Composite DSR uses concatenated D and H daily return series (fee 0.50%), T = number of returns; D->H boundary return not included (separate periods).",
        "Cash benchmark reported as constant $1000 (no interest).",
    ]
    out["ambiguities_flagged"] = [
        "Prereg's 'simulator check' against the reviewed harness cannot be run blind; only an internal band=0 vs no-band equivalence check is reported.",
        "Band interaction with the shared sizing is unspecified in prereg (whether untouched assets' drift can force over-allocation); clamp rule chosen above.",
        "Prereg says 'close > close L days earlier' without saying calendar vs trading-row offset; crypto trades daily so identical here.",
        "Whether the no-vol-scaling sensitivity keeps the 0.10 band is not stated; assumed yes (only one ingredient changed).",
        "A target of exactly 0 inside the band leaves a small residual position, which conflicts with 'rest is cash' only in spirit; literal rule applied.",
        "Last data row is 2026-10-09; H ends 2026-10-08 as stated.",
    ]
    with open(os.path.join(HERE, "e8_blind_result.json"), "w") as f:
        json.dump(out, f, indent=1)
    return out


if __name__ == "__main__":
    o = main()
    for fk, R in o["results"].items():
        for p, r in R.items():
            for k in ("composite", "incumbent", "hold_btc", "mix_25_25_50"):
                print(fk, p, k, r[k])
    print(json.dumps(o["checks"], indent=1))
    print(o["verdict"])
    for fk, S in o["sensitivities"].items():
        for p, r in S.items():
            for k, v in r.items():
                print("SENS", fk, p, k, v)
    for x in o["dsr_composite_DplusH_fee_0.50pct"]:
        print("DSR", x)
