"""Versioned diagnostic rerun of the frozen altcoin candidates under the corrected execution contract.
Research only. Does not alter original scripts, results, workbooks, campaigns, accounts or schedules.

WRITTEN BEFORE THE FIRST RUN (2026-10-09). What is frozen and what changes:
  Frozen, unchanged: each study's SELECTED version (chosen by its original TRAIN rule; no re-selection), its signal
  code (executed from the original script, which is hashed), sizing (10% of equity per entry, max 10 positions;
  basket/top-10 weights), trailing-stop and holding-period parameters, TRAIN/TEST windows, original slippage.
  Corrected (same contract as scripts/research/corrected_research_math.py):
    - entries and scheduled exits fill at the NEXT day's open after the signal close, not at the signal close;
    - trailing exits retain the original completed-close trigger against highest close since entry;
      a triggered exit fills at the next observed open, not at a guaranteed stop threshold;
    - a held coin with no candle on a day is NOT forward-filled: strict mode stops the run as INCOMPLETE;
      outage mode (separately labeled) keeps the position, leaves that day's NAV unknown and defers exits to the
      next observed open. A coin with no later candles at all is DELISTED: strict -> INCOMPLETE; scenarios
      'delist_last_close' (original assumption) and 'delist_zero' bound the outcome;
    - weekly-weight portfolios rebalance at the next open with the shared post-cost rebalance() helper.
  Costs: primary 0.50% per side (observed account taker tier, product applicability UNVERIFIED); stress 0.60% and
  1.20%; plus each study's original slippage (0.3% altcoins, 0.1% top-10, 0.05% BTC benchmark).
  Benchmark: BTC bought at the same first open with the same fee, marked at closes.
  Statistics: marked and terminal-liquidated end values, max drawdown on observed closes, and the shared
  paired_block_sharpe (56-day blocks, 2000 repeats, seed 7) of daily returns vs BTC when returns are complete.
  Not rerunnable here: the CMC weekly-proxy study (its prices are CMC aggregates, not exchange prices; only a
  fee-scenario recomputation is reported, labeled as such). The rejected BTC+ETH rule is covered by
  rerun_frozen_majors.py and is not repeated.
No pass/fail bar is changed and none is added: this reports corrected numbers for decisions already made."""
import argparse, datetime as dt, hashlib, json, math, os, statistics, sys, io, contextlib
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.research.corrected_research_math import gap_aware_stop, paired_block_sharpe, rebalance  # noqa: E402

FEES = {"primary_50bps": 0.005, "stress_60bps": 0.006, "stress_120bps": 0.012}
SRC = {
    "recovery": "docs/research/recovery_momentum_20261009/recovery.py",
    "recovery_regime": "docs/research/recovery_momentum_20261009/recovery_regime.py",
    "ideas": "docs/research/three_ideas_20261009/ideas.py",
    "top10": "docs/research/top10_trend_20261009/top10.py",
    "cmc": "docs/research/cmc_trending_20261009/cmc_trend.py",
}
SELECTED = {  # from each study's saved JSON 'selected' field; asserted against it below
    "recovery": {"drop_from_high": 0.7, "momentum_28d": 0.15, "trailing_stop": 0.35, "former_top50": False},
    "recovery_regime": {"drop_from_high": 0.7, "momentum_28d": 0.15, "trailing_stop": 0.35, "former_top50": True, "regime": "exit_all"},
    "new_listings": {"entry_day": 7, "only_if_above_listing_close": True, "hold_days": 30},
    "early_accumulation": {"volume_ratio": 3, "flat_band": 0.1, "trailing_stop": 0.35},
    "small_coin_basket": {"lookback": 28, "volume_rank_band": "51-150"},
}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_frozen(key, data_dir):
    """Execute the original script up to its result loop: frozen arrays and signal functions, unmodified."""
    path = ROOT / SRC[key]
    text = path.read_text()
    prefix = text[: text.index("\nout = {")]
    ns = {"__file__": str(path), "__name__": "frozen"}
    argv = sys.argv; sys.argv = [str(path), str(data_dir)]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(compile(prefix, str(path), "exec"), ns)
    finally:
        sys.argv = argv
    return ns


def load_ohlc(ns, folder):
    """Open and low on the same day index as the frozen close matrix C."""
    O = np.full_like(ns["C"], np.nan); L = np.full_like(ns["C"], np.nan)
    for j, s in enumerate(ns["syms"]):
        for ts, o, h, l, c, qv in json.load(open(f"{folder}/{s}.json")):
            i = (ts - ns["D0"]) // 86400
            if 0 <= i < ns["ND"]: O[i, j] = o; L[i, j] = l
    last = np.full(ns["NS"], -1)
    have = ~np.isnan(ns["C"])
    for j in range(ns["NS"]):
        idx = np.nonzero(have[:, j])[0]
        if len(idx): last[j] = idx[-1]
    return O, L, last


