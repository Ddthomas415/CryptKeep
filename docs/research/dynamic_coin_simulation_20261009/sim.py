"""Research-only, no hindsight: dynamic-universe strategies on Coinbase hourly data.
Every decision at hour t uses only candles with open time < t (closed by t). Fills at the close of the
last completed hour (price known at decision time) plus slippage, with a fee per side. Start cash 1,000 USD.
Rules were fixed before the first run and are reported in full, including the losing ones."""
import json, os, sys, math, datetime as dt, statistics, hashlib
D = sys.argv[1]; H = 3600
END = int(dt.datetime(2026, 10, 9, tzinfo=dt.timezone.utc).timestamp()); START = END - 60 * 86400
T = list(range(START, END, H)); IDX = {t: i for i, t in enumerate(T)}; N = len(T)
close = {}; vol_usd = {}; high = {}; present = {}
for f in sorted(os.listdir(f"{D}/h1")):
    rows = json.load(open(f"{D}/h1/{f}")); pid = f[:-5]
    if len(rows) < 24 * 14: continue
    c = [None] * N; v = [0.0] * N; h = [None] * N; p = [False] * N
    for ts, o, hi, lo, cl, vo in rows:
        i = IDX.get(ts)
        if i is None: continue
        c[i] = float(cl); v[i] = float(vo) * float(cl); h[i] = float(hi); p[i] = True
    last = None
    for i in range(N):
        if c[i] is None: c[i] = last; h[i] = last
        else: last = c[i]
    close[pid] = c; vol_usd[pid] = v; high[pid] = h; present[pid] = p
PIDS = sorted(close)
def eligible(pid, i, min_daily_usd=2e6):
    """At decision index i (using hours < i): 7 full days of history, >=90% hours traded, avg daily USD volume >= min."""
    if i < 7 * 24 or close[pid][i - 7 * 24] is None: return False
    w = range(i - 7 * 24, i)
    if sum(present[pid][j] for j in w) < 0.9 * 7 * 24: return False
    return sum(vol_usd[pid][j] for j in w) / 7 >= min_daily_usd
def ret(pid, i, hours):
    a = close[pid][i - hours]; b = close[pid][i - 1]
    return None if not a or not b else b / a - 1
def mark(pid, i): return close[pid][i - 1]
class Book:
    def __init__(s, fee_bps, slip_bps): s.cash = 1000.0; s.pos = {}; s.fee = fee_bps / 1e4; s.slip = slip_bps / 1e4; s.trades = []; s.eq = []
    def buy(s, pid, usd, i, why):
        if usd <= 1e-9: return
        px = mark(pid, i) * (1 + s.slip); cost = usd; q = (cost / (1 + s.fee)) / px
        s.cash -= cost; p = s.pos.setdefault(pid, {"q": 0.0, "cost": 0.0, "t": T[i], "peak": mark(pid, i)}); p["q"] += q; p["cost"] += cost
    def sell(s, pid, i, why, frac=1.0):
        p = s.pos[pid]; q = p["q"] * frac; px = mark(pid, i) * (1 - s.slip); got = q * px * (1 - s.fee)
        s.cash += got; cost = p["cost"] * frac
        s.trades.append({"coin": pid, "entry": T[i] if False else p["t"], "exit": T[i], "pnl_usd": got - cost, "pnl_pct": (got / cost - 1) * 100, "why": why})
        p["q"] -= q; p["cost"] -= cost
        if p["q"] <= 1e-15 or frac >= 0.999999: del s.pos[pid]
    def value(s, i): return s.cash + sum(p["q"] * mark(pid, i) for pid, p in s.pos.items())
def rotation(lookback_h, top_k, rebalance_h, fee, slip=10.0, min_usd=2e6):
    b = Book(fee, slip)
    for i in range(N):
        if i >= 7 * 24 and (i - 7 * 24) % rebalance_h == 0:
            ranked = sorted(((ret(p, i, lookback_h), p) for p in PIDS if eligible(p, i, min_usd) and ret(p, i, lookback_h) is not None), reverse=True)
            want = [p for r, p in ranked[:top_k] if r > 0]
            for pid in list(b.pos):
                if pid not in want: b.sell(pid, i, "rotated_out")
            target = b.value(i) / top_k
            for pid in want:
                have = b.pos[pid]["q"] * mark(pid, i) if pid in b.pos else 0.0
                if have < target * 0.5: b.buy(pid, min(b.cash, target - have), i, "rotated_in")
        if i >= 7 * 24: b.eq.append((T[i], b.value(i)))
    return b
def breakout(trail, max_hold_h, slots, fee, slip=10.0, vol_mult=3.0, min_usd=2e6):
    b = Book(fee, slip)
    for i in range(7 * 24 + 1, N):
        for pid in list(b.pos):
            p = b.pos[pid]; px = mark(pid, i); p["peak"] = max(p["peak"], px)
            if px <= p["peak"] * (1 - trail): b.sell(pid, i, "trailing_stop")
            elif T[i] - p["t"] >= max_hold_h * H: b.sell(pid, i, "time_stop")
        if len(b.pos) < slots:
            cands = []
            for pid in PIDS:
                if pid in b.pos or not eligible(pid, i, min_usd): continue
                prior_high = max(x for x in high[pid][i - 1 - 7 * 24: i - 1] if x is not None)
                if mark(pid, i) <= prior_high: continue
                v24 = sum(vol_usd[pid][i - 24: i]); v7 = sum(vol_usd[pid][i - 7 * 24: i - 24]) / 6
                if v7 > 0 and v24 >= vol_mult * v7: cands.append((v24 / v7, pid))
            for _, pid in sorted(cands, reverse=True)[: slots - len(b.pos)]:
                b.buy(pid, min(b.cash, b.value(i) / slots), i, "breakout")
        b.eq.append((T[i], b.value(i)))
    return b
