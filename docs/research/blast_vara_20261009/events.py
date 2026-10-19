"""Research-only event studies on Coinbase hourly candles, 2025-10-09 to 2026-10-09, every USD coin.
A) Pump: an hour that closes at least +10% above the previous close. Buy at that close.
B) Dip in an uptrend: coin up at least 30% over the prior 30 days, and its close is at least 10% below the
   highest close of the prior 72 hours. Buy at that close. One event per coin per 72 hours.
Exits use the hourly high/low: if take-profit and stop are both touched in one hour, the stop is assumed first.
Costs: fee per side (60 bps), slippage by liquidity (10 bps at >=$2M/day, 50 bps at $100K-$2M, 150 bps below)."""
import json, os, sys, statistics, datetime as dt, math, hashlib
S = sys.argv[1]
def load_dir(d):
    out = {}
    for f in os.listdir(d):
        for r in json.load(open(f"{d}/{f}")): out.setdefault(f[:-5], {})[r[0]] = r
    return out
A = load_dir(f"{S}/cb2/h1"); B = load_dir(f"{S}/cb/h1")
for k, v in B.items(): A.setdefault(k, {}).update(v)
for pid in ("BLAST-USD", "VARA-USD"):
    for r in json.load(open(f"{S}/bv/{pid}_h1.json")): A.setdefault(pid, {})[r[0]] = r
SER = {}
for pid, m in A.items():
    ts = sorted(m); 
    if len(ts) < 24 * 40: continue
    SER[pid] = [m[t] for t in ts]   # [ts, o, h, l, c, v]
FEE = 0.006
def slip_for(usd_day): return 0.001 if usd_day >= 2e6 else 0.005 if usd_day >= 1e5 else 0.015
def usd_day(rows, i):
    lo = max(0, i - 168); w = rows[lo:i]
    return sum(r[4] * r[5] for r in w) / max(1, len(w)) * 24
def simulate_exit(rows, i, tp, sl, max_h, trail=None):
    """Entry at close of bar i. Returns (gross_return, hours_held, reason)."""
    e = rows[i][4]; peak = e; t0 = rows[i][0]
    for j in range(i + 1, len(rows)):
        if rows[j][0] - t0 > max_h * 3600: return rows[j - 1][4] / e - 1, (rows[j - 1][0] - t0) / 3600, "time"
        h, l, c = rows[j][2], rows[j][3], rows[j][4]
        stop = e * (1 - sl) if sl else None
        if trail: stop = max(stop or 0, peak * (1 - trail))
        if stop and l <= stop: return stop / e - 1, (rows[j][0] - t0) / 3600, "stop"
        if tp and h >= e * (1 + tp): return tp, (rows[j][0] - t0) / 3600, "take_profit"
        peak = max(peak, h)
    return rows[-1][4] / e - 1, (rows[-1][0] - t0) / 3600, "open_at_end"
def fwd(rows, i, h):
    t = rows[i][0] + h * 3600
    for j in range(i + 1, min(len(rows), i + h + 5)):
        if rows[j][0] >= t: return rows[j][4] / rows[i][4] - 1
    return None
def summarize(xs):
    if not xs: return {"n": 0}
    s = sorted(xs); q = lambda p: s[min(len(s) - 1, int(p * len(s)))]
    return {"n": len(xs), "mean_pct": round(statistics.mean(xs) * 100, 2), "median_pct": round(statistics.median(xs) * 100, 2),
            "win_pct": round(100 * sum(1 for x in xs if x > 0) / len(xs), 1), "worst_pct": round(s[0] * 100, 1), "p05_pct": round(q(0.05) * 100, 1),
            "p95_pct": round(q(0.95) * 100, 1), "best_pct": round(s[-1] * 100, 1)}
EXITS = {"hold_1h": None, "hold_4h": None, "hold_24h": None,
         "tp10_sl5_max24h": (0.10, 0.05, 24, None), "tp20_sl10_max72h": (0.20, 0.10, 72, None), "trail8_max72h": (None, None, 72, 0.08),
         "tp10_sl10_max168h": (0.10, 0.10, 168, None), "tp15_sl8_max168h": (0.15, 0.08, 168, None), "trail15_max168h": (None, None, 168, 0.15)}
def run_events(kind):
    res = {}; per_coin = {}; examples = []
    for pid, rows in SER.items():
        last_ev = -10 ** 12
        for i in range(721, len(rows) - 1):
            if rows[i][0] - rows[i - 1][0] != 3600: continue
            if kind == "pump":
                ok = rows[i][4] >= rows[i - 1][4] * 1.10
            else:
                r30 = None
                for j in range(i - 1, max(0, i - 760), -1):
                    if rows[i][0] - rows[j][0] >= 30 * 86400: r30 = rows[i][4] / rows[j][4] - 1; break
                hi72 = max(r[4] for r in rows[max(0, i - 72):i])
                ok = r30 is not None and r30 >= 0.30 and rows[i][4] <= hi72 * 0.90 and rows[i][0] - last_ev >= 72 * 3600
            if not ok: continue
            last_ev = rows[i][0]
            ud = usd_day(rows, i); sl_ = slip_for(ud); bucket = ">=$2M/day" if ud >= 2e6 else "$100K-2M/day" if ud >= 1e5 else "<$100K/day"
            cost = (1 + sl_) * (1 + FEE) / ((1 - sl_) * (1 - FEE)) - 1
            for name, spec in EXITS.items():
                if spec is None:
                    g = fwd(rows, i, int(name.split("_")[1][:-1]))
                    if g is None: continue
                else:
                    g = simulate_exit(rows, i, *spec)[0]
                net = (1 + g) / (1 + cost) - 1
                for key in (("all", name), (bucket, name)):
                    res.setdefault(key, {"gross": [], "net": []}); res[key]["gross"].append(g); res[key]["net"].append(net)
                if pid in ("BLAST-USD", "VARA-USD"):
                    per_coin.setdefault((pid, name), {"gross": [], "net": []}); per_coin[(pid, name)]["gross"].append(g); per_coin[(pid, name)]["net"].append(net)
            examples.append((pid, dt.datetime.fromtimestamp(rows[i][0], dt.timezone.utc).strftime("%Y-%m-%d %H:00"), round(ud)))
    fmt = lambda d: {f"{k[0]} | {k[1]}": {"gross": summarize(v["gross"]), "net_after_costs": summarize(v["net"])} for k, v in sorted(d.items())}
    return {"by_bucket_and_exit": fmt(res), "blast_vara": fmt(per_coin), "events": len(examples), "coins": len({e[0] for e in examples}),
            "blast_vara_events": [e for e in examples if e[0] in ("BLAST-USD", "VARA-USD")]}
out = {"artifact_type": "research_only_event_study", "not_promotion_evidence": True, "coins": len(SER),
       "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(), "pump_10pct_hour": run_events("pump"), "dip_in_uptrend": run_events("dip")}
print(json.dumps(out, indent=1))
