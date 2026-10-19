"""Blind independent reimplementation of the BTC+ETH vol-scaled 28d momentum rule."""
import json, math, sys, os
from datetime import datetime, timezone, date

HERE = os.path.dirname(os.path.abspath(__file__))
FEE, SLIP = 0.005, 0.0005
DAY = 86400


def load(sym):
    rows = json.load(open(os.path.join(HERE, "data", f"{sym}-USD_d1.json")))
    rows.sort(key=lambda r: r[0])
    d = {}
    for r in rows:
        assert r[0] % DAY == 0, r
        d[r[0] // DAY] = dict(o=float(r[1]), h=float(r[2]), l=float(r[3]), c=float(r[4]))
    days = sorted(d)
    gaps = [(days[i - 1], days[i]) for i in range(1, len(days)) if days[i] - days[i - 1] != 1]
    dups = len(rows) - len(d)
    return d, days, gaps, dups


def dn(day):
    return datetime.fromtimestamp(day * DAY, timezone.utc).date()


def daynum(s):
    y, m, dd = map(int, s.split("-"))
    return (date(y, m, dd) - date(1970, 1, 1)).days


DATA = {}


def ann_vol(sym, t, logret):
    c = DATA[sym]
    rets = []
    for k in range(t - 29, t + 1):
        a, b = c[k - 1]["c"], c[k]["c"]
        rets.append(math.log(b / a) if logret else b / a - 1)
    m = sum(rets) / len(rets)
    return math.sqrt(sum((x - m) ** 2 for x in rets) / len(rets)) * math.sqrt(365)


def target(sym, t, logret):
    c = DATA[sym]
    r28 = c[t]["c"] / c[t - 28]["c"] - 1
    if r28 <= 0:
        return 0.0
    v = ann_vol(sym, t, logret)
    return 0.5 * min(1.0, 0.50 / v) if v > 0 else 0.5


def stats(nav):
    rets = [nav[i] / nav[i - 1] - 1 for i in range(1, len(nav))]
    m = sum(rets) / len(rets)
    sd = math.sqrt(sum((x - m) ** 2 for x in rets) / len(rets))
    sh = m / sd * math.sqrt(365) if sd > 0 else float("nan")
    pk, mdd = nav[0], 0.0
    for x in nav:
        pk = max(pk, x)
        mdd = min(mdd, x / pk - 1)
    return nav[-1], sh, mdd * 100


def run_rule(start, end, logret=False, cap_cash=False):
    syms = ["BTC", "ETH"]
    cash, qty = 1000.0, {s: 0.0 for s in syms}
    nav = []
    pending = None  # targets to execute at next open
    trades = events = 0
    for t in range(start, end + 1):
        if pending is not None:
            px = {s: DATA[s][t]["o"] for s in syms}
            V = cash + sum(qty[s] * px[s] for s in syms)
            events += 1
            # sells first, then buys
            order = sorted(syms, key=lambda s: pending[s] * V - qty[s] * px[s])
            for s in order:
                dv = pending[s] * V - qty[s] * px[s]
                if abs(dv) < 1e-9:
                    continue
                if dv < 0:
                    ep = px[s] * (1 - SLIP)
                    q = -dv / px[s]
                    cash += q * ep * (1 - FEE)
                    qty[s] -= q
                else:
                    ep = px[s] * (1 + SLIP)
                    q = dv / px[s]
                    cost = q * ep * (1 + FEE)
                    if cap_cash and cost > cash:
                        q = max(cash, 0) / (ep * (1 + FEE))
                        cost = q * ep * (1 + FEE)
                    cash -= cost
                    qty[s] += q
                trades += 1
            pending = None
        nav.append(cash + sum(qty[s] * DATA[s][t]["c"] for s in syms))
        if t < end and (t == start or dn(t).weekday() == 6):
            pending = {s: target(s, t, logret) for s in syms}
    return stats(nav), trades, events


def run_hold(start, end, buy_day_offset=0):
    t0 = start + buy_day_offset
    ep = DATA["BTC"][t0]["o"] * (1 + SLIP)
    q = 1000.0 / (ep * (1 + FEE))
    nav = [1000.0] if buy_day_offset == 0 else []
    for t in range(start, end + 1):
        nav.append(1000.0 if t < t0 else q * DATA["BTC"][t]["c"])
    return stats(nav), 1, 1


PERIODS = [("A", "2016-08-01", "2019-12-31"), ("B", "2020-01-01", "2023-12-31"),
           ("C", "2024-01-01", "2026-10-08")]


def main():
    for s in ["BTC", "ETH"]:
        d, days, gaps, dups = load(s)
        DATA[s] = d
        print(f"{s}: {len(days)} days {dn(days[0])}..{dn(days[-1])}, dups={dups}, gaps="
              + (", ".join(f"{dn(a)}->{dn(b)} ({b-a-1} missing)" for a, b in gaps) or "none"))
    for _, a, b in PERIODS:
        for s in DATA:
            miss = [dn(t) for t in range(daynum(a) - 31, daynum(b) + 1) if t not in DATA[s]]
            if miss:
                print(f"  {s} missing in/before window {a}: {miss[:10]}{'...' if len(miss)>10 else ''}")
    variants = [
        ("RULE main (simple-ret vol, cash may dip <0 by fees)", lambda a, b: run_rule(a, b)),
        ("RULE alt1 log-return vol", lambda a, b: run_rule(a, b, logret=True)),
        ("RULE alt2 buys capped at cash", lambda a, b: run_rule(a, b, cap_cash=True)),
        ("HOLD main (buy start-day open, NAV0=1000 pre-buy)", lambda a, b: run_hold(a, b, 0)),
        ("HOLD alt (buy day-2 open, like rule)", lambda a, b: run_hold(a, b, 1)),
    ]
    print(f"\n{'variant':52s} {'P':1s} {'end$':>10s} {'Sharpe':>7s} {'MDD%':>7s} {'trades':>6s} {'events':>6s}")
    for name, fn in variants:
        for p, a, b in PERIODS:
            (e, sh, mdd), tr, ev = fn(daynum(a), daynum(b))
            print(f"{name:52s} {p} {e:10.2f} {sh:7.3f} {mdd:7.2f} {tr:6d} {ev:6d}")


if __name__ == "__main__":
    main()
