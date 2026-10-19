"""Research-only, no hindsight: does buying the top gainers work with SHORT holding periods?
Grid fixed before running: lookback L in {1h, 4h, 24h} x hold H in {1h, 4h, 12h, 24h}, top 3, plus a
take-profit/stop variant. Same data, eligibility, fills and costs as sim.py; prefix sums for speed.
Exits are evaluated on hourly closes only (no intrahour prices)."""
import json, os, sys, math, datetime as dt, statistics, hashlib
D, START_S, END_S = sys.argv[1], sys.argv[2], sys.argv[3]; H = 3600
P = lambda s: int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())
START, END = P(START_S), P(END_S)
T = list(range(START, END, H)); IDX = {t: i for i, t in enumerate(T)}; N = len(T)
close = {}; pv = {}; pp = {}
for f in sorted(os.listdir(f"{D}/h1")):
    rows = json.load(open(f"{D}/h1/{f}")); pid = f[:-5]
    if len(rows) < 24 * 14: continue
    c = [None] * N; v = [0.0] * N; p = [0] * N
    for ts, o, hi, lo, cl, vo in rows:
        i = IDX.get(ts)
        if i is None: continue
        c[i] = float(cl); v[i] = float(vo) * float(cl); p[i] = 1
    last = None
    for i in range(N):
        if c[i] is None: c[i] = last
        else: last = c[i]
    a = [0.0]; b = [0]
    for i in range(N): a.append(a[-1] + v[i]); b.append(b[-1] + p[i])
    close[pid] = c; pv[pid] = a; pp[pid] = b
PIDS = sorted(close)
def eligible(pid, i, min_usd=2e6):
    if i < 168 or close[pid][i - 168] is None: return False
    if pp[pid][i] - pp[pid][i - 168] < 0.9 * 168: return False
    return (pv[pid][i] - pv[pid][i - 168]) / 7 >= min_usd
def ret(pid, i, h):
    a = close[pid][i - h - 1] if i - h - 1 >= 0 else None; b = close[pid][i - 1]
    return None if not a or not b else b / a - 1
mark = lambda pid, i: close[pid][i - 1]
class Book:
    def __init__(s, fee, slip): s.cash = 1000.0; s.pos = {}; s.fee = fee / 1e4; s.slip = slip / 1e4; s.tr = []; s.eq = []
    def buy(s, pid, usd, i):
        if usd <= 1e-9: return
        q = (usd / (1 + s.fee)) / (mark(pid, i) * (1 + s.slip)); s.cash -= usd
        p = s.pos.setdefault(pid, {"q": 0.0, "cost": 0.0, "t": i}); p["q"] += q; p["cost"] += usd
    def sell(s, pid, i, why):
        p = s.pos.pop(pid); got = p["q"] * mark(pid, i) * (1 - s.slip) * (1 - s.fee); s.cash += got
        s.tr.append({"coin": pid, "in": T[p["t"]], "out": T[i], "pnl_pct": (got / p["cost"] - 1) * 100, "pnl_usd": got - p["cost"], "why": why})
    def value(s, i): return s.cash + sum(p["q"] * mark(pid, i) for pid, p in s.pos.items())
def ranked(i, L):
    out = []
    for p in PIDS:
        if eligible(p, i):
            r = ret(p, i, L)
            if r is not None: out.append((r, p))
    out.sort(reverse=True); return out
def rotation(L, Hh, K, fee, slip=10.0):
    b = Book(fee, slip)
    for i in range(169, N):
        if (i - 169) % Hh == 0:
            want = [p for r, p in ranked(i, L)[:K] if r > 0]
            for pid in list(b.pos):
                if pid not in want: b.sell(pid, i, "rotated_out")
            tgt = b.value(i) / K
            for pid in want:
                have = b.pos[pid]["q"] * mark(pid, i) if pid in b.pos else 0.0
                if have < tgt * 0.5: b.buy(pid, min(b.cash, tgt - have), i)
        b.eq.append((T[i], b.value(i)))
    return b
def tp_sl(L, tp, sl, max_h, K, fee, slip=10.0):
    b = Book(fee, slip)
    for i in range(169, N):
        for pid in list(b.pos):
            p = b.pos[pid]; g = mark(pid, i) * (1 - b.slip) * (1 - b.fee) * p["q"] / p["cost"] - 1
            if g >= tp: b.sell(pid, i, "take_profit")
            elif g <= -sl: b.sell(pid, i, "stop_loss")
            elif i - p["t"] >= max_h: b.sell(pid, i, "time_stop")
        if len(b.pos) < K:
            for r, pid in ranked(i, L):
                if len(b.pos) >= K or r <= 0: break
                if pid not in b.pos: b.buy(pid, min(b.cash, b.value(i) / K), i)
        b.eq.append((T[i], b.value(i)))
    return b
def stats(b):
    day = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).date()
    by = {}
    for t, v in b.eq: by[day(t)] = v
    days = sorted(by); prev = 1000.0; dr = []
    for d in days: dr.append(by[d] / prev - 1); prev = by[d]
    mo = {}
    for d, r in zip(days, dr): mo.setdefault(d.strftime("%Y-%m"), []).append(r)
    pk = None; mdd = 0
    for _, v in b.eq:
        if pk is None or v > pk: pk = v
        else: mdd = max(mdd, (pk - v) / pk)
    tr = b.tr; pc = [t["pnl_pct"] for t in tr]
    gross = [t["pnl_pct"] + 0 for t in tr]
    return {"final_usd": round(b.eq[-1][1], 2), "net_pct": round((b.eq[-1][1] / 1000 - 1) * 100, 2), "max_drawdown_pct": round(mdd * 100, 2),
            "trades": len(tr), "trades_per_day": round(len(tr) / len(days), 2), "win_rate_pct": round(100 * sum(1 for x in pc if x > 0) / len(pc), 1) if pc else None,
            "avg_trade_pct": round(statistics.mean(pc), 3) if pc else None, "median_trade_pct": round(statistics.median(pc), 3) if pc else None,
            "mean_daily_pct": round(statistics.mean(dr) * 100, 3), "positive_days_pct": round(100 * sum(1 for x in dr if x > 0) / len(dr), 1),
            "monthly_pct": {k: round((math.prod(1 + x for x in v) - 1) * 100, 2) for k, v in mo.items()},
            "exit_reasons": {w: sum(1 for t in tr if t["why"] == w) for w in sorted({t["why"] for t in tr})}}
RUNS = [(f"top3_by_{L}h_gain_hold_{Hh}h", (lambda L=L, Hh=Hh: (lambda f: rotation(L, Hh, 3, f)))()) for L in (1, 4, 24) for Hh in (1, 4, 12, 24)]
RUNS += [("top3_by_4h_gain_tp5_sl3_max24h", lambda f: tp_sl(4, 0.05, 0.03, 24, 3, f)),
         ("top3_by_24h_gain_tp10_sl5_max48h", lambda f: tp_sl(24, 0.10, 0.05, 48, 3, f))]
out = {"window": [START_S, END_S], "products": len(PIDS), "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "results": []}
for fee in (0.0, 10.0, 60.0):
    for name, fn in RUNS:
        out["results"].append({"strategy": name, "fee_bps_per_side": fee, **stats(fn(fee))})
        print(name, fee, file=sys.stderr, flush=True)
print(json.dumps(out, indent=1))
