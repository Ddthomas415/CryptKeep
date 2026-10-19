"""Versioned diagnostic rerun of the frozen Binance research strategies (hybrid_momentum_20261009/hybrid.py) under
the corrected execution contract. Research only; the original script, JSON and workbook are unchanged.

WRITTEN BEFORE THE FIRST RUN (2026-10-09):
  Frozen, unchanged: all 12 original strategies (no selection), their weight rules executed from the hashed
  original source (universe, trend/momentum signals, BTC 100-day filter, volatility scaling), weekly Sunday-close
  decisions, the continuous 2020-01-01 start, TRAIN 2020-2023 / TEST 2024-01-01..2026-10-08 split, 0.05% slippage,
  the current-listed Binance universe (survivorship limitation unchanged).
  Corrected:
    - weights decided at Sunday's close are executed at Monday's OPEN with the shared post-cost rebalance()
      helper, not at the deciding close; between rebalances positions are marked at actual closes;
    - a held coin with no candle is never given a 0% return (the original's implicit forward fill).
      strict: the run stops INCOMPLETE. outage (separately labeled): that day's NAV is unknown, the coin keeps its
      units, and a rebalance needing an unavailable open waits for the next day where all needed opens exist;
    - target coins without a Monday open are left out of that rebalance (their weight stays in cash), counted;
    - the original dropped daily returns above +500% as data errors; here prices are used as recorded, and every
      held-coin day above that threshold is counted and listed so its influence is visible.
  Costs: 0.50% per side primary (observed account taker tier; product applicability UNVERIFIED), 0.10% (original
  Binance base) and 0.60% / 1.20% stress, plus 0.05% slippage.
  Statistics: TRAIN/TEST/FULL marked values, CAGR, max drawdown on observed closes, and for TEST the shared paired
  56-day block Sharpe difference vs the corrected btc_hold at the same fee when both series are complete.
  No pass/fail bar is added or changed.
  ADDED AFTER THE FIRST PRIMARY-FEE RUN (documented, not a strategy change): LUNAUSDT's candles stop at 0.00005 on
  2022-05-13 and resume 2022-05-31 at 1.0 as a different asset (Terra 2.0). An outage path holding the old units
  would book a ~20,000x false gain. Guard: a held coin whose first close after a missing-candle gap differs from its
  last close before the gap by more than 100x (or less than 1/100) is an identity break: the run stops INCOMPLETE in
  both modes. The pre-guard primary run is preserved under _superseded_hybrid_parts_pre_identity_guard/."""
import argparse, contextlib, datetime as dt, hashlib, io, json, math, statistics, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.research.corrected_research_math import paired_block_sharpe, rebalance  # noqa: E402

SRC = ROOT / "docs/research/hybrid_momentum_20261009/hybrid.py"
FEES = {"primary_50bps": 0.005, "original_binance_10bps": 0.001, "stress_60bps": 0.006, "stress_120bps": 0.012}
SLIP = 0.0005
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_frozen(data_dir):
    text = SRC.read_text()
    prefix = text[: text.index("\ndef run(")]
    ns = {"__file__": str(SRC), "__name__": "frozen"}
    argv = sys.argv; sys.argv = [str(SRC), str(data_dir)]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(compile(prefix, str(SRC), "exec"), ns)
    finally:
        sys.argv = argv
    O = np.full_like(ns["C"], np.nan)
    for j, s in enumerate(ns["syms"]):
        for ts, o, h, l, c, qv in json.load(open(Path(data_dir) / "bn/d1" / f"{s}.json")):
            i = (ts - ns["D0"]) // 86400
            if 0 <= i < ns["ND"]: O[i, j] = o
    ns["O"] = O
    return ns


def day(ns, i):
    return dt.datetime.fromtimestamp(ns["D0"] + i * 86400, dt.timezone.utc).date().isoformat()


def run(ns, name, L, fee, mode):
    C, O, syms = ns["C"], ns["O"], ns["syms"]
    START, ND = ns["START"], ns["ND"]
    wname = name.rsplit("_", 1)[0] if L else name
    cash, units = 1000.0, {}
    curve = [(START, 1000.0)]; status, stopped = "COMPLETE", None
    # first decision at the original start close (i == START), executed at the next open
    pending = {ns["BTC"]: 1.0} if name == "btc_hold" else ns["weights"](wname, L, START)
    skipped_targets = 0; deferred_days = 0; big_moves = []; last_close = {}; gap_open = {}
    for i in range(START, ND - 1):
        k = i + 1
        # 1) execute a pending rebalance at today's open
        if pending is not None:
            held_missing = [j for j in units if not (np.isfinite(O[k, j]) and O[k, j] > 0)]
            if held_missing:
                if mode == "strict":
                    status, stopped = "INCOMPLETE", f"held {syms[held_missing[0]]} no open {day(ns, k)}"; break
                deferred_days += 1
            else:
                w = {}
                for j, x in pending.items():
                    if np.isfinite(O[k, j]) and O[k, j] > 0: w[j] = x
                    else: skipped_targets += 1
                s = sum(w.values())
                if s > 1: w = {j: x / s for j, x in w.items()}
                prices = {j: float(O[k, j]) for j in set(w) | set(units)}
                cash, new = rebalance(cash, units, prices, w, fee, SLIP)
                units = {j: q for j, q in new.items() if q > 0}
                pending = None
        # 2) mark at today's close; no forward fill
        missing = [j for j in units if not (np.isfinite(C[k, j]) and C[k, j] > 0)]
        for j in units:
            if j not in missing:
                if j in last_close and gap_open.get(j):
                    ratio = C[k, j] / last_close[j]
                    if ratio > 100 or ratio < 0.01:
                        status, stopped = "INCOMPLETE", f"identity break {syms[j]} {day(ns, k)} ratio {ratio:.3g}"
                        break
                last_close[j] = float(C[k, j]); gap_open[j] = False
            else:
                gap_open[j] = True
        if status != "COMPLETE": break
        if missing and mode == "strict":
            status, stopped = "INCOMPLETE", f"held {syms[missing[0]]} no close {day(ns, k)}"; break
        for j in units:
            if np.isfinite(C[k, j]) and np.isfinite(C[i, j]) and C[i, j] > 0 and C[k, j] / C[i, j] - 1 > 5:
                big_moves.append({"coin": syms[j], "day": day(ns, k), "ret_pct": round((C[k, j] / C[i, j] - 1) * 100, 1)})
        nav = None if missing else cash + sum(q * C[k, j] for j, q in units.items())
        curve.append((k, None if nav is None else float(nav)))
        # 3) frozen decision at today's close (Sunday) -> execute next open; btc_hold buys once
        is_sunday = dt.datetime.fromtimestamp(ns["D0"] + k * 86400, dt.timezone.utc).weekday() == 6
        if k < ND - 1 and pending is None and name != "btc_hold" and is_sunday:
            pending = ns["weights"](wname, L, k)
    return {"status": status, "stopped_at": stopped, "targets_skipped_no_open": skipped_targets,
            "rebalance_days_deferred": deferred_days, "held_days_above_500pct": big_moves}, curve


