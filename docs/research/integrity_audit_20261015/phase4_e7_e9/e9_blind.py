"""E9 blind independent reimplementation (stdlib only).
Spec: PREREGISTRATION.md + auditor-supplied shared conventions. See CHOICES below."""
import json, math, os, datetime as dt, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
SLIP = 0.0005
FEES = [0.005, 0.009]
DAY = 86400


def load(sym):
    rows = json.load(open(os.path.join(HERE, "data", f"{sym}-USD_d1.json")))
    return {int(r[0]): (float(r[1]), float(r[4])) for r in rows}  # ts -> (open, close)


BTC, ETH = load("BTC"), load("ETH")
ASSETS = ["BTC", "ETH"]
PX = {"BTC": BTC, "ETH": ETH}


def ts_of(y, m, d):
    return int(dt.datetime(y, m, d, tzinfo=dt.timezone.utc).timestamp())


def first_sunday_on_or_after(ts):
    while dt.datetime.fromtimestamp(ts, dt.timezone.utc).weekday() != 6:
        ts += DAY
    return ts


def is_sunday(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).weekday() == 6


def close(a, ts):
    return PX[a][ts][1]


def opn(a, ts):
    return PX[a][ts][0]


def candidate_weight(a, t):
    c = lambda k: close(a, t - k * DAY)
    mom = c(0) / c(28) - 1
    if not mom > 0:
        return 0.0
    rets = [c(k) / c(k + 1) - 1 for k in range(30)]  # 30 returns ending at t
    vol = st.pstdev(rets) * math.sqrt(365)
    return 0.5 * min(1.0, 0.50 / vol)


def cost_of(delta, fee):
    if delta >= 0:
        return delta * ((1 + SLIP) * (1 + fee) - 1)
    return -delta * (1 - (1 - SLIP) * (1 - fee))


def execute(units, cash, targets, traded, t_open, fee, nolev=False):
    """units: dict asset->units; targets: asset->weight; traded: assets to trade.
    Untouched assets keep units. Traded assets are set to w*E where E is the
    post-cost total equity, solved by bisection: E + sum(cost) = V (value at open)."""
    prices = {a: opn(a, t_open) for a in ASSETS}
    held = {a: units[a] * prices[a] for a in ASSETS}
    V = cash + sum(held.values())

    U = sum(held[a] for a in ASSETS if a not in traded)

    def tvals(E):
        tv = {a: targets[a] * E for a in traded}
        if nolev:
            s = sum(tv.values())
            room = max(0.0, E - U)
            if s > room:
                tv = {a: v * room / s for a, v in tv.items()}
        return tv

    def total_cost(E):
        tv = tvals(E)
        return sum(cost_of(tv[a] - held[a], fee) for a in traded)

    lo, hi = 0.0, V * 1.5 + 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if mid + total_cost(mid) > V:
            hi = mid
        else:
            lo = mid
    E = (lo + hi) / 2
    notional = 0.0
    c_tot = 0.0
    new_units = dict(units)
    TV = tvals(E)
    for a in traded:
        tv = TV[a]
        d = tv - held[a]
        notional += abs(d)
        c_tot += cost_of(d, fee)
        new_units[a] = tv / prices[a]
    new_cash = cash - sum(TV[a] - held[a] for a in traded) - c_tot
    return new_units, new_cash, notional / V if V > 0 else 0.0


