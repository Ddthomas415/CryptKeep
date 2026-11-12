"""Descriptive report on the BTC+ETH trend candidate (research item 7). Definitions: PLAN.md in this folder, written
before this script was run. Research only; descriptive, not a test. Usage: python3 -B describe.py DATA_DIR
DATA_DIR must contain maj/BTC-USD_d1.json and maj/ETH-USD_d1.json (hash-checked below)."""
import datetime as dt, hashlib, json, math, statistics, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECT = {"scripts/research/rerun_frozen_stress.py": "1f98513ae63c4f84819327746872a9dd0a73b3bc35e5e67364c57458ca395907",
          "docs/research/majors_trend_20261009/BTC-USD_d1.json": "64cab2cf912244babb251485a9949a266be30fb80840e95b80d4478a9cde07c0",
          "docs/research/majors_trend_20261009/ETH-USD_d1.json": "9fa81ca8395321dddc5453a2144b5081ada012e74ed3132c9c2c039e5e6206b8"}
got = {k: sha(ROOT / k) for k in EXPECT}
data = Path(sys.argv[1])
for a in ("BTC", "ETH"):
    got[f"DATA/maj/{a}-USD_d1.json"] = sha(data / "maj" / f"{a}-USD_d1.json")
if any(got[k] != v for k, v in EXPECT.items()) or got["DATA/maj/BTC-USD_d1.json"] != EXPECT["docs/research/majors_trend_20261009/BTC-USD_d1.json"] \
        or got["DATA/maj/ETH-USD_d1.json"] != EXPECT["docs/research/majors_trend_20261009/ETH-USD_d1.json"]:
    raise SystemExit(f"hash mismatch {got}")
from scripts.research.rerun_frozen_stress import load_frozen, run
from scripts.research.corrected_research_math import rebalance
ns = load_frozen(data); P, O, WD, days, PER, stats = ns["P"], ns["OPEN"], ns["WD"], ns["days"], ns["PER"], ns["stats"]
A2 = ("BTC", "ETH"); SLIP = 0.0005; EPS = 1e-12
day = lambda k: dt.datetime.fromtimestamp(days[k], dt.timezone.utc).date().isoformat()

def instrumented(lo, hi, fee, kind="rule", fixed=None):
    cash, units = 1000.0, {}; curve = [1000.0]; trades = []; spells = {a: None for a in A2}; closed = []
    pending = ns["target"]("rule", lo, 28, 0.5, A2, None) if kind == "rule" else dict(fixed)
    traded_usd = 0.0
    for k in range(lo + 1, hi + 1):
        if pending is not None:
            prices = {a: O[a][k] for a in A2}
            old = {a: units.get(a, 0.0) for a in A2}
            cash_before = cash
            cash, units = rebalance(cash, units, prices, pending, fee, SLIP)
            flows = 0.0
            for a in A2:
                dq = units.get(a, 0.0) - old[a]
                if abs(dq) <= EPS: continue
                px = prices[a]; traded_usd += abs(dq) * px
                flow = -dq * px * (1 + SLIP) * (1 + fee) if dq > 0 else -dq * px * (1 - SLIP) * (1 - fee)
                flows += flow
                kind_t = "entry" if old[a] <= EPS else ("exit" if units.get(a, 0.0) <= EPS else "resize")
                trades.append({"day": day(k), "asset": a, "type": kind_t, "units_delta": dq, "price": px, "cash_flow": flow})
                if kind_t == "entry":
                    spells[a] = {"asset": a, "entry_day": day(k), "entry_k": k, "cash_in": 0.0, "cash_out": -flow, "entry_cost_usd": -flow}
                elif spells[a] is not None:
                    if flow >= 0: spells[a]["cash_in"] += flow
                    else: spells[a]["cash_out"] += -flow
                if kind_t == "exit" and spells[a] is not None:
                    s = spells[a]; s.update(exit_day=day(k), days=k - s["entry_k"], net_pnl=s["cash_in"] - s["cash_out"])
                    s["return_pct"] = 100 * s["net_pnl"] / s["entry_cost_usd"]; closed.append(s); spells[a] = None
            if abs((cash - cash_before) - flows) > 1e-6:
                raise SystemExit(f"cash flow attribution mismatch on {day(k)}: {cash - cash_before} vs {flows}")
            pending = None
        nav = cash + sum(q * P[a][k] for a, q in units.items())
        curve.append(nav)
        if kind == "rule" and k < hi and WD[k] == 6:
            pending = ns["target"]("rule", k, 28, 0.5, A2, None)
    open_spells = []
    for a, s in spells.items():
        if s is not None:
            mark = units.get(a, 0.0) * P[a][hi]
            open_spells.append({**s, "mark_usd": mark, "open_pnl": s["cash_in"] + mark - s["cash_out"]})
    return curve, trades, closed, open_spells, traded_usd

def trip_stats(closed):
    n = len(closed); wins = [s["net_pnl"] for s in closed if s["net_pnl"] > 0]; losses = [s["net_pnl"] for s in closed if s["net_pnl"] < 0]
    return {"round_trips": n, "wins": len(wins), "losses": len(losses),
            "win_rate_net_pct": round(100 * len(wins) / n, 1) if n else None,
            "profit_factor_net": round(sum(wins) / abs(sum(losses)), 2) if losses else None,
            "avg_win_usd": round(statistics.mean(wins), 2) if wins else None, "avg_loss_usd": round(statistics.mean(losses), 2) if losses else None,
            "median_spell_days": statistics.median([s["days"] for s in closed]) if n else None,
            "by_asset": {a: sum(1 for s in closed if s["asset"] == a) for a in A2}}