def window_stats(ns, curve, lo_ts, hi_ts):
    pts = [(i, v) for i, v in curve if lo_ts <= ns["D0"] + i * 86400 < hi_ts]
    prior = [v for i, v in curve if ns["D0"] + i * 86400 < lo_ts and v is not None]
    v0 = prior[-1] if prior else 1000.0
    known = [v for _, v in pts if v is not None]
    if not pts or not known: return {"status": "NO_DATA"}
    pk, mdd = v0, 0.0
    for v in known: pk = max(pk, v); mdd = max(mdd, 1 - v / pk)
    yrs = len(pts) / 365
    end = pts[-1][1]
    return {"start_usd": round(v0, 2), "end_marked_usd": None if end is None else round(end, 2),
            "total_pct": None if end is None else round((end / v0 - 1) * 100, 1),
            "cagr_pct": None if end is None or end <= 0 else round(((end / v0) ** (1 / yrs) - 1) * 100, 1),
            "max_drawdown_observed_pct": round(mdd * 100, 1), "unknown_nav_days": sum(1 for _, v in pts if v is None)}


def daily(curve, ns, lo_ts, hi_ts):
    pts = [(i, v) for i, v in curve if lo_ts <= ns["D0"] + i * 86400 < hi_ts]
    return pts


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--fee", choices=list(FEES), required=True)
    a = ap.parse_args()
    ns = load_frozen(a.data)
    T0 = ns["D0"] + ns["START"] * 86400; SPLIT = ns["SPLIT"]; TEND = ns["D1"]
    fee = FEES[a.fee]
    out = {"artifact_type": "research_only_corrected_frozen_hybrid_rerun", "not_promotion_evidence": True,
           "not_independent_holdout": True, "survivorship": "current-listed Binance pairs only (unchanged limitation)",
           "script_sha256": sha(__file__), "shared_math_sha256": sha(ROOT / "scripts/research/corrected_research_math.py"),
           "original_source_sha256": {str(SRC.relative_to(ROOT)): sha(SRC)},
           "input_sha256": {f"bn/d1/{s}.json": sha(Path(a.data) / "bn/d1" / f"{s}.json") for s in ns["syms"]}, "results": {}}
    curves = {}
    for name, L in ns["STRATS"]:
        for mode in ("strict", "outage"):
            meta, curve = run(ns, name, L, fee, mode)
            curves[(name, mode)] = curve
            rec = dict(meta)
            rec.update({"train": window_stats(ns, curve, T0, SPLIT), "test": window_stats(ns, curve, SPLIT, TEND),
                        "full": window_stats(ns, curve, T0, TEND)})
            out["results"][f"{name}|{a.fee}|{mode}"] = rec
    for (name, mode), curve in curves.items():
        rec = out["results"][f"{name}|{a.fee}|{mode}"]
        if name == "btc_hold": continue
        left = daily(curve, ns, SPLIT, TEND); right = daily(curves[("btc_hold", mode)], ns, SPLIT, TEND)
        ok = (rec["status"] == "COMPLETE" and len(left) == len(right) and len(left) >= 113
              and all(v is not None for _, v in left) and all(v is not None for _, v in right))
        if ok:
            lv = [v for _, v in left]; rv = [v for _, v in right]
            try:
                rec["test_block_sharpe_vs_btc"] = paired_block_sharpe([lv[k] / lv[k - 1] - 1 for k in range(1, len(lv))],
                                                                      [rv[k] / rv[k - 1] - 1 for k in range(1, len(rv))])
            except ValueError as e:
                rec["test_block_sharpe_vs_btc"] = {"status": "INCOMPLETE", "reason": str(e)}
        else:
            rec["test_block_sharpe_vs_btc"] = {"status": "INCOMPLETE", "reason": "run incomplete or unknown NAV days in TEST"}
    path = Path(f"{a.out}.part.{a.fee}.json")
    with path.open("x") as fh:
        json.dump(out, fh, allow_nan=False)
    for k, r in out["results"].items():
        print(k, r["status"], r["stopped_at"], "test", r["test"].get("end_marked_usd"), "full", r["full"].get("end_marked_usd"),
              "dd", r["test"].get("max_drawdown_observed_pct"), "unk", r["test"].get("unknown_nav_days"), "big", len(r["held_days_above_500pct"]))


if __name__ == "__main__":
    main()