def run(strategy, start, end, fee, band=None, nolev=False):
    """strategy: 'cand' | 'hold_btc' | 'mix'. Returns metrics dict."""
    units = {a: 0.0 for a in ASSETS}
    cash = 1000.0
    nav = []
    turnover_sum = 0.0
    n_exec = 0
    min_cash = cash
    first_decision_done = False
    t = start
    pending = None  # (targets, traded) to execute at today's open
    while t <= end:
        if pending is not None:
            targets, traded = pending
            if traded:
                units, cash, to = execute(units, cash, targets, traded, t, fee, nolev)
                if to > 0:
                    turnover_sum += to
                    n_exec += 1
                min_cash = min(min_cash, cash)
            pending = None
        nav_t = cash + sum(units[a] * close(a, t) for a in ASSETS)
        nav.append(nav_t)
        if is_sunday(t) and t < end:
            if strategy == "cand":
                targets = {a: candidate_weight(a, t) for a in ASSETS}
                if band is None:
                    traded = list(ASSETS)
                else:
                    cur = {a: units[a] * close(a, t) / nav_t for a in ASSETS}
                    traded = [a for a in ASSETS if abs(targets[a] - cur[a]) >= band]
                pending = (targets, traded)
            elif strategy == "mix":
                pending = ({"BTC": 0.25, "ETH": 0.25}, list(ASSETS))
            elif strategy == "hold_btc":
                if not first_decision_done:
                    pending = ({"BTC": 1.0, "ETH": 0.0}, ["BTC"])
            first_decision_done = True
        t += DAY
    years = (end - start) / DAY / 365.0
    rets = [nav[i] / nav[i - 1] - 1 for i in range(1, len(nav))]
    sd = st.pstdev(rets)
    sharpe = st.mean(rets) / sd * math.sqrt(365) if sd > 0 else 0.0
    peak, mdd = nav[0], 0.0
    for v in nav:
        peak = max(peak, v)
        mdd = max(mdd, 1 - v / peak)
    return {
        "end_usd": round(nav[-1], 4),
        "sharpe": round(sharpe, 4),
        "max_drawdown_pct": round(mdd * 100, 4),
        "turnover_per_year": round(turnover_sum / years, 4),
        "rebalance_executions_per_year": round(n_exec / years, 4),
        "rebalance_executions_total": n_exec,
        "min_cash_usd": round(min_cash, 4),
        "nav_points": len(nav),
    }


PERIODS = {
    "D": (first_sunday_on_or_after(ts_of(2017, 1, 1)), ts_of(2023, 12, 31)),
    "H": (first_sunday_on_or_after(ts_of(2024, 1, 1)), ts_of(2026, 10, 8)),
}


