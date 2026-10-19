"""Versioned diagnostic rerun of the BTC+ETH stress test (btc_eth_stress_test_20261009/stress_btc_eth.py) under the
corrected execution contract. Research only; the original script, JSON, verdict and workbook are unchanged.

WRITTEN BEFORE THE FIRST RUN (2026-10-09):
  Frozen, unchanged: the study's registered rules - periods A/B/C/FULL, baseline (L=28, V=50%, Sunday), the 13
  one-at-a-time variants, the 105-setting grid, benchmarks (hold BTC; fixed BTC/ETH mix at the rule's own average
  exposure, hindsight given to the benchmark; BTC-only), Required 1 / Required 2 / reject logic, the weekly-return
  block bootstrap (blocks 4/8/13 weeks, 5,000 resamples, seed 7), the registered PRIMARY cost of 1.2% + 0.05%
  slippage, and the target-weight function executed from the hashed original source.
  Corrected: a decision at day i's close is executed at day i+1's OPEN (stored rows are [time, open, high, low,
  close, volume]) using the shared post-cost rebalance() helper, instead of trading at the deciding close;
  positions are marked at closes. Both assets trade every day in these periods (checked: contiguous).
  Reported in addition, labeled as sensitivity only: 0.50% (observed account taker tier) and 0.60%.
  The verdict is recomputed with the original rules at the registered 1.2% primary cost."""
import argparse, contextlib, datetime as dt, hashlib, io, json, math, random, statistics, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.research.corrected_research_math import rebalance  # noqa: E402

SRC = ROOT / "docs/research/btc_eth_stress_test_20261009/stress_btc_eth.py"
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_frozen(data_dir):
    text = SRC.read_text()
    prefix = text[: text.index("\ndef run(")]
    stats_src = text[text.index("\ndef stats("): text.index("\ndef evaluate(")]
    ns = {"__file__": str(SRC), "__name__": "frozen"}
    argv = sys.argv; sys.argv = [str(SRC), str(data_dir)]
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            exec(compile(prefix + stats_src, str(SRC), "exec"), ns)
    finally:
        sys.argv = argv
    raw = {a: {r[0]: r for r in json.load(open(Path(data_dir) / "maj" / f"{a}-USD_d1.json"))} for a in ("BTC", "ETH")}
    ns["OPEN"] = {a: [float(raw[a][d][1]) for d in ns["days"]] for a in raw}
    days = ns["days"]
    lo = ns["PER"]["FULL"][0] - 60
    if any(days[k + 1] - days[k] != 86400 for k in range(lo, ns["PER"]["FULL"][1])):
        raise ValueError("non-contiguous daily data inside the study periods")
    return ns


def run(ns, kind, lo, hi, L=28, V=0.5, wd=6, assets=("BTC", "ETH"), fee=0.012, slip=0.0005, expo=None):
    """Decide at close i (frozen target), trade at open i+1, mark at closes."""
    P, O, WD = ns["P"], ns["OPEN"], ns["WD"]
    cash, units = 1000.0, {}
    curve = [1000.0]; ex = []
    pending = ns["target"](kind, lo, L, V, assets, expo)
    for k in range(lo + 1, hi + 1):
        if pending is not None:
            prices = {a: O[a][k] for a in ("BTC", "ETH")}
            cash, units = rebalance(cash, units, prices, pending, fee, slip)
            pending = None
        nav = cash + sum(q * P[a][k] for a, q in units.items())
        curve.append(nav); ex.append(sum(q * P[a][k] for a, q in units.items()) / nav if nav > 0 else 0.0)
        if k < hi and kind != "hold_btc" and WD[k] == wd:
            pending = ns["target"](kind, k, L, V, assets, expo)
    return curve, statistics.mean(ex)


