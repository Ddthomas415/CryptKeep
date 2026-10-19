"""Versioned diagnostic rerun of the frozen Coinbase dynamic-universe simulation under the corrected execution
contract. Research only; original sim.py / sim_earlier_10_months.py, their JSON and workbook are unchanged.

WRITTEN BEFORE THE FIRST RUN (2026-10-09):
  Frozen, unchanged: all 8 original strategies (no selection), their decision logic (signals, eligibility,
  ranking, targets, trailing-stop and time-stop triggers) computed exactly as in the original from bars that
  closed before the decision hour, using the original script's own (forward-filled) close series, executed from
  the hashed original source. Original 10 bps slippage. Windows: last 60 days (cb/h1) and prior 10 months (cb2/h1).
  Corrected:
    - every fill is at the OPEN of the decision hour's bar (the first price after the decision), not at the close
      of the last completed hour; a coin with no bar at that hour cannot be bought (entry skipped, counted);
    - held coins are never valued or sold at a forward-filled price. strict: a held coin missing an hourly bar
      stops the run as INCOMPLETE. outage (separately labeled): the position is kept, that hour's NAV is unknown,
      and a due sale waits for the coin's next observed open;
    - marks use the actual close of each observed bar.
  Costs: 0.50% per side primary (observed account taker tier; product applicability UNVERIFIED), 0.60% and
  1.20% stress, plus 10 bps slippage. Benchmarks (hold_BTC, hold_ETH) follow the same fill rule.
  Statistics: end value, max drawdown on observed NAV, unknown-NAV hours, trades, win rate; the shared paired
  56-day block Sharpe vs BTC only when day-end NAVs are complete and >= 112 days exist (the 60-day window cannot
  qualify and is reported as such). No pass/fail bar is added or changed."""
import argparse, hashlib, json, math, statistics, sys, io, contextlib, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.research.corrected_research_math import paired_block_sharpe  # noqa: E402

FEES = {"primary_50bps": 0.005, "stress_60bps": 0.006, "stress_120bps": 0.012}
SLIP = 0.001
WINDOWS = {"last_60d": ("docs/research/dynamic_coin_simulation_20261009/sim.py", "cb"),
           "prior_10m": ("docs/research/dynamic_coin_simulation_20261009/sim_earlier_10_months.py", "cb2")}
STRATS = ["rotation_7d_top1_daily", "rotation_7d_top3_daily", "rotation_24h_top3_daily", "rotation_7d_top3_weekly",
          "breakout_7d_high_vol3x_trail15_hold7d", "breakout_7d_high_vol3x_trail8_hold7d", "hold_BTC", "hold_ETH"]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_frozen(window, data_root):
    src = ROOT / WINDOWS[window][0]
    text = src.read_text()
    prefix = text[: text.index("\nSTRATS = {")]
    ns = {"__file__": str(src), "__name__": "frozen"}
    argv = sys.argv; sys.argv = [str(src), str(Path(data_root) / WINDOWS[window][1])]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(compile(prefix, str(src), "exec"), ns)
    finally:
        sys.argv = argv
    folder = Path(data_root) / WINDOWS[window][1] / "h1"
    opens, closes = {}, {}
    for pid in ns["PIDS"]:
        o = [None] * ns["N"]; c = [None] * ns["N"]
        for ts, op, hi, lo, cl, vo in json.load(open(folder / f"{pid}.json")):
            i = ns["IDX"].get(ts)
            if i is not None: o[i] = float(op); c[i] = float(cl)
        opens[pid] = o; closes[pid] = c
    ns["OPEN"], ns["ACTUAL_CLOSE"] = opens, closes
    return ns, src, folder


