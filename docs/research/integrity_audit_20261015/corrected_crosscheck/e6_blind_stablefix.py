#!/usr/bin/env python3
"""E6 blind reimplementation: weekly cross-sectional momentum on Coinbase USD coins.

Usage: python3 e6_blind.py <candles_dir> <out.json>
Python 3.10, stdlib only.
"""
import bisect
import datetime as dt
import json
import math
import os
import statistics
import sys

COST = 0.0075            # 0.50% fee + 0.25% slippage per side, on traded value
START_CASH = 1000.0
TOP_UNIVERSE = 20
TOP_HOLD = 5
LOOKBACK = 28
MIN_HISTORY = 90
VOL_WINDOW = 30
VOL_MIN_OBS = 20
EXCLUDED_BASES = {"USDC", "USDT", "DAI", "PYUSD", "EURC", "GUSD", "PAX", "USDS", "WBTC", "CBETH", "UST", "TUSD", "BUSD", "USDP", "FDUSD", "EURT", "GYEN", "USD1"}  # audit variant: original script list
DSR_V = 0.0004636024000905694
EULER_GAMMA = 0.5772156649015329

CHOICES = [
    "Day index = unix_ts // 86400 (UTC calendar day). A row's open is that day's 00:00 open, its close the next 00:00 close.",
    "Decision day d = a Sunday (UTC weekday of the candle's start date); decision uses close[d]; execution at open[d+1] (Monday).",
    "First decision = first Sunday on/after period start; decisions whose execution day falls after the period end are skipped.",
    "Only files named <BASE>-USD.json are used; files starting with '_' ignored. Excluded bases: exact match to the prereg list, plus any base containing 'USD'. 'PAXG' etc. are NOT excluded (exact match on 'PAX').",
    "Rows with open or close missing/non-numeric/<=0 are dropped. Missing/negative base volume treated as 0. Duplicate day rows: the last occurrence in the file wins.",
    "Data end L = last day present in any (non-excluded) product file. Period B and FULL end at L.",
    "Universe eligibility at d: first valid candle <= d-90 and a candle on d; median of close*base_volume over candles in [d-29, d], at least 20 such candles; top 20 by median (ties broken by product id).",
    "28-day return = close[d]/close[d-28]-1; universe members lacking a candle on d-28 are not rankable (strategy) but still count in the equal-weight benchmark.",
    "Strategy: top 5 by 28d return among those with return > 0, fixed 20% weight each, unfilled slots cash. Ties broken by product id.",
    "EW benchmark: 1/n weight on every universe member (n = universe size, may be < 20 early on), fully invested.",
    "Every execution day is a full rebalance to target weights (continuing holdings are trimmed/topped up to target, paying cost on that traded value).",
    "Costs: 0.75% of absolute traded value per trade, deducted from cash. Post-cost tradable NAV N' solved by fixed point N' = N_t - 0.0075*sum|w_i*N' - V_i| so cash never goes negative.",
    "Hold BTC: all cash into BTC-USD at the first execution day of the period (cost 0.75%), then held; never sold, no exit cost.",
    "No liquidation at period end: final NAV is marked to the last close without exit costs.",
    "NAV series: point 0 = $1000 at the first decision day's close (all cash), then one mark per calendar day at the close from the first execution day through period end. Held products with no candle on a day are marked at their most recent prior close.",
    "Periods A, B, FULL are independent runs each starting with $1000 (FULL is not a concatenation of A and B).",
    "Sharpe = mean/pstdev of daily NAV returns * sqrt(365); CAGR = (end/1000)^(365/days)-1 with days = number of daily returns; max drawdown reported as a negative percentage of peak NAV.",
    "AS_REGISTERED: product with no candle on the execution day trades at its most recent prior close (strictly before the exec day), for buys and sells, including after delisting.",
    "CORRECTED: 'frozen' = held product with no candle on exec day; it is not traded, stays held; target weights applied to tradable NAV = NAV - frozen value (at last close). A frozen product that is also in the new target keeps its current position (its target weight is not added as cash or redistributed). A target product with no candle on exec day is skipped and its weight stays cash.",
    "CORRECTED 'never trades again' = the product's last candle in the whole dataset is before L (dataset-wide, not per period). Sensitivities write such a held position down to 50% / 0% of its last close from the day after its last candle; trades are identical to PRIMARY (frozen value is excluded from tradable NAV either way).",
    "DSR (Bailey & Lopez de Prado 2014): SR0 = sqrt(V)*((1-g)*Z^-1(1-1/N) + g*Z^-1(1-1/(N*e))), g = Euler-Mascheroni; DSR = Z((SR-SR0)*sqrt(T-1)/sqrt(1 - skew*SR + (kurt-1)/4*SR^2)); SR = per-day mean/pstdev (non-annualised), skew = population skewness, kurt = population (non-excess, Pearson) kurtosis of the strategy's FULL daily returns, T = number of daily returns.",
    "Benchmark (c) not implemented (optional).",
    "Stale/frozen event counts: AS_REGISTERED counts trades executed at a stale (prior-close) price; CORRECTED counts frozen position-instances at execution, skipped buys, and held positions that never trade again (locked).",
]