def day(ns, i):
    return dt.datetime.fromtimestamp(ns["D0"] + i * 86400, dt.timezone.utc).date().isoformat()


def summarize(ns, curve, btc_curve, lo):
    """curve: list of (i, marked NAV or None). Stats on observed values only; block test needs completeness."""
    vals = [v for _, v in curve if v is not None]
    pk, mdd = vals[0], 0.0
    for v in vals: pk = max(pk, v); mdd = max(mdd, 1 - v / pk)
    out = {"end_marked_usd": round(vals[-1], 2), "total_pct": round((vals[-1] / 1000 - 1) * 100, 1),
           "max_drawdown_observed_pct": round(mdd * 100, 1), "unknown_nav_days": sum(1 for _, v in curve if v is None)}
    b = dict(btc_curve)
    endpoint = curve[-1][0]
    benchmark_end = b.get(endpoint)
    out["comparison_endpoint_day_index"] = endpoint
    out["btc_end_marked_usd"] = (round(benchmark_end, 2)
                                  if benchmark_end is not None and math.isfinite(benchmark_end) else None)
    pairs = [(curve[k][1], curve[k - 1][1], b.get(curve[k][0]), b.get(curve[k - 1][0])) for k in range(1, len(curve))]
    if all(None not in p for p in pairs) and len(pairs) >= 112:
        left = [a / c - 1 for a, c, _, _ in pairs]; right = [x / y - 1 for _, _, x, y in pairs]
        try:
            out["block_sharpe_vs_btc"] = paired_block_sharpe(left, right)
        except ValueError as e:
            out["block_sharpe_vs_btc"] = {"status": "INCOMPLETE", "reason": str(e)}
    else:
        out["block_sharpe_vs_btc"] = {"status": "INCOMPLETE", "reason": "unknown NAV days or sample < 2 blocks"}
    return out


def btc_bench(ns, O, lo, hi, fee, slip=0.0005):
    b = ns["syms"].index("BTCUSDT")
    units = 1000.0 / (O[lo + 1, b] * (1 + slip)) / (1 + fee)
    return [(lo, 1000.0)] + [(i, units * ns["C"][i, b]) for i in range(lo + 1, hi + 1)]