class Book:
    """Decisions use the frozen mark (close of the last completed hour); fills use the open of hour i."""
    def __init__(s, ns, fee, mode):
        s.ns, s.fee, s.mode = ns, fee, mode
        s.cash = 1000.0; s.pos = {}; s.trades = []; s.nav = []; s.deferred = set()
        s.status = "COMPLETE"; s.stopped_at = None; s.entries_skipped = 0

    def fill(s, pid, i):
        return s.ns["OPEN"][pid][i]

    def buy(s, pid, usd, i):
        if usd <= 1e-9: return
        # Unknown held valuation cannot authorize additional exposure.
        if any(s.ns["OPEN"][held][i] is None
               or not math.isfinite(s.ns["OPEN"][held][i])
               or s.ns["OPEN"][held][i] <= 0 for held in s.pos):
            s.entries_skipped += 1; return
        px = s.fill(pid, i)
        if px is None or not math.isfinite(px) or px <= 0: s.entries_skipped += 1; return
        q = (usd / (1 + s.fee)) / (px * (1 + SLIP)); s.cash -= usd
        p = s.pos.setdefault(pid, {"q": 0.0, "cost": 0.0, "t": s.ns["T"][i], "peak": s.ns["mark"](pid, i)})
        p["q"] += q; p["cost"] += usd

    def sell(s, pid, i, why):
        px = s.fill(pid, i)
        if px is None or px <= 0:
            s.deferred.add((pid, why)); return False
        p = s.pos.pop(pid); got = p["q"] * px * (1 - SLIP) * (1 - s.fee); s.cash += got
        s.trades.append({"coin": pid, "entry": p["t"], "exit": s.ns["T"][i], "ret": got / p["cost"] - 1, "why": why})
        return True

    def frozen_value(s, i):
        """The original decision-time equity (used only for sizing decisions, as in the frozen rule)."""
        return s.cash + sum(p["q"] * s.ns["mark"](pid, i) for pid, p in s.pos.items())

    def start_hour(s, i):
        """Retry deferred sales; enforce strict mode on held coins without a bar this hour."""
        for pid, why in list(s.deferred):
            if pid in s.pos and s.sell(pid, i, why): s.deferred.discard((pid, why))
            elif pid not in s.pos: s.deferred.discard((pid, why))
        if s.mode == "strict":
            for pid in s.pos:
                if s.ns["OPEN"][pid][i] is None:
                    s.status = "INCOMPLETE"; s.stopped_at = f"{pid} no bar {dt.datetime.fromtimestamp(s.ns['T'][i], dt.timezone.utc):%Y-%m-%d %H:%M}"
                    return False
        return True

    def end_hour(s, i):
        marks = [p["q"] * s.ns["ACTUAL_CLOSE"][pid][i] if s.ns["ACTUAL_CLOSE"][pid][i] is not None else None for pid, p in s.pos.items()]
        s.nav.append((s.ns["T"][i], None if None in marks else s.cash + sum(marks)))


def rotation(ns, lookback_h, top_k, rebalance_h, fee, mode, min_usd=2e6):
    b = Book(ns, fee, mode); N = ns["N"]; PIDS = ns["PIDS"]; eligible = ns["eligible"]; ret = ns["ret"]; mark = ns["mark"]
    for i in range(N):
        if i >= 7 * 24 and not b.start_hour(i): break
        if i >= 7 * 24 and (i - 7 * 24) % rebalance_h == 0:
            ranked = sorted(((ret(p, i, lookback_h), p) for p in PIDS if eligible(p, i, min_usd) and ret(p, i, lookback_h) is not None), reverse=True)
            want = [p for r, p in ranked[:top_k] if r > 0]
            for pid in list(b.pos):
                if pid not in want: b.sell(pid, i, "rotated_out")
            target = b.frozen_value(i) / top_k
            for pid in want:
                have = b.pos[pid]["q"] * mark(pid, i) if pid in b.pos else 0.0
                if have < target * 0.5: b.buy(pid, min(b.cash, target - have), i)
        if i >= 7 * 24: b.end_hour(i)
    return b


