"""Versioned diagnostic rerun of the frozen short-hold top-gainer study (dynamic_coin_simulation_20261009/short_hold.py)
under the corrected execution contract. Research only; original script and JSON unchanged.

WRITTEN BEFORE THE FIRST RUN (2026-10-09):
  Frozen, unchanged: all 14 original strategies (12 rotations: top-3 by 1/4/24 h gain, held 1/4/12/24 h; 2 take-profit/
  stop variants), their decision logic executed from the hashed original (eligibility, ranking, targets, the gain
  check for take-profit/stop computed on the original's own last-completed close), 10 bps slippage, both original
  windows (2026-08-10..2026-10-09 on cb/h1; 2025-10-09..2026-08-10 on cb2/h1).
  Corrected: fills at the OPEN of the decision hour's bar, not the last completed close; no fill without a bar;
  held coins never valued or sold at forward-filled prices (strict = INCOMPLETE; outage = keep, NAV unknown, sale
  deferred to the coin's next observed open; no new buys while any held coin lacks a bar).
  Fees: 0 bps (the deciding check: the original lost at zero fees, so a positive corrected zero-fee result is the
  only way this verdict could change), 50 bps primary, 120 bps stress. No pass/fail bar is added or changed."""
import argparse, contextlib, hashlib, io, json, math, statistics, sys, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "docs/research/dynamic_coin_simulation_20261009/short_hold.py"
WINDOWS = {"last_60d": ("2026-08-10", "2026-10-09", "cb"), "prior_10m": ("2025-10-09", "2026-08-10", "cb2")}
FEES = {"zero_fee": 0.0, "primary_50bps": 0.005, "stress_120bps": 0.012}
SLIP = 0.001
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_frozen(window, data_root):
    start, end, sub = WINDOWS[window]
    text = SRC.read_text()
    prefix = text[: text.index("\ndef rotation")]
    ns = {"__file__": str(SRC), "__name__": "frozen"}
    argv = sys.argv; sys.argv = [str(SRC), str(Path(data_root) / sub), start, end]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(compile(prefix, str(SRC), "exec"), ns)
    finally:
        sys.argv = argv
    folder = Path(data_root) / sub / "h1"
    ns["OPEN"], ns["ACTUAL_CLOSE"] = {}, {}
    for pid in ns["PIDS"]:
        o = [None] * ns["N"]; c = [None] * ns["N"]
        for ts, op, hi, lo, cl, vo in json.load(open(folder / f"{pid}.json")):
            i = ns["IDX"].get(ts)
            if i is not None: o[i] = float(op); c[i] = float(cl)
        ns["OPEN"][pid] = o; ns["ACTUAL_CLOSE"][pid] = c
    return ns, folder


def ok(x):
    return x is not None and math.isfinite(x) and x > 0


class Book:
    def __init__(s, ns, fee, mode):
        s.ns, s.fee, s.mode = ns, fee, mode
        s.cash = 1000.0; s.pos = {}; s.tr = []; s.nav = []; s.deferred = {}
        s.status = "COMPLETE"; s.stopped_at = None; s.entries_skipped = 0

    def buy(s, pid, usd, i):
        if usd <= 1e-9: return
        if any(not ok(s.ns["OPEN"][h][i]) for h in s.pos) or not ok(s.ns["OPEN"][pid][i]):
            s.entries_skipped += 1; return
        px = s.ns["OPEN"][pid][i]; q = (usd / (1 + s.fee)) / (px * (1 + SLIP)); s.cash -= usd
        p = s.pos.setdefault(pid, {"q": 0.0, "cost": 0.0, "t": i}); p["q"] += q; p["cost"] += usd

    def sell(s, pid, i, why):
        px = s.ns["OPEN"][pid][i]
        if not ok(px):
            s.deferred[pid] = why; return False
        p = s.pos.pop(pid); got = p["q"] * px * (1 - SLIP) * (1 - s.fee); s.cash += got
        s.tr.append({"coin": pid, "ret": got / p["cost"] - 1, "why": why}); s.deferred.pop(pid, None)
        return True

    def frozen_value(s, i):
        return s.cash + sum(p["q"] * s.ns["mark"](pid, i) for pid, p in s.pos.items())

    def start_hour(s, i):
        for pid, why in list(s.deferred.items()):
            if pid in s.pos: s.sell(pid, i, why)
            else: s.deferred.pop(pid, None)
        if s.mode == "strict":
            for pid in s.pos:
                if not ok(s.ns["OPEN"][pid][i]):
                    s.status = "INCOMPLETE"
                    s.stopped_at = f"{pid} no bar {dt.datetime.fromtimestamp(s.ns['T'][i], dt.timezone.utc):%Y-%m-%d %H:%M}"
                    return False
        return True

    def end_hour(s, i):
        marks = [p["q"] * s.ns["ACTUAL_CLOSE"][pid][i] if ok(s.ns["ACTUAL_CLOSE"][pid][i]) else None for pid, p in s.pos.items()]
        s.nav.append(None if None in marks else s.cash + sum(marks))