def event_portfolio(ns, O, L, last, sigfn, keyfn, T, H, fee, slip, lo, hi, mode, regime=None):
    """Frozen close-triggered exits at next open, no forward fill of held coins."""
    C = ns["C"]; cash = 1000.0; pos = {}; pend_in = {}; pend_out = set(); trades = []; curve = [(lo, 1000.0)]
    skipped_entries = 0; status = "COMPLETE"; note = None
    for k in range(lo + 1, hi + 1):
        if mode == "strict":
            missing = next((j for j in pos if not np.isfinite(O[k, j])
                            or O[k, j] <= 0 or not np.isfinite(C[k, j]) or C[k, j] <= 0), None)
            if missing is not None:
                status, note = "INCOMPLETE", f"missing candle held {ns['syms'][missing]} {day(ns, k)}"
                break
        # 1) scheduled exits at today's open
        for j in list(pend_out):
            if np.isnan(O[k, j]):
                if last[j] < k: status, note = "INCOMPLETE", f"delisted held {ns['syms'][j]} {day(ns, k)}"; break
                continue  # outage: defer to next observed open
            p = pos.pop(j); got = p["q"] * O[k, j] * (1 - slip) * (1 - fee); cash += got; pend_out.discard(j)
            trades.append({"coin": ns["syms"][j], "in": day(ns, p["in"]), "out": day(ns, k), "ret": got / p["cost"] - 1, "why": p["why"]})
        if status != "COMPLETE": break
        # 2) scheduled entries at today's open
        for j, usd in list(pend_in.items()):
            del pend_in[j]
            if (not np.isfinite(O[k, j]) or O[k, j] <= 0
                    or not np.isfinite(C[k - 1, j]) or C[k - 1, j] <= 0):
                cash += usd; skipped_entries += 1; continue
            px = O[k, j]; pos[j] = {"q": usd / (1 + fee) / (px * (1 + slip)), "cost": usd, "in": k, "entry": px, "peak": C[k - 1, j], "why": None}
        # 3) original completed-close exit decisions, executed next open
        for j in list(pos):
            if j in pend_out: continue
            if np.isnan(C[k, j]):
                if last[j] < k:
                    status, note = "INCOMPLETE", f"delisted held {ns['syms'][j]} {day(ns, k)}"; break
                if mode == "strict": status, note = "INCOMPLETE", f"missing candle held {ns['syms'][j]} {day(ns, k)}"; break
                continue
            p = pos[j]
            p["peak"] = max(p["peak"], C[k, j])
            if T and C[k, j] <= p["peak"] * (1 - T):
                p["why"] = "stop_close_next_open"; pend_out.add(j)
            elif k - p["in"] >= H: p["why"] = "time"; pend_out.add(j)
        if status != "COMPLETE": break
        # 4) regime exit decided at today's close
        if regime is not None and regime.get("exit_all") and not regime["up"][k]:
            for j in pos:
                if j not in pend_out: pos[j]["why"] = "regime"; pend_out.add(j)
        # 5) mark at close (unknown if any held coin lacks today's close)
        marks = [pos[j]["q"] * C[k, j] for j in pos]
        nav = None if any(np.isnan(m) for m in marks) else cash + sum(pend_in.values()) + float(sum(marks))
        curve.append((k, nav))
        # 6) signals at today's close -> orders for next open
        if k < hi and len(pos) + len(pend_in) < 10 and (regime is None or regime["up"][k]) and nav is not None:
            for j in sorted(sigfn(k), key=lambda j: -keyfn(k, j)):
                if len(pos) + len(pend_in) >= 10 or j in pos or j in pend_in: continue
                usd = min(cash, nav * 0.10)
                if usd < 1: break
                pend_in[j] = usd; cash -= usd
    res = {"status": status, "stopped_at": note, "trades": len(trades), "entries_cancelled_no_open": skipped_entries,
           "stop_exits": sum(t["why"] == "stop_close_next_open" for t in trades)}
    if trades:
        rs = [t["ret"] for t in trades]
        res.update({"win_pct": round(100 * sum(r > 0 for r in rs) / len(rs), 1), "mean_trade_pct": round(statistics.mean(rs) * 100, 2),
                    "median_trade_pct": round(statistics.median(rs) * 100, 2),
                    "best_trades": sorted(trades, key=lambda t: -t["ret"])[:5]})
        for t in res["best_trades"]: t["ret"] = round(t["ret"] * 100, 1)
    # terminal liquidation at last close with costs (no later open in the archive): labeled approximation
    if status == "COMPLETE":
        k = hi; liq = cash + sum(pend_in.values()) + sum(p["q"] * C[k, j] * (1 - slip) * (1 - fee) for j, p in pos.items())
        res["terminal_liquidated_at_last_close_usd"] = round(float(liq), 2)
    return res, curve


def weight_portfolio(ns, O, last, target_fn, rebal_days, fee, slip, lo, hi, delist):
    """Weights decided at close of a rebalance day, executed at next open via shared rebalance()."""
    C = ns["C"]; cash = 1000.0; units = {}; curve = [(lo, 1000.0)]; status = "COMPLETE"; note = None; delisted_events = []
    pending = target_fn(lo) if lo in rebal_days else None
    for k in range(lo + 1, hi + 1):
        # delisting / missing candle of held coins
        for j in list(units):
            if np.isnan(C[k, j]):
                if last[j] < k:
                    if delist == "strict": status, note = "INCOMPLETE", f"delisted held {ns['syms'][j]} {day(ns, k)}"; break
                    rec = C[last[j], j] * (1 - slip) * (1 - fee) if delist == "delist_last_close" else 0.0
                    cash += units.pop(j) * rec; delisted_events.append(ns["syms"][j])
                else:
                    status, note = "INCOMPLETE", f"missing candle held {ns['syms'][j]} {day(ns, k)}"; break
        if status != "COMPLETE": break
        if pending is not None:
            w = {j: x for j, x in pending.items() if not np.isnan(O[k, j]) and O[k, j] > 0}
            prices = {j: O[k, j] for j in set(w) | set(units)}
            if any(np.isnan(p) for p in prices.values()): status, note = "INCOMPLETE", f"held coin no open {day(ns, k)}"; break
            s = sum(w.values())
            if s > 1: w = {j: x / s for j, x in w.items()}
            cash_after, new_units = rebalance(cash, units, prices, w, fee, slip)
            cash = cash_after; units = {j: q for j, q in new_units.items() if q > 0}
            pending = None
        nav = cash + sum(q * C[k, j] for j, q in units.items())
        curve.append((k, float(nav)))
        if k in rebal_days and k < hi: pending = target_fn(k)
    res = {"status": status, "stopped_at": note, "delisted_while_held": delisted_events}
    if status == "COMPLETE":
        res["terminal_liquidated_at_last_close_usd"] = round(float(cash + sum(q * C[hi, j] * (1 - slip) * (1 - fee) for j, q in units.items())), 2)
    return res, curve