def breakout(ns, trail, max_hold_h, slots, fee, mode, vol_mult=3.0, min_usd=2e6):
    b = Book(ns, fee, mode); N = ns["N"]; PIDS = ns["PIDS"]; eligible = ns["eligible"]; mark = ns["mark"]
    high, vol_usd, T, H = ns["high"], ns["vol_usd"], ns["T"], ns["H"]
    for i in range(7 * 24 + 1, N):
        if not b.start_hour(i): break
        pending = {pid for pid, _ in b.deferred}
        for pid in list(b.pos):
            if pid in pending: continue
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
                b.buy(pid, min(b.cash, b.frozen_value(i) / slots), i)
        b.end_hour(i)
    return b


def hold(ns, pid, fee, mode):
    b = Book(ns, fee, mode)
    first = 7 * 24
    while first < ns["N"] and ns["OPEN"][pid][first] is None: first += 1
    b.buy(pid, 1000.0, first)
    for i in range(first, ns["N"]):
        if not b.start_hour(i): break
        b.end_hour(i)
    return b


def run_strategy(ns, name, fee, mode):
    table = {
        "rotation_7d_top1_daily": lambda: rotation(ns, 7 * 24, 1, 24, fee, mode),
        "rotation_7d_top3_daily": lambda: rotation(ns, 7 * 24, 3, 24, fee, mode),
        "rotation_24h_top3_daily": lambda: rotation(ns, 24, 3, 24, fee, mode),
        "rotation_7d_top3_weekly": lambda: rotation(ns, 7 * 24, 3, 7 * 24, fee, mode),
        "breakout_7d_high_vol3x_trail15_hold7d": lambda: breakout(ns, 0.15, 7 * 24, 3, fee, mode),
        "breakout_7d_high_vol3x_trail8_hold7d": lambda: breakout(ns, 0.08, 7 * 24, 3, fee, mode),
        "hold_BTC": lambda: hold(ns, "BTC-USD", fee, mode),
        "hold_ETH": lambda: hold(ns, "ETH-USD", fee, mode),
    }
    return table[name]()


def day_end(nav):
    by = {}
    for t, v in nav: by[dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat()] = v
    return by


def summarize(b, btc=None):
    known = [v for _, v in b.nav if v is not None]
    pk, mdd = 1000.0, 0.0
    for v in known: pk = max(pk, v); mdd = max(mdd, 1 - v / pk)
    rs = [t["ret"] for t in b.trades]
    out = {"status": b.status, "stopped_at": b.stopped_at, "hours": len(b.nav),
           "unknown_nav_hours": sum(1 for _, v in b.nav if v is None),
           "end_nav_usd": round(b.nav[-1][1], 2) if b.nav and b.nav[-1][1] is not None else None,
           "last_known_nav_usd": round(known[-1], 2) if known else None,
           "max_drawdown_observed_pct": round(mdd * 100, 2), "closed_trades": len(rs),
           "win_pct": round(100 * sum(r > 0 for r in rs) / len(rs), 1) if rs else None,
           "mean_trade_pct": round(statistics.mean(rs) * 100, 2) if rs else None,
           "entries_skipped_no_bar": b.entries_skipped, "open_positions_at_end": len(b.pos),
           "sales_still_deferred_at_end": len(b.deferred),
           "best_trades": [{"coin": t["coin"], "ret_pct": round(t["ret"] * 100, 1), "why": t["why"]} for t in sorted(b.trades, key=lambda t: -t["ret"])[:5]],
           "dimo_rlc_trades": [{"coin": t["coin"], "ret_pct": round(t["ret"] * 100, 1), "why": t["why"],
                                "entry": dt.datetime.fromtimestamp(t["entry"], dt.timezone.utc).strftime("%m-%d %H:%M")}
                               for t in b.trades if t["coin"] in ("DIMO-USD", "RLC-USD")]}
    if btc is not None:
        a, c = day_end(b.nav), day_end(btc.nav)
        days = [d for d in sorted(a) if d in c]
        if b.status == "COMPLETE" and len(days) >= 113 and all(a[d] is not None and c[d] is not None for d in days):
            left = [a[days[k]] / a[days[k - 1]] - 1 for k in range(1, len(days))]
            right = [c[days[k]] / c[days[k - 1]] - 1 for k in range(1, len(days))]
            try:
                out["block_sharpe_vs_btc"] = paired_block_sharpe(left, right)
            except ValueError as e:
                out["block_sharpe_vs_btc"] = {"status": "INCOMPLETE", "reason": str(e)}
        else:
            out["block_sharpe_vs_btc"] = {"status": "INCOMPLETE", "reason": "run incomplete, unknown day-end NAV, or < 113 days"}
    return out