def rotation(ns, L, Hh, K, fee, mode):
    b = Book(ns, fee, mode); mark = ns["mark"]
    for i in range(169, ns["N"]):
        if not b.start_hour(i): break
        if (i - 169) % Hh == 0:
            want = [p for r, p in ns["ranked"](i, L)[:K] if r > 0]
            for pid in list(b.pos):
                if pid not in want and pid not in b.deferred: b.sell(pid, i, "rotated_out")
            tgt = b.frozen_value(i) / K
            for pid in want:
                have = b.pos[pid]["q"] * mark(pid, i) if pid in b.pos else 0.0
                if have < tgt * 0.5: b.buy(pid, min(b.cash, tgt - have), i)
        b.end_hour(i)
    return b


def tp_sl(ns, L, tp, sl, max_h, K, fee, mode):
    b = Book(ns, fee, mode); mark = ns["mark"]
    for i in range(169, ns["N"]):
        if not b.start_hour(i): break
        for pid in list(b.pos):
            if pid in b.deferred: continue
            p = b.pos[pid]; g = mark(pid, i) * (1 - SLIP) * (1 - b.fee) * p["q"] / p["cost"] - 1
            if g >= tp: b.sell(pid, i, "take_profit")
            elif g <= -sl: b.sell(pid, i, "stop_loss")
            elif i - p["t"] >= max_h: b.sell(pid, i, "time_stop")
        if len(b.pos) < K:
            for r, pid in ns["ranked"](i, L):
                if len(b.pos) >= K or r <= 0: break
                if pid not in b.pos: b.buy(pid, min(b.cash, b.frozen_value(i) / K), i)
        b.end_hour(i)
    return b


STRATS = [(f"top3_by_{L}h_gain_hold_{Hh}h", ("rot", L, Hh)) for L in (1, 4, 24) for Hh in (1, 4, 12, 24)]
STRATS += [("top3_by_4h_gain_tp5_sl3_max24h", ("tp", 4, 0.05, 0.03, 24)), ("top3_by_24h_gain_tp10_sl5_max48h", ("tp", 24, 0.10, 0.05, 48))]


def run_one(ns, spec, fee, mode):
    return rotation(ns, spec[1], spec[2], 3, fee, mode) if spec[0] == "rot" else tp_sl(ns, spec[1], spec[2], spec[3], spec[4], 3, fee, mode)


def summarize(b):
    known = [v for v in b.nav if v is not None]
    pk, mdd = 1000.0, 0.0
    for v in known: pk = max(pk, v); mdd = max(mdd, 1 - v / pk)
    rs = [t["ret"] for t in b.tr]
    return {"status": b.status, "stopped_at": b.stopped_at, "hours": len(b.nav), "unknown_nav_hours": sum(v is None for v in b.nav),
            "end_nav_usd": round(b.nav[-1], 2) if b.nav and b.nav[-1] is not None else None,
            "last_known_nav_usd": round(known[-1], 2) if known else None, "max_drawdown_observed_pct": round(mdd * 100, 2),
            "closed_trades": len(rs), "win_pct": round(100 * sum(r > 0 for r in rs) / len(rs), 1) if rs else None,
            "mean_trade_pct": round(statistics.mean(rs) * 100, 3) if rs else None,
            "median_trade_pct": round(statistics.median(rs) * 100, 3) if rs else None,
            "entries_skipped": b.entries_skipped, "sales_deferred_at_end": len(b.deferred),
            "exit_reasons": {w: sum(1 for t in b.tr if t["why"] == w) for w in sorted({t["why"] for t in b.tr})}}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--window", choices=list(WINDOWS), required=True); ap.add_argument("--fee", choices=list(FEES), required=True)
    ap.add_argument("--mode", choices=["strict", "outage"], required=True)
    a = ap.parse_args()
    ns, folder = load_frozen(a.window, a.data)
    out = {"artifact_type": "research_only_corrected_frozen_short_hold_rerun", "not_promotion_evidence": True, "not_independent_holdout": True,
           "script_sha256": sha(__file__), "original_source_sha256": {str(SRC.relative_to(ROOT)): sha(SRC)},
           "input_sha256": {f"{WINDOWS[a.window][2]}/h1/{p}.json": sha(folder / f"{p}.json") for p in ns["PIDS"]}, "results": {}}
    for name, spec in STRATS:
        out["results"][f"{a.window}|{name}|{a.fee}|{a.mode}"] = summarize(run_one(ns, spec, FEES[a.fee], a.mode))
    with Path(f"{a.out}.part.{a.window}.{a.fee}.{a.mode}.json").open("x") as fh:
        json.dump(out, fh, allow_nan=False)
    for k, v in out["results"].items():
        print(k, v["status"], v["end_nav_usd"], v["closed_trades"], v["mean_trade_pct"], v["stopped_at"])


if __name__ == "__main__":
    main()