def evaluate(ns, lo, hi, fee, **kw):
    c, e = run(ns, "rule", lo, hi, fee=fee, **kw)
    m, _ = run(ns, "fixed_mix", lo, hi, wd=kw.get("wd", 6), fee=fee, expo=e)
    h, _ = run(ns, "hold_btc", lo, hi, fee=fee)
    st = ns["stats"]
    return {"rule": {**st(c), "avg_exposure_pct": round(e * 100, 1)}, "fixed_mix": st(m), "hold_btc": st(h)}, c, m


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--part", choices=["core", "grid"], required=True)
    a = ap.parse_args()
    ns = load_frozen(a.data); PER = ns["PER"]
    out = {"artifact_type": "research_only_corrected_frozen_stress_rerun", "not_promotion_evidence": True,
           "not_independent_holdout": True, "script_sha256": sha(__file__),
           "shared_math_sha256": sha(ROOT / "scripts/research/corrected_research_math.py"),
           "original_source_sha256": {str(SRC.relative_to(ROOT)): sha(SRC)},
           "input_sha256": {f"maj/{x}-USD_d1.json": sha(Path(a.data) / "maj" / f"{x}-USD_d1.json") for x in ("BTC", "ETH")}}
    if a.part == "core":
        out["baseline"] = {str(f): {p: evaluate(ns, lo, hi, f)[0] for p, (lo, hi) in PER.items()} for f in (0.012, 0.005, 0.006)}
        b = out["baseline"]["0.012"]
        beats = lambda p: all(b[p]["rule"]["max_drawdown_pct"] < b[p][x]["max_drawdown_pct"] and b[p]["rule"]["sharpe"] > b[p][x]["sharpe"] for x in ("hold_btc", "fixed_mix"))
        r1 = {p: beats(p) for p in ("A", "B", "C")}
        out["required_1"] = {"by_period": r1, "passes": bool(r1["A"] and sum(r1.values()) >= 2)}
        VARS = [("lookback", {"L": L}) for L in (14, 21, 42, 56)] + [("vol_target", {"V": V}) for V in (0.30, 0.70)] + \
               [("weekday", {"wd": d}) for d in (0, 1, 2, 3, 4, 5)] + [("btc_only", {"assets": ("BTC",)})]
        out["variants"] = []
        for name, kw in VARS:
            res = {p: evaluate(ns, lo, hi, 0.012, **kw)[0] for p, (lo, hi) in PER.items()}
            out["variants"].append({"change": name, "setting": {k: (list(v) if isinstance(v, tuple) else v) for k, v in kw.items()},
                                    "results": res, "beats_fixed_mix_full_sharpe": res["FULL"]["rule"]["sharpe"] > res["FULL"]["fixed_mix"]["sharpe"]})
        n2 = sum(v["beats_fixed_mix_full_sharpe"] for v in out["variants"])
        out["required_2"] = {"variants_beating": n2, "of": len(VARS), "passes": n2 >= 10}
        lo, hi = PER["FULL"]; _, c, m = evaluate(ns, lo, hi, 0.012)
        wk = lambda cur: [cur[k + 7] / cur[k] - 1 for k in range(0, len(cur) - 7, 7)]
        wr, wm = wk(c), wk(m)
        def sh(x): s = statistics.pstdev(x); return statistics.mean(x) / s * math.sqrt(52.18) if s else 0
        out["bootstrap"] = {"observed_weekly_sharpe_diff": round(sh(wr) - sh(wm), 3), "weeks": len(wr)}
        rng = random.Random(7)
        for blk in (4, 8, 13):
            diffs = []; n = len(wr)
            for _ in range(5000):
                ii = []
                while len(ii) < n:
                    s0 = rng.randrange(0, n - blk + 1); ii.extend(range(s0, s0 + blk))
                ii = ii[:n]; diffs.append(sh([wr[j] for j in ii]) - sh([wm[j] for j in ii]))
            diffs.sort()
            out["bootstrap"][f"block_{blk}w"] = {"p05": round(diffs[250], 3), "p50": round(diffs[2500], 3), "p95": round(diffs[4750], 3),
                                                 "share_above_zero_pct": round(100 * sum(d > 0 for d in diffs) / 5000, 1)}
        fb = b["FULL"]
        reject = not (fb["rule"]["sharpe"] > fb["fixed_mix"]["sharpe"])
        out["verdict"] = "reject" if reject else ("continue_paper_validation" if out["required_1"]["passes"] and out["required_2"]["passes"]
                         else ("keep_researching" if out["required_1"]["passes"] or out["required_2"]["passes"] else "reject"))
    else:
        lo, hi = PER["FULL"]; grid = []
        for L in (14, 21, 28, 42, 56):
            for V in (0.30, 0.50, 0.70):
                for d in range(7):
                    r = evaluate(ns, lo, hi, 0.012, L=L, V=V, wd=d)[0]
                    grid.append({"L": L, "V": V, "weekday": d, "rule_sharpe": r["rule"]["sharpe"], "fixed_mix_sharpe": r["fixed_mix"]["sharpe"]})
        out["combined_grid"] = {"rows": grid, "share_beating_fixed_mix_sharpe_pct": round(100 * sum(g["rule_sharpe"] > g["fixed_mix_sharpe"] for g in grid) / len(grid), 1)}
    with Path(f"{a.out}.part.{a.part}.json").open("x") as fh:
        json.dump(out, fh, allow_nan=False)
    if a.part == "core":
        print("R1", out["required_1"], "R2", out["required_2"], "verdict", out["verdict"], "boot8", out["bootstrap"]["block_8w"])
        for f, R in out["baseline"].items():
            for p, r in R.items():
                print(f, p, {k: (v["end_usd"], v["max_drawdown_pct"], v["sharpe"]) for k, v in r.items()})
        print([(v["change"], v["setting"], v["results"]["FULL"]["rule"]["sharpe"], v["results"]["FULL"]["fixed_mix"]["sharpe"]) for v in out["variants"]])
    else:
        print("grid share", out["combined_grid"]["share_beating_fixed_mix_sharpe_pct"])


if __name__ == "__main__":
    main()
