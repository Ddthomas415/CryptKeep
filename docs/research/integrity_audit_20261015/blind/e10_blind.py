"""E10 blind independent reimplementation (audit). Standard library only."""
import json, math, os, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
SYMS = "BTC ETH SOL DOGE LTC LINK AVAX ADA XRP DOT".split()
DAY = 86400


def d2t(s):
    return int(dt.datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=dt.timezone.utc).timestamp())


def t2d(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat()


def load_cb(sym):
    rows = json.load(open(os.path.join(HERE, "data", f"{sym}-USD.json")))
    return {int(r[0]): {"open": float(r[3]), "close": float(r[4])} for r in rows}


def load_d1(path):
    rows = json.load(open(os.path.join(HERE, path)))
    return {int(r[0]): {"open": float(r[1]), "close": float(r[4])} for r in rows}


def first_sunday_on_after(t):
    while dt.datetime.fromtimestamp(t, dt.timezone.utc).weekday() != 6:
        t += DAY
    return t


def eligible(c, t):
    return all((t - k * DAY) in c for k in range(61))


def signal(c, t):
    """Return (ret28, vol30) at close of day t (requires eligibility)."""
    closes = [c[t - k * DAY]["close"] for k in range(30, -1, -1)]  # 31 closes, oldest first
    rets = [closes[i] / closes[i - 1] - 1 for i in range(1, 31)]
    m = sum(rets) / 30
    sd = math.sqrt(sum((r - m) ** 2 for r in rets) / 30)
    vol = sd * math.sqrt(365)
    r28 = c[t]["close"] / c[t - 28 * DAY]["close"] - 1
    return r28, vol


def trend_weights(data, syms, t, vol_scale=True):
    el = [s for s in syms if eligible(data[s], t)]
    n = len(el)
    w = {}
    for s in el:
        r28, vol = signal(data[s], t)
        if r28 > 0:
            scale = min(1.0, 0.50 / vol) if (vol_scale and vol > 0) else 1.0
            w[s] = scale / n
        else:
            w[s] = 0.0
    return w, el


def simulate(data, syms, start, end, fee, slip, weight_fn, band=0.0):
    """weight_fn(t) -> dict sym->target weight for eligible syms (others target 0).
    Decisions at Sundays in [start, end]; executions next day open if <= end.
    Returns dict of metrics and NAV list."""
    cash = 1000.0
    qty = {s: 0.0 for s in syms}
    last_close = {}
    navs = []
    turnover_sum = 0.0
    pending = None
    t = start
    while t <= end:
        # execution at today's open
        if pending is not None:
            tw = pending
            pending = None
            tradable = [s for s in syms if t in data[s]]
            px = {s: data[s][t]["open"] for s in tradable}
            nav_tr = cash + sum(qty[s] * px[s] for s in tradable)
            sells, buys = {}, {}
            for s in tradable:
                cur = qty[s] * px[s]
                tgt = tw.get(s, 0.0) * nav_tr
                if band > 0 and qty[s] > 0 and tgt > 0 and abs(cur - tgt) / nav_tr < band:
                    continue
                d = tgt - cur
                if d < -1e-12:
                    sells[s] = -d / px[s]
                elif d > 1e-12:
                    buys[s] = d / px[s]
            traded = 0.0
            for s, q in sells.items():
                q = min(q, qty[s])
                notional = q * px[s] * (1 - slip)
                cash += notional * (1 - fee)
                qty[s] -= q
                traded += notional
            need = sum(q * px[s] * (1 + slip) * (1 + fee) for s, q in buys.items())
            scale = min(1.0, cash / need) if need > 0 else 1.0
            for s, q in buys.items():
                q *= scale
                notional = q * px[s] * (1 + slip)
                cash -= notional * (1 + fee)
                qty[s] += q
                traded += notional
            if cash < 0 and cash > -1e-9:
                cash = 0.0
            turnover_sum += traded / nav_tr
        # mark at close
        for s in syms:
            if t in data[s]:
                last_close[s] = data[s][t]["close"]
        nav = cash + sum(qty[s] * last_close[s] for s in syms if qty[s] != 0.0)
        if t == start:
            nav = 1000.0
        navs.append(nav)
        # decision
        if dt.datetime.fromtimestamp(t, dt.timezone.utc).weekday() == 6 and t + DAY <= end:
            pending = weight_fn(t)
        t += DAY
    return metrics(navs, turnover_sum, start, end)


def metrics(navs, turnover_sum, start, end):
    rets = [navs[i] / navs[i - 1] - 1 for i in range(1, len(navs))]
    m = sum(rets) / len(rets)
    sd = math.sqrt(sum((r - m) ** 2 for r in rets) / len(rets))
    sharpe = m / sd * math.sqrt(365) if sd > 0 else 0.0
    peak, mdd = -1, 0.0
    for v in navs:
        peak = max(peak, v)
        mdd = max(mdd, 1 - v / peak)
    years = (end - start) / DAY / 365
    return {"end_usd": round(navs[-1], 4), "sharpe": round(sharpe, 4),
            "max_drawdown_pct": round(mdd * 100, 3),
            "turnover": round(turnover_sum / years, 4),
            "days": len(navs), "_rets": rets}


def ew_fn(data, syms):
    def f(t):
        el = [s for s in syms if eligible(data[s], t)]
        return {s: 1.0 / len(el) for s in el} if el else {}
    return f


def trend_fn(data, syms, vol_scale=True):
    return lambda t: trend_weights(data, syms, t, vol_scale)[0]


def simulate_hold(data, sym, start, end, fee, slip):
    c = data[sym]
    navs, cash, q, last = [], 1000.0, 0.0, None
    t = start
    bought = False
    turnover = 0.0
    while t <= end:
        if not bought and t > start and t in c:
            px = c[t]["open"] * (1 + slip)
            q = cash / (px * (1 + fee))
            turnover += q * px / cash
            cash = 0.0
            bought = True
        if t in c:
            last = c[t]["close"]
        navs.append(1000.0 if t == start else cash + q * last)
        t += DAY
    return metrics(navs, turnover, start, end)


def strip(m):
    return {k: v for k, v in m.items() if not k.startswith("_")}


def main():
    data = {s: load_cb(s) for s in SYMS}
    periods = {
        "D": (first_sunday_on_after(d2t("2019-01-01")), d2t("2023-12-31")),
        "H": (first_sunday_on_after(d2t("2024-01-01")), d2t("2026-10-11")),
    }
    slip = 0.001
    out = {"periods": {k: [t2d(a), t2d(b)] for k, (a, b) in periods.items()}, "results": {}}
    for fee in (0.005, 0.009):
        fk = f"fee_{fee*100:.2f}pct"
        out["results"][fk] = {}
        for pk, (a, b) in periods.items():
            r = {
                "portfolio_core10": simulate(data, SYMS, a, b, fee, slip, trend_fn(data, SYMS)),
                "incumbent_btc_eth": simulate(data, ["BTC", "ETH"], a, b, fee, slip, trend_fn(data, ["BTC", "ETH"])),
                "hold_btc": simulate_hold(data, "BTC", a, b, fee, slip),
                "equal_weight_core": simulate(data, SYMS, a, b, fee, slip, ew_fn(data, SYMS)),
                "sens_band_0.05": simulate(data, SYMS, a, b, fee, slip, trend_fn(data, SYMS), band=0.05),
                "sens_no_vol_scaling": simulate(data, SYMS, a, b, fee, slip, trend_fn(data, SYMS, vol_scale=False)),
            }
            out["results"][fk][pk] = {k: strip(v) for k, v in r.items()}
    # PRIMARY
    checks = {}
    allpass = True
    for fk, per in out["results"].items():
        for pk, tol in (("D", 0.0), ("H", 0.05)):
            p, i = per[pk]["portfolio_core10"], per[pk]["incumbent_btc_eth"]
            s_ok = p["sharpe"] >= i["sharpe"] - tol
            d_ok = p["max_drawdown_pct"] <= i["max_drawdown_pct"] + 2.0
            checks[f"{fk}_{pk}"] = {"sharpe_ok": s_ok, "dd_ok": d_ok, "pass": s_ok and d_ok,
                                    "port_sharpe": p["sharpe"], "inc_sharpe": i["sharpe"],
                                    "port_mdd": p["max_drawdown_pct"], "inc_mdd": i["max_drawdown_pct"]}
            allpass &= s_ok and d_ok
    out["primary"] = {"checks": checks, "verdict": "PASS" if allpass else "FAIL"}
    # SECONDARY
    sec = {}
    fee = 0.005
    for s in SYMS:
        row = {}
        for pk, (a, b) in periods.items():
            t = a
            while t <= b and not eligible(data[s], t):
                t += 7 * DAY
            if t > b:
                row[pk] = None
                continue
            st = simulate(data, [s], t, b, fee, slip, lambda tt, s=s: trend_weights(data, [s], tt)[0])
            ho = simulate_hold(data, s, t, b, fee, slip)
            row[pk] = {"first_eligible_sunday": t2d(t), "days": st["days"],
                       "standalone": strip(st), "hold": strip(ho)}
        D, H = row["D"], row["H"]
        if D is None or D["days"] < 365 or H is None:
            cls = "INCONCLUSIVE"
        else:
            def better(x):
                return (x["standalone"]["sharpe"] >= x["hold"]["sharpe"] and
                        x["standalone"]["max_drawdown_pct"] < x["hold"]["max_drawdown_pct"])
            if better(D) and better(H):
                cls = "CANDIDATE"
            elif D["standalone"]["sharpe"] < D["hold"]["sharpe"] and H["standalone"]["sharpe"] < H["hold"]["sharpe"]:
                cls = "REJECTED_UNDER_TESTED_CONDITIONS"
            else:
                cls = "INCONCLUSIVE"
        row["classification"] = cls
        sec[s] = row
    out["secondary"] = sec
    # Simulator check on hash-checked majors files
    maj = {"BTC": load_d1("BTC-USD_d1.json"), "ETH": load_d1("ETH-USD_d1.json")}
    a, b = d2t("2020-01-05"), d2t("2026-10-08")
    sc = simulate(maj, ["BTC", "ETH"], a, b, 0.005, 0.0005, trend_fn(maj, ["BTC", "ETH"]))
    gaps = {k: [t2d(t) for t in range(a - 61 * DAY, b + 1, DAY) if t not in v] for k, v in maj.items()}
    out["simulator_check_majors"] = {"start": "2020-01-05", "end": "2026-10-08", "fee": 0.005, "slip": 0.0005,
                                     **strip(sc), "missing_days_in_window": gaps,
                                     "note": "reference harness not available; compare end_usd externally (tol 1e-6)"}
    out["choices"] = CHOICES
    json.dump(out, open(os.path.join(HERE, "e10_blind_result.json"), "w"), indent=1)
    return out


CHOICES = [
    "Eligibility at decision Sunday t: candles exist on t and each of the 60 prior calendar days (61 days incl. t). N = count of eligible symbols in the rule's universe at t.",
    "vol30 = population stdev of last 30 close-to-close simple returns (31 closes ending t) x sqrt(365); ret28 = close[t]/close[t-28]-1; weight = (1/N)*min(1,0.5/vol30) if ret28>0 else 0. Non-eligible symbols target 0.",
    "NAV series starts at $1000 at the first decision close (day 0) and is marked at every calendar-day close through the period end; a decision on the last day (end Sunday) is not executed (execution would fall after period end).",
    "Execution day: only symbols with a candle that day are tradable. Tradable sub-account NAV = cash + sum(qty*open) over tradable symbols; target value = weight*tradable NAV. Frozen (no candle) positions are neither traded nor counted in the sizing base, and are marked at last close in total NAV.",
    "A symbol eligible at the decision but missing its execution-day candle is frozen (target ignored). A tradable symbol that is not eligible (e.g. candles resumed <61 days ago) has target 0.",
    "Sells first: proceeds = q*open*(1-slip)*(1-fee). Buys: cost = q*open*(1+slip)*(1+fee); target delta computed at raw open; if total buy cost exceeds cash, all buys are scaled down proportionally (no leverage). Fee is on executed notional (q*open*(1+/-slip)).",
    "Turnover/yr = sum over executions of executed notional / tradable NAV at execution opens, divided by (end-start calendar days)/365.",
    "Sharpe = mean/pstdev of daily NAV returns x sqrt(365) (calendar days, incl. days with no trade); MDD = max peak-to-trough on daily NAV incl. day-0 $1000.",
    "Hold BTC / standalone hold: all cash into the symbol at the first execution open after the start Sunday (cost slip+fee), never sold; turnover counts that one buy.",
    "Equal-weight core: weight 1/N for each eligible core symbol at every Sunday decision, rebalanced to target at next open with the same costs (no band).",
    "Sensitivity band 0.05: skip a trade for a symbol that is held and has nonzero target when |current-target|/tradable NAV < 0.05; entries from 0 and exits to 0 always trade.",
    "Sensitivity no-vol-scaling: weight 1/N if ret28>0 else 0.",
    "Secondary: each symbol's first eligible Sunday within each period = first Sunday >= period start at which it is eligible (stepping weekly). Standalone N=1. Hold baseline starts the same Sunday. 'Fewer than 365 days of data in D' measured as NAV days from that Sunday to D end. CANDIDATE needs Sharpe>=hold AND MDD<hold MDD in both; REJECTED if Sharpe<hold in both; else INCONCLUSIVE.",
    "Simulator check: majors d1 files (columns ts,open,high,low,close,volume), incumbent rule, fee 0.50%, slip 0.05%, start 2020-01-05, end 2026-10-08 (last candle in those files). Only end_usd is reported; no reference curve available here.",
    "XRP: candles stop 2021-01-19, resume 2023-07-13; XRP 28d return was negative at the 2021-01-03/10/17 decisions, so no XRP was held into the gap and the frozen-position path is not exercised in D.",
    "Primary: per fee, D: port Sharpe >= inc Sharpe AND port MDD <= inc MDD + 2pts; H: port Sharpe >= inc Sharpe - 0.05 AND same MDD test. Comparisons made on rounded (4dp Sharpe, 3dp MDD) values.",
]

if __name__ == "__main__":
    o = main()
    for fk, per in o["results"].items():
        for pk, r in per.items():
            for k, v in r.items():
                print(fk, pk, k, v)
    print(json.dumps(o["primary"], indent=1))
    for s, r in o["secondary"].items():
        print(s, r["classification"], {p: (r[p]["first_eligible_sunday"], r[p]["standalone"]["sharpe"], r[p]["hold"]["sharpe"], r[p]["standalone"]["max_drawdown_pct"], r[p]["hold"]["max_drawdown_pct"], r[p]["days"]) if r[p] else None for p in ("D", "H")})
    print(o["simulator_check_majors"])