def day_of(ts):
    return int(ts) // 86400


def iso(d):
    return (dt.date(1970, 1, 1) + dt.timedelta(days=d)).isoformat()


def to_day(s):
    return (dt.date.fromisoformat(s) - dt.date(1970, 1, 1)).days


def is_sunday(d):
    return (dt.date(1970, 1, 1) + dt.timedelta(days=d)).weekday() == 6


def fnum(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if math.isnan(v) or math.isinf(v):
        return None
    return v


class Product:
    def __init__(self, pid, rows):
        data = {}
        for r in rows:
            if not isinstance(r, (list, tuple)) or len(r) < 5:
                continue
            ts = fnum(r[0])
            o = fnum(r[3])
            c = fnum(r[4])
            if ts is None or o is None or c is None or o <= 0 or c <= 0:
                continue
            v = fnum(r[5]) if len(r) > 5 else None
            if v is None or v < 0:
                v = 0.0
            data[day_of(ts)] = (o, c, c * v)
        self.pid = pid
        self.data = data
        self.days = sorted(data)
        self.closes = [data[d][1] for d in self.days]
        self.first = self.days[0] if self.days else None
        self.last = self.days[-1] if self.days else None

    def has(self, d):
        return d in self.data

    def open(self, d):
        return self.data[d][0]

    def close(self, d):
        return self.data[d][1]

    def last_close_le(self, d):
        i = bisect.bisect_right(self.days, d) - 1
        return None if i < 0 else self.closes[i]

    def last_close_lt(self, d):
        return self.last_close_le(d - 1)


def load(candles_dir):
    prods = {}
    for fn in sorted(os.listdir(candles_dir)):
        if fn.startswith("_") or not fn.endswith(".json"):
            continue
        pid = fn[:-5]
        parts = pid.split("-")
        if len(parts) != 2 or parts[1] != "USD":
            continue
        base = parts[0]
        if base in EXCLUDED_BASES or "USD" in base:
            continue
        with open(os.path.join(candles_dir, fn)) as f:
            rows = json.load(f)
        p = Product(pid, rows)
        if p.days:
            prods[pid] = p
    return prods


def universe(prods, d):
    cands = []
    for pid, p in prods.items():
        if p.first is None or p.first > d - MIN_HISTORY or not p.has(d):
            continue
        vols = [p.data[x][2] for x in range(d - VOL_WINDOW + 1, d + 1) if x in p.data]
        if len(vols) < VOL_MIN_OBS:
            continue
        cands.append((-statistics.median(vols), pid))
    cands.sort()
    return [pid for _, pid in cands[:TOP_UNIVERSE]]


def strategy_targets(prods, d, uni):
    scored = []
    for pid in uni:
        p = prods[pid]
        if not p.has(d - LOOKBACK):
            continue
        r = p.close(d) / p.close(d - LOOKBACK) - 1.0
        if r > 0:
            scored.append((-r, pid))
    scored.sort()
    return {pid: 1.0 / TOP_HOLD for _, pid in scored[:TOP_HOLD]}


def ew_targets(uni):
    return {pid: 1.0 / len(uni) for pid in uni} if uni else {}


def simulate(prods, L, start, end, target_fn, mode, hold_once=False, writedown=None):
    """Return (nav list, events dict). target_fn(d) -> {pid: weight}."""
    d = start
    while not is_sunday(d):
        d += 1
    d0 = d
    decisions = {}
    while d + 1 <= end:
        decisions[d + 1] = d
        d += 7
        if hold_once:
            break
    if not decisions:
        return None, None
    first_exec = min(decisions)
    cash = START_CASH
    units = {}
    nav = [START_CASH]
    ev = {"stale_price_trades": 0, "frozen_at_execution": 0, "skipped_buys": 0, "locked_never_trade_again": 0}
    locked_seen = set()
    for t in range(first_exec, end + 1):
        if t in decisions:
            dd = decisions[t]
            targets = target_fn(dd)
            # execution prices and frozen set
            price = {}
            frozen = set()
            for pid in set(units) | set(targets):
                p = prods[pid]
                if p.has(t):
                    price[pid] = p.open(t)
                elif mode == "AS_REGISTERED":
                    lc = p.last_close_lt(t)
                    if lc is None:
                        continue  # never traded before: cannot price; skip
                    price[pid] = lc
                else:
                    if pid in units:
                        frozen.add(pid)
                        ev["frozen_at_execution"] += 1
                        if p.last < L and pid not in locked_seen and t > p.last:
                            locked_seen.add(pid)
                            ev["locked_never_trade_again"] += 1
                    else:
                        ev["skipped_buys"] += 1
            tradable = [pid for pid in units if pid not in frozen]
            vals = {pid: units[pid] * price[pid] for pid in tradable}
            w = {pid: wt for pid, wt in targets.items() if pid in price and pid not in frozen}
            n_t = cash + sum(vals.values())
            allp = set(vals) | set(w)
            n2 = n_t
            for _ in range(100):
                tc = COST * sum(abs(w.get(pid, 0.0) * n2 - vals.get(pid, 0.0)) for pid in allp)
                new = n_t - tc
                if abs(new - n2) < 1e-12:
                    n2 = new
                    break
                n2 = new
            for pid in allp:
                tv = w.get(pid, 0.0) * n2
                if mode == "AS_REGISTERED" and not prods[pid].has(t) and abs(tv - vals.get(pid, 0.0)) > 1e-9:
                    ev["stale_price_trades"] += 1
                if tv > 1e-12:
                    units[pid] = tv / price[pid]
                else:
                    units.pop(pid, None)
            cash = n2 * (1.0 - sum(w.values()))
            if cash < 0 and cash > -1e-9:
                cash = 0.0
        # mark at close
        v = cash
        for pid, u in units.items():
            p = prods[pid]
            c = p.close(t) if p.has(t) else p.last_close_le(t)
            if writedown is not None and p.last < L and t > p.last:
                c *= writedown
            v += u * c
        nav.append(v)
    return nav, ev


def stats(nav):
    rets = [nav[i] / nav[i - 1] - 1.0 for i in range(1, len(nav))]
    days = len(rets)
    end = nav[-1]
    cagr = (end / START_CASH) ** (365.0 / days) - 1.0 if end > 0 else -1.0
    sd = statistics.pstdev(rets)
    sharpe = statistics.fmean(rets) / sd * math.sqrt(365) if sd > 0 else 0.0
    peak, mdd = nav[0], 0.0
    for x in nav:
        peak = max(peak, x)
        mdd = min(mdd, x / peak - 1.0)
    return {"end_usd": round(end, 4), "cagr_pct": round(cagr * 100, 4), "sharpe": round(sharpe, 4),
            "max_drawdown_pct": round(mdd * 100, 4), "days": days}, rets


def dsr(rets, N, V=DSR_V):
    nd = statistics.NormalDist()
    T = len(rets)
    m = statistics.fmean(rets)
    m2 = sum((r - m) ** 2 for r in rets) / T
    m3 = sum((r - m) ** 3 for r in rets) / T
    m4 = sum((r - m) ** 4 for r in rets) / T
    sr = m / math.sqrt(m2)
    skew = m3 / m2 ** 1.5
    kurt = m4 / m2 ** 2
    sr0 = math.sqrt(V) * ((1 - EULER_GAMMA) * nd.inv_cdf(1 - 1.0 / N)
                          + EULER_GAMMA * nd.inv_cdf(1 - 1.0 / (N * math.e)))
    den = 1 - skew * sr + (kurt - 1) / 4.0 * sr * sr
    z = (sr - sr0) * math.sqrt(T - 1) / math.sqrt(den)
    return {"N": N, "dsr": round(nd.cdf(z), 6), "sr_daily": round(sr, 6), "sr0_daily": round(sr0, 6),
            "skew": round(skew, 6), "kurtosis_pearson": round(kurt, 6), "T": T, "z": round(z, 6)}


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    prods = load(sys.argv[1])
    if "BTC-USD" not in prods:
        sys.exit("BTC-USD.json missing")
    L = max(p.last for p in prods.values())
    periods = {"A": (to_day("2018-01-01"), to_day("2021-12-31")),
               "B": (to_day("2022-01-01"), L),
               "FULL": (to_day("2018-01-01"), L)}
    ucache = {}

    def uni(d):
        if d not in ucache:
            ucache[d] = universe(prods, d)
        return ucache[d]

    strat_fn = lambda d: strategy_targets(prods, d, uni(d))
    ew_fn = lambda d: ew_targets(uni(d))
    btc_fn = lambda d: {"BTC-USD": 1.0}

    out = {"script": "e6_blind.py", "data": {"products_used": len(prods), "data_end": iso(L),
           "periods": {k: [iso(a), iso(b)] for k, (a, b) in periods.items()}},
           "choices": CHOICES, "modes": {}}
    for mode in ("AS_REGISTERED", "CORRECTED"):
        mres = {"periods": {}, "events": {}}
        full_rets = None
        sens = {"writedown_50": {}, "writedown_0": {}}
        for pname, (a, b) in periods.items():
            row = {}
            for name, fn, once in (("strategy", strat_fn, False), ("hold_btc", btc_fn, True), ("ew_universe", ew_fn, False)):
                nav, ev = simulate(prods, L, a, b, fn, mode, hold_once=once)
                st, rets = stats(nav)
                row[name] = st
                mres["events"][f"{pname}.{name}"] = ev
                if pname == "FULL" and name == "strategy":
                    full_rets = rets
                if mode == "CORRECTED" and name != "hold_btc":
                    for key, f in (("writedown_50", 0.5), ("writedown_0", 0.0)):
                        nav2, _ = simulate(prods, L, a, b, fn, mode, hold_once=once, writedown=f)
                        sens[key].setdefault(pname, {})[name] = stats(nav2)[0]
            mres["periods"][pname] = row
        P = mres["periods"]
        c1 = P["A"]["strategy"]["cagr_pct"] > 0 and P["B"]["strategy"]["cagr_pct"] > 0
        c2 = all(P[k]["strategy"]["sharpe"] > P[k]["hold_btc"]["sharpe"] for k in ("A", "B"))
        c3 = all(P[k]["strategy"]["sharpe"] > P[k]["ew_universe"]["sharpe"] for k in ("A", "B"))
        d = {f"N{n}": dsr(full_rets, n) for n in (4, 15, 120, 576)}
        c4 = d["N15"]["dsr"] >= 0.90
        mres["pass"] = {"1_positive_cagr_A_and_B": c1, "2_sharpe_gt_btc_A_and_B": c2,
                        "3_sharpe_gt_ew_A_and_B": c3, "4_dsr_full_N15_ge_0.90": c4,
                        "checks_1_to_3": c1 and c2 and c3, "overall": c1 and c2 and c3 and c4}
        mres["dsr_full"] = d
        if mode == "CORRECTED":
            mres["sensitivities_delisted_writedown"] = sens
        out["modes"][mode] = mres
    with open(sys.argv[2], "w") as f:
        json.dump(out, f, indent=2)
    print(json.dumps({m: {"pass": v["pass"], "FULL": v["periods"]["FULL"]} for m, v in out["modes"].items()}, indent=1))


if __name__ == "__main__":
    main()