def main():
    out = {"results": {}, "pass_checks": {}, "sensitivities": {}}
    for fee in FEES:
        fk = f"fee_{fee*100:.2f}pct"
        out["results"][fk] = {}
        for p, (s, e) in PERIODS.items():
            out["results"][fk][p] = {
                "period": [dt.datetime.fromtimestamp(s, dt.timezone.utc).date().isoformat(),
                           dt.datetime.fromtimestamp(e, dt.timezone.utc).date().isoformat()],
                "banded_0.10": run("cand", s, e, fee, 0.10),
                "incumbent_no_band": run("cand", s, e, fee, None),
                "hold_btc": run("hold_btc", s, e, fee),
                "mix_25_25_50": run("mix", s, e, fee),
            }
            out["sensitivities"].setdefault(fk, {})[p] = {
                "band_0.05": run("cand", s, e, fee, 0.05),
                "band_0.20": run("cand", s, e, fee, 0.20),
                "ALT_banded_0.10_no_leverage_cap": run("cand", s, e, fee, 0.10, True),
            }
        R = out["results"][fk]
        b, i = R["D"]["banded_0.10"], R["D"]["incumbent_no_band"]
        c1a = b["sharpe"] >= i["sharpe"]
        c1b = b["turnover_per_year"] <= 0.75 * i["turnover_per_year"]
        bh, ih = R["H"]["banded_0.10"], R["H"]["incumbent_no_band"]
        c2a = bh["sharpe"] >= ih["sharpe"] - 0.05
        c2b = bh["max_drawdown_pct"] <= ih["max_drawdown_pct"] + 2.0
        out["pass_checks"][fk] = {
            "D_sharpe_banded_ge_incumbent": [b["sharpe"], i["sharpe"], c1a],
            "D_turnover_banded_le_0.75x_incumbent": [b["turnover_per_year"], round(0.75 * i["turnover_per_year"], 4), c1b],
            "H_sharpe_banded_ge_incumbent_minus_0.05": [bh["sharpe"], round(ih["sharpe"] - 0.05, 4), c2a],
            "H_maxdd_banded_le_incumbent_plus_2pp": [bh["max_drawdown_pct"], round(ih["max_drawdown_pct"] + 2, 4), c2b],
            "all": c1a and c1b and c2a and c2b,
        }
    out["verdict"] = "PASS" if all(v["all"] for v in out["pass_checks"].values()) else "FAIL"
    out["shared_assumptions_from_auditor"] = [
        "Candidate weight 0.5*min(1,0.50/vol30) if close[t]/close[t-28]-1>0 else 0; vol30 = pstdev of 30 daily simple close returns ending at t * sqrt(365).",
        "Execution at next day's open; post-cost equity E by bisection s.t. E + sum(cost) = value at open; buy cost delta*((1+s)(1+f)-1), sell cost -delta*(1-(1-s)(1-f)).",
        "Band current weight = asset value / NAV at decision close.",
        "Turnover = sum(traded notional / NAV at execution) / period years.",
        "NAV: $1000 cash at first decision close; daily close marks through period end; decision on last day not executed; Sharpe = mean/pstdev daily returns * sqrt(365); MDD on daily NAV.",
        "Hold BTC: 100% BTC at open after first decision, same costs. 25/25/50 rebalanced weekly at every decision, same costs.",
    ]
    out["choices"] = [
        "Decision days = UTC Sundays (weekday of day-start timestamp); D = 2017-01-01..2023-12-31 (both Sundays; 2023-12-31 decision not executed); H = 2024-01-07..2026-10-08.",
        "Period length in years = (end - start) days / 365.",
        "Band test |target - current| >= band, inclusive, exact float comparison (no tolerance).",
        "Band applied per asset; exits to 0 and entries from 0 obey the band (a holding <band with target 0 is left untouched; a new target <band from 0 is not entered).",
        "Band x sizing: only assets passing the band are traded; untouched assets keep units; traded assets are set to target_weight * E where E is the post-cost TOTAL portfolio equity (including untouched holdings), solved by the same bisection over traded assets only. Remainder is cash.",
        "PRIMARY: cash is not floored: if untouched holdings + traded targets exceed E, cash goes negative (leverage); min_cash_usd is reported per run to show whether this ever happens.",
        "Incumbent: every decision trades both assets to w*E (even tiny deltas, which incur cost); an execution is counted when traded notional > 0 (so all-zero-target weeks with no holdings are not counted).",
        "Turnover NAV denominator = pre-trade portfolio value at the execution open.",
        "Hold BTC counts 1 execution; its ETH target is not traded.",
        "Bad lows in data (BTC 2017-04-15 low 0.06, ETH 2017-06-21 low 0.10) are irrelevant: only open and close are used.",
        "ALT (not prereg, reported under sensitivities): traded targets scaled down so cash >= 0 (no leverage); reported to show whether the verdict depends on the leverage interpretation.",
        "Cash benchmark ($1000 flat, Sharpe undefined/0) not simulated.",
    ]
    out["flags"] = [
        "Prereg says 'A target of 0 is always >= 0.10 away from any holding of 0.10 or more' - true only for the inclusive boundary used here; it implies holdings below 0.10 can persist (dust) when the target goes to 0.",
        "Prereg does not specify whether band-traded assets size to total equity or to the traded sub-portfolio; total equity chosen.",
        "Prereg 'turnover' undefined in prereg itself; auditor convention used.",
        "H is not a true holdout for the signal (stated in prereg).",
        "With the band, the untouched weight may sit up to band away from target, so total gross weight can exceed 1.0 in principle; see min_cash_usd.",
    ]
    json.dump(out, open(os.path.join(HERE, "e9_blind_result.json"), "w"), indent=2)
    print(json.dumps({k: out[k] for k in ("pass_checks", "verdict")}, indent=1))
    for fk, R in out["results"].items():
        for p, r in R.items():
            for k, v in r.items():
                if k != "period":
                    print(fk, p, k, v["end_usd"], v["sharpe"], v["max_drawdown_pct"], v["turnover_per_year"], v["rebalance_executions_per_year"], v["min_cash_usd"])
        for p, r in out["sensitivities"][fk].items():
            for k, v in r.items():
                print(fk, p, k, v["end_usd"], v["sharpe"], v["max_drawdown_pct"], v["turnover_per_year"], v["rebalance_executions_per_year"], v["min_cash_usd"])


if __name__ == "__main__":
    main()