def merge(out_path):
    """Combine part files; refuse mixed script/source hashes; never drop a part."""
    parts = sorted(Path(out_path).parent.glob(Path(out_path).name + ".part.*.json"))
    if not parts: raise SystemExit("no part files")
    loaded = [json.loads(p.read_text()) for p in parts]
    keys = ("script_sha256", "shared_math_sha256")
    for d in loaded:
        for k in keys:
            if d[k] != loaded[0][k]: raise SystemExit(f"mixed {k}: {d[k]} vs {loaded[0][k]}")
    merged = {k: loaded[0][k] for k in ("artifact_type", "not_promotion_evidence", "not_independent_holdout") + keys}
    merged["original_source_sha256"] = {}; merged["input_sha256"] = {}; merged["results"] = {}
    merged["parts"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in parts}
    for d in loaded:
        for manifest in ("original_source_sha256", "input_sha256"):
            for name, digest in d[manifest].items():
                if name in merged[manifest] and merged[manifest][name] != digest:
                    raise ValueError(f"conflicting {manifest}: {name}")
                merged[manifest][name] = digest
        for k, v in d["results"].items():
            if k in merged["results"]: raise SystemExit(f"duplicate result {k}")
            merged["results"][k] = v
    with Path(out_path).open("x") as stream:
        json.dump(merged, stream, allow_nan=False)
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", help="folder holding the extracted cb/ and cb2/ archives")
    ap.add_argument("--out", required=True)
    ap.add_argument("--window", choices=list(WINDOWS)); ap.add_argument("--strategy", choices=STRATS)
    ap.add_argument("--fee", choices=list(FEES)); ap.add_argument("--mode", choices=["strict", "outage"])
    ap.add_argument("--merge", action="store_true")
    a = ap.parse_args()
    if a.merge:
        m = merge(a.out); print("merged", len(m["results"]), "results from", len(m["parts"]), "parts"); return
    ns, src, folder = load_frozen(a.window, a.data)
    out = {"artifact_type": "research_only_corrected_frozen_dynamic_rerun", "not_promotion_evidence": True,
           "not_independent_holdout": True, "script_sha256": sha(__file__),
           "shared_math_sha256": sha(ROOT / "scripts/research/corrected_research_math.py"),
           "original_source_sha256": {str(src.relative_to(ROOT)): sha(src)},
           "input_sha256": {f"{WINDOWS[a.window][1]}/h1/{p}.json": sha(folder / f"{p}.json") for p in ns["PIDS"]},
           "results": {}}
    for fname, fee in FEES.items():
        if a.fee and fname != a.fee: continue
        for mode in ("strict", "outage"):
            if a.mode and mode != a.mode: continue
            btc = run_strategy(ns, "hold_BTC", fee, mode)
            b = btc if a.strategy == "hold_BTC" else run_strategy(ns, a.strategy, fee, mode)
            out["results"][f"{a.window}|{a.strategy}|{fname}|{mode}"] = summarize(b, None if a.strategy == "hold_BTC" else btc)
    Path(f"{a.out}.part.{a.window}.{a.strategy}.{a.fee or 'allfees'}.{a.mode or 'allmodes'}.json").write_text(json.dumps(out))
    for k, v in out["results"].items():
        print(k, v["status"], v["end_nav_usd"], v["last_known_nav_usd"], v["unknown_nav_hours"], v["closed_trades"], v["stopped_at"])


if __name__ == "__main__":
    main()