def hold(pid, fee, slip=10.0):
    b = Book(fee, slip); b.buy(pid, 1000.0, 7 * 24, "hold")
    for i in range(7 * 24, N): b.eq.append((T[i], b.value(i)))
    return b
def stats(b):
    eq = b.eq; day = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).date()
    by = {}
    for t, v in eq: by[day(t)] = v
    days = sorted(by); prev = 1000.0; dr = []
    for d in days: dr.append(by[d] / prev - 1); prev = by[d]
    wk = {}; mo = {}
    for d, r in zip(days, dr): wk.setdefault(d.isocalendar()[:2], []).append(r); mo.setdefault(d.strftime("%Y-%m"), []).append(r)
    comp = lambda v: math.prod(1 + x for x in v) - 1
    pk = None; mdd = 0
    for _, v in eq:
        if pk is None or v > pk: pk = v
        else: mdd = max(mdd, (pk - v) / pk)
    tr = b.trades; w = [t for t in tr if t["pnl_usd"] > 0]
    top = sorted(tr, key=lambda t: -t["pnl_usd"])[:5]
    fmt = lambda t: dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%m-%d %H:%M")
    return {"start": str(days[0]), "end": str(days[-1]), "days": len(days), "final_usd": round(eq[-1][1], 2), "net_pct": round((eq[-1][1] / 1000 - 1) * 100, 2),
            "max_drawdown_pct": round(mdd * 100, 2), "closed_trades": len(tr), "win_rate_pct": round(100 * len(w) / len(tr), 1) if tr else None,
            "avg_trade_pct": round(statistics.mean(t["pnl_pct"] for t in tr), 2) if tr else None,
            "mean_daily_pct": round(statistics.mean(dr) * 100, 3), "median_daily_pct": round(statistics.median(dr) * 100, 3),
            "positive_days_pct": round(100 * sum(1 for x in dr if x > 0) / len(dr), 1), "best_day_pct": round(max(dr) * 100, 2), "worst_day_pct": round(min(dr) * 100, 2),
            "weekly_pct": {f"{k[0]}-W{k[1]:02d}": round(comp(v) * 100, 2) for k, v in wk.items()},
            "monthly_pct": {k: round(comp(v) * 100, 2) for k, v in mo.items()},
            "daily_usd_end": {str(d): round(by[d], 2) for d in days},
            "best_trades": [{"coin": t["coin"], "in": fmt(t["entry"]), "out": fmt(t["exit"]), "pnl_usd": round(t["pnl_usd"], 2), "pnl_pct": round(t["pnl_pct"], 1), "why": t["why"]} for t in top],
            "coins_traded": len({t["coin"] for t in tr}),
            "trades_in_RLC_DIMO": [{"coin": t["coin"], "in": fmt(t["entry"]), "out": fmt(t["exit"]), "pnl_pct": round(t["pnl_pct"], 1), "why": t["why"]} for t in tr if t["coin"] in ("RLC-USD", "DIMO-USD")]}
STRATS = {
 "rotation_7d_top1_daily": lambda f: rotation(7 * 24, 1, 24, f),
 "rotation_7d_top3_daily": lambda f: rotation(7 * 24, 3, 24, f),
 "rotation_24h_top3_daily": lambda f: rotation(24, 3, 24, f),
 "rotation_7d_top3_weekly": lambda f: rotation(7 * 24, 3, 7 * 24, f),
 "breakout_7d_high_vol3x_trail15_hold7d": lambda f: breakout(0.15, 7 * 24, 3, f),
 "breakout_7d_high_vol3x_trail8_hold7d": lambda f: breakout(0.08, 7 * 24, 3, f),
 "hold_BTC": lambda f: hold("BTC-USD", f),
 "hold_ETH": lambda f: hold("ETH-USD", f),
}
out = {"artifact_type": "research_only_dynamic_universe_simulation", "not_promotion_evidence": True,
       "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "products_loaded": len(PIDS),
       "data_window": [str(dt.datetime.fromtimestamp(START, dt.timezone.utc)), str(dt.datetime.fromtimestamp(END, dt.timezone.utc))],
       "eligible_at_sim_start": sum(eligible(p, 7 * 24) for p in PIDS), "eligible_at_end": sum(eligible(p, N - 1) for p in PIDS), "results": []}
for fee in (10.0, 60.0, 120.0):
    for name, fn in STRATS.items():
        out["results"].append({"strategy": name, "fee_bps_per_side": fee, "slippage_bps": 10.0, **stats(fn(fee))})
        print(name, fee, file=sys.stderr, flush=True)
print(json.dumps(out, indent=1))