def weekly(curves, lo, hi):
    sma = lambda k: sum(P["BTC"][k - 199:k + 1]) / 200
    dec = [k for k in range(lo, hi) if WD[k] == 6]
    rows = []
    for j in range(len(dec) - 1):
        d0, d1 = dec[j], dec[j + 1]
        if d0 - 220 < 0: lab = "insufficient"
        else:
            s0, sprev = sma(d0), sma(d0 - 20)
            lab = "bull" if P["BTC"][d0] > s0 and s0 > sprev else ("bear" if P["BTC"][d0] < s0 and s0 < sprev else "mixed")
        rows.append({"label": lab, **{n: c[d1 - lo] / c[d0 - lo] - 1 for n, c in curves.items()}})
    out = {}
    for lab in ("bull", "bear", "mixed", "insufficient"):
        rs = [r for r in rows if r["label"] == lab]
        if not rs: continue
        out[lab] = {"weeks": len(rs), **{n: {"mean_weekly_pct": round(100 * statistics.mean(r[n] for r in rs), 3),
                    "compounded_pct": round(100 * (math.prod(1 + r[n] for r in rs) - 1), 1)} for n in curves}}
    return out

def years(curves, lo, hi):
    out = {}
    ends = {}
    for k in range(lo, hi + 1):
        ends[day(k)[:4]] = k
    prev = lo
    for y, k in sorted(ends.items()):
        out[y] = {n: round(100 * (c[k - lo] / c[prev - lo] - 1), 1) for n, c in curves.items()}
        out[y]["from"] = day(prev); out[y]["to"] = day(k); prev = k
    return out

out = {"artifact_type": "research_only_descriptive_not_a_test", "plan_sha256": sha(Path(__file__).parent / "PLAN.md"),
       "script_sha256": sha(__file__), "inputs_sha256": got, "slippage_per_side": SLIP, "results": {}}
for fee in (0.005, 0.012):
    R = out["results"][str(fee)] = {}
    for p, (lo, hi) in PER.items():
        ref, _ = run(ns, "rule", lo, hi, fee=fee)
        c, trades, closed, opens, traded = instrumented(lo, hi, fee)
        maxdiff = max(abs(a - b) for a, b in zip(ref, c))
        if len(ref) != len(c) or maxdiff > 0.01:
            raise SystemExit(f"reproduction check failed {fee} {p}: max diff {maxdiff}")
        recon = c[-1] - 1000.0 - (sum(s["net_pnl"] for s in closed) + sum(s["open_pnl"] for s in opens))
        if abs(recon) > 0.05:
            raise SystemExit(f"reconciliation failed {fee} {p}: {recon}")
        hb, _ = run(ns, "hold_btc", lo, hi, fee=fee)
        he, _, _, _, _ = instrumented(lo, hi, fee, kind="fixed", fixed={"ETH": 1.0})
        yrs = (hi - lo) / 365
        reb = sorted({t["day"] for t in trades})
        R[p] = {"period": [day(lo), day(hi)], "reproduction_max_abs_diff_usd": round(maxdiff, 6), "reconciliation_residual_usd": round(recon, 6),
                "rule": stats(c), "hold_btc": stats(hb), "hold_eth": stats(he),
                "trades": {"rebalance_days_with_trades": len(reb), "per_year": round(len(reb) / yrs, 1),
                           "entries": sum(t["type"] == "entry" for t in trades), "exits": sum(t["type"] == "exit" for t in trades),
                           "resizes": sum(t["type"] == "resize" for t in trades),
                           "turnover_x_per_year": round(traded / statistics.mean(c) / yrs, 2)},
                "round_trips": trip_stats(closed),
                "open_spells_at_end": [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in s.items() if k != "entry_k"} for s in opens],
                "regimes": weekly({"rule": c, "hold_btc": hb, "hold_eth": he}, lo, hi)}
        if p == "FULL":
            R[p]["calendar_years_pct"] = years({"rule": c, "hold_btc": hb, "hold_eth": he}, lo, hi)
            R[p]["round_trip_list"] = [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in s.items() if k != "entry_k"} for s in closed]
with open(Path(__file__).parent / "results.json", "x") as fh:
    json.dump(out, fh, indent=1, allow_nan=False)
for f in ("0.005", "0.012"):
    for p in ("A", "B", "C", "FULL"):
        r = out["results"][f][p]; rt = r["round_trips"]
        print(f, p, "rule $%.0f DD %s%% | BTC $%.0f | ETH $%.0f | trips %s win %s%% PF %s | turnover %sx/yr" % (
            r["rule"]["end_usd"], r["rule"]["max_drawdown_pct"], r["hold_btc"]["end_usd"], r["hold_eth"]["end_usd"],
            rt["round_trips"], rt["win_rate_net_pct"], rt["profit_factor_net"], r["trades"]["turnover_x_per_year"]))