def group_recovery(D, out, inputs):
    # --- recovery and recovery_regime (bn/d1, current-listed pairs) ---
    for key in ("recovery", "recovery_regime"):
        ns = load_frozen(key, D)
        saved = json.load(open(ROOT / SRC[key].replace(".py", ".json")))["selected"]
        assert saved == SELECTED[key], (key, saved)
        O, L, last = load_ohlc(ns, D / "bn/d1"); s = SELECTED[key]
        sig = lambda i, s=s, ns=ns: ns["signal"](i, s["drop_from_high"], s["momentum_28d"], s["former_top50"])
        key_fn = lambda i, j, ns=ns: ns["R28"][i, j]
        regime = {"up": ns["MKT_UP"], "exit_all": s["regime"] == "exit_all"} if key == "recovery_regime" else None
        out["results"][key] = {}
        for part, (lo, hi) in (("train", ns["TRAIN"]), ("test", ns["TEST"])):
            for fname, fee in FEES.items():
                for mode in ("strict", "outage"):
                    r, c = event_portfolio(ns, O, L, last, sig, key_fn, s["trailing_stop"], 180, fee, 0.003, lo, hi, mode, regime)
                    r.update(summarize(ns, c, btc_bench(ns, O, lo, hi, fee), lo))
                    out["results"][key][f"{part}|{fname}|{mode}"] = r
        inputs["bn/d1"] = {f: sha(D / "bn/d1" / f) for f in sorted(os.listdir(D / "bn/d1"))}


def group_ideas(D, out, inputs):
    # --- ideas: new listings, accumulation (event), small-coin basket (weights) ---
    ns = load_frozen("ideas", D); O, L, last = load_ohlc(ns, D / "bn/d1")
    inputs["bn/d1"] = {f: sha(D / "bn/d1" / f) for f in sorted(os.listdir(D / "bn/d1"))}
    saved = json.load(open(ROOT / "docs/research/three_ideas_20261009/ideas.json"))["ideas"]
    for idea in ("new_listings", "early_accumulation", "small_coin_basket"):
        assert saved[idea]["selected"] == SELECTED[idea], (idea, saved[idea]["selected"])
    TRAIN, TEST = ns["TRAIN"], ns["TEST"]
    s = SELECTED["new_listings"]
    nl_sig = ns["listing_sig"](s["entry_day"], s["only_if_above_listing_close"])
    nl_key = lambda i, j: ns["V30"][i, j] if not np.isnan(ns["V30"][i, j]) else ns["QV"][i, j]
    s2 = SELECTED["early_accumulation"]; ac_sig = ns["accum_sig"](s2["volume_ratio"], s2["flat_band"])
    for idea, sigf, keyf, T, H in (("new_listings", nl_sig, nl_key, None, s["hold_days"]), ("early_accumulation", ac_sig, ns["accum_key"], s2["trailing_stop"], 90)):
        out["results"][idea] = {}
        for part, (lo, hi) in (("train", TRAIN), ("test", TEST)):
            for fname, fee in FEES.items():
                for mode in ("strict", "outage"):
                    r, c = event_portfolio(ns, O, L, last, sigf, keyf, T, H, fee, 0.003, lo, hi, mode)
                    r.update(summarize(ns, c, btc_bench(ns, O, lo, hi, fee), lo))
                    out["results"][idea][f"{part}|{fname}|{mode}"] = r
    # basket: frozen weight rule copied from ideas.py basket() (L=28, ranks 51-150), rebalance every 7 days from lo
    s3 = SELECTED["small_coin_basket"]; Lb = s3["lookback"]; rlo, rhi = 51, 150
    RL = np.full_like(ns["P"], np.nan); RL[Lb:] = ns["P"][Lb:] / ns["P"][:-Lb] - 1
    def basket_target(i):
        with np.errstate(invalid="ignore", divide="ignore"):
            ok = (ns["AGE"][i] >= 365) & ~np.isnan(ns["C"][i]) & (ns["RANK"][i] >= rlo - 1) & (ns["RANK"][i] <= rhi - 1) & (RL[i] > 0) & (ns["C"][i] > ns["SMA50"][i]) & (ns["VOL30"][i] > 0)
            nw = np.where(ok, np.minimum(0.05, 0.004 / ns["VOL30"][i]), 0.0)
        nw = np.nan_to_num(nw)
        if nw.sum() > 1: nw /= nw.sum()
        return {int(j): float(nw[j]) for j in np.nonzero(nw > 0)[0]}
    out["results"]["small_coin_basket"] = {}
    for part, (lo, hi) in (("train", TRAIN), ("test", TEST)):
        rd = set(range(lo, hi + 1, 7))
        for fname, fee in FEES.items():
            r, c = weight_portfolio(ns, O, last, basket_target, rd, fee, 0.003, lo, hi, "strict")
            r.update(summarize(ns, c, btc_bench(ns, O, lo, hi, fee), lo))
            out["results"]["small_coin_basket"][f"{part}|{fname}|strict"] = r


def group_top10(D, out, inputs):
    # --- top-10 trend (bn_all incl. delisted), N=10, Sunday close -> Monday open ---
    ns = load_frozen("top10", D); O, L, last = load_ohlc(ns, D / "bn_all/d1")
    inputs["bn_all/d1"] = {f: sha(D / "bn_all/d1" / f) for f in sorted(os.listdir(D / "bn_all/d1"))}
    out["results"]["top10_trend"] = {}
    for wn, (lo, hi) in ns["WIN"].items():
        rd = {i for i in range(lo, hi + 1) if ns["SUN"][i]} | {lo}
        for fname, fee in FEES.items():
            for dpol in ("strict", "delist_last_close", "delist_zero"):
                r, c = weight_portfolio(ns, O, last, lambda i: ns["target"]("topn_trend", 10, i), rd, fee, 0.001, lo, hi, dpol)
                r.update(summarize(ns, c, btc_bench(ns, O, lo, hi, fee), lo))
                out["results"]["top10_trend"][f"{wn}|{fname}|{dpol}"] = r


def group_cmc(D, out, inputs):
    # --- CMC proxy: fee-scenario recomputation only (CMC aggregate prices, NOT the corrected execution contract) ---
    ns = load_frozen("cmc", D)
    sel = json.load(open(ROOT / "docs/research/cmc_trending_20261009/cmc_trend.json"))["selected"]
    out["results"]["cmc_proxy_fee_only"] = {"note": "CMC aggregate snapshot prices; not executable; only the fee is changed", "selected": sel}
    for part, (lo, hi) in (("train", ns["TRAIN"]), ("test", ns["TEST"])):
        for fname, fee in FEES.items():
            curve, _, miss = ns["run"](sel["signal"], sel["hold_weeks"], sel["regime"], fee, lo, hi)
            out["results"]["cmc_proxy_fee_only"][f"{part}|{fname}"] = {"end_usd": round(curve[-1][1], 2), "picks_missing_at_exit": miss}
    inputs["cmc/weekly"] = {f: sha(D / "cmc/weekly" / f) for f in sorted(os.listdir(D / "cmc/weekly"))}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--only", choices=["recovery", "ideas", "top10", "cmc", "merge"], required=True,
                    help="run one study group per process (each writes <out>.<only>.json); merge combines them")
    a = ap.parse_args()
    if a.only == "merge":
        parts = {g: json.load(open(f"{a.out}.{g}.json")) for g in ("recovery", "ideas", "top10", "cmc")}
        base = parts["recovery"]; base["results"] = {}; base["input_sha256"] = {}
        for g, d in parts.items():
            assert d["script_sha256"] == base["script_sha256"], g
            base["results"].update(d["results"]); base["input_sha256"].update(d["input_sha256"])
        Path(a.out).write_text(json.dumps(base)); print("merged", list(base["results"])); return
    D = Path(a.data)
    out = {"artifact_type": "research_only_corrected_frozen_altcoin_rerun", "not_promotion_evidence": True,
           "not_independent_holdout": True, "script_sha256": sha(__file__),
           "shared_math_sha256": sha(ROOT / "scripts/research/corrected_research_math.py"),
           "original_source_sha256": {k: sha(ROOT / v) for k, v in SRC.items()}, "results": {}}
    inputs = {}
    {"recovery": group_recovery, "ideas": group_ideas, "top10": group_top10, "cmc": group_cmc}[a.only](D, out, inputs)
    out["input_sha256"] = inputs
    Path(f"{a.out}.{a.only}.json").write_text(json.dumps(out, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    print(json.dumps({k: {kk: {x: vv.get(x) for x in ("status", "end_marked_usd", "btc_end_marked_usd", "max_drawdown_observed_pct", "trades", "unknown_nav_days", "stopped_at", "end_usd")} if isinstance(vv, dict) else vv
                          for kk, vv in v.items() if kk != "note"} for k, v in out["results"].items()}, indent=0, default=str)[:20000])


if __name__ == "__main__":
    main()
