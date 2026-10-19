"""EXPLORATORY (post-hoc) rerun of the registered BTC+ETH stress robustness checks at the observed 0.50% taker tier.
Authorized by the operator 2026-10-11. Written BEFORE the first run. Research only; not promotion or confirmatory evidence.

Why: the registered primary cost was 1.2%/side (then believed to be Coinbase taker); the observed account tier is 0.50%.
The registered verdict (REJECT, at 1.2%) stands and is not replaced by this analysis.

Changed: fee 0.012 -> 0.005 per side, everywhere the registered study used 0.012. NOTHING ELSE:
  same data (hash-checked), same corrected execution (decide at close, trade next open; frozen
  scripts/research/rerun_frozen_stress.py imported unmodified, hash-checked), 0.05% slippage, periods A/B/C/FULL,
  baseline L=28 V=50% Sunday, the same 13 one-at-a-time variants, same 105-setting grid, same benchmarks (hold BTC;
  fixed BTC/ETH mix at the rule's own average exposure), same Required 1 / Required 2 / reject logic, same bootstrap
  (weekly returns, blocks 4/8/13, 5,000 resamples, seed 7).
Reported: every variant and every grid cell, losers included. No tuning; the best cell is not promoted.
Harness check: baseline at 0.5% must reproduce stress_corrected_v1.json baseline["0.005"] exactly, else abort.
Reading rule (fixed now): a "pass" here can only justify further research (Scenario 2 candidate), not a profitability
claim, capital, or a change to the frozen paper test.
Usage: python3 -B stress_fee050_exploratory.py --data DIR_WITH_maj/ --out result.json"""
import argparse, hashlib, json, math, random, statistics, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
FROZEN = ROOT / "scripts/research/rerun_frozen_stress.py"
STORED = ROOT / "research/research_corrections_20261009/stress_corrected_v1.json"
EXPECT = {"frozen_script": "1f98513ae63c4f84819327746872a9dd0a73b3bc35e5e67364c57458ca395907",
          "maj/BTC-USD_d1.json": "64cab2cf912244babb251485a9949a266be30fb80840e95b80d4478a9cde07c0",
          "maj/ETH-USD_d1.json": "9fa81ca8395321dddc5453a2144b5081ada012e74ed3132c9c2c039e5e6206b8"}
FEE = 0.005

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    got = {"frozen_script": sha(FROZEN), **{k: sha(Path(a.data) / k) for k in EXPECT if k.startswith("maj/")}}
    if got != EXPECT: raise SystemExit(f"hash mismatch: {got}")
    from scripts.research.rerun_frozen_stress import load_frozen, evaluate
    ns = load_frozen(a.data); PER = ns["PER"]
    out = {"artifact_type": "research_only_EXPLORATORY_post_hoc_fee_sensitivity", "not_confirmatory": True,
           "not_promotion_evidence": True, "registered_verdict_unchanged": "reject (at 1.2%)", "fee_per_side": FEE,
           "slippage": 0.0005, "script_sha256": sha(__file__), "inputs_sha256": got,
           "stored_reference_sha256": sha(STORED)}
    base = {p: evaluate(ns, lo, hi, FEE)[0] for p, (lo, hi) in PER.items()}
    if base != json.load(open(STORED))["baseline"]["0.005"]: raise SystemExit("harness check failed: baseline differs from stored")
    out["harness_check"] = "baseline at 0.5% reproduces stored stress_corrected_v1 exactly"
    out["baseline"] = base
    beats = lambda p: all(base[p]["rule"]["max_drawdown_pct"] < base[p][x]["max_drawdown_pct"] and base[p]["rule"]["sharpe"] > base[p][x]["sharpe"] for x in ("hold_btc", "fixed_mix"))
    r1 = {p: beats(p) for p in ("A", "B", "C")}
    out["required_1"] = {"by_period": r1, "passes": bool(r1["A"] and sum(r1.values()) >= 2)}
    VARS = [("lookback", {"L": L}) for L in (14, 21, 42, 56)] + [("vol_target", {"V": V}) for V in (0.30, 0.70)] + \
           [("weekday", {"wd": d}) for d in (0, 1, 2, 3, 4, 5)] + [("btc_only", {"assets": ("BTC",)})]
    out["variants"] = []
    for name, kw in VARS:
        res = {p: evaluate(ns, lo, hi, FEE, **kw)[0] for p, (lo, hi) in PER.items()}
        out["variants"].append({"change": name, "setting": {k: (list(v) if isinstance(v, tuple) else v) for k, v in kw.items()},
                                "results": res, "beats_fixed_mix_full_sharpe": res["FULL"]["rule"]["sharpe"] > res["FULL"]["fixed_mix"]["sharpe"]})
    n2 = sum(v["beats_fixed_mix_full_sharpe"] for v in out["variants"])
    out["required_2"] = {"variants_beating": n2, "of": len(VARS), "passes": n2 >= 10}
    lo, hi = PER["FULL"]; _, c, m = evaluate(ns, lo, hi, FEE)
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
    grid = []
    for L in (14, 21, 28, 42, 56):
        for V in (0.30, 0.50, 0.70):
            for d in range(7):
                r = evaluate(ns, lo, hi, FEE, L=L, V=V, wd=d)[0]
                grid.append({"L": L, "V": V, "weekday": d, "rule_sharpe": r["rule"]["sharpe"], "fixed_mix_sharpe": r["fixed_mix"]["sharpe"],
                             "rule_mdd": r["rule"]["max_drawdown_pct"], "fixed_mix_mdd": r["fixed_mix"]["max_drawdown_pct"],
                             "rule_cagr": r["rule"]["cagr_pct"], "fixed_mix_cagr": r["fixed_mix"]["cagr_pct"]})
    out["combined_grid"] = {"rows": grid, "share_beating_fixed_mix_sharpe_pct": round(100 * sum(g["rule_sharpe"] > g["fixed_mix_sharpe"] for g in grid) / len(grid), 1),
                            "share_beating_fixed_mix_sharpe_and_mdd_pct": round(100 * sum(g["rule_sharpe"] > g["fixed_mix_sharpe"] and g["rule_mdd"] < g["fixed_mix_mdd"] for g in grid) / len(grid), 1)}
    fb = base["FULL"]
    reject = not (fb["rule"]["sharpe"] > fb["fixed_mix"]["sharpe"])
    out["exploratory_verdict_same_rules"] = "reject" if reject else ("continue_paper_validation" if out["required_1"]["passes"] and out["required_2"]["passes"]
                                            else ("keep_researching" if out["required_1"]["passes"] or out["required_2"]["passes"] else "reject"))
    with open(a.out, "x") as fh: json.dump(out, fh, indent=1, allow_nan=False)
    print(json.dumps({k: out[k] for k in ("harness_check", "required_1", "required_2", "bootstrap", "exploratory_verdict_same_rules")}, indent=1))
    print("grid", out["combined_grid"]["share_beating_fixed_mix_sharpe_pct"], out["combined_grid"]["share_beating_fixed_mix_sharpe_and_mdd_pct"])
    for v in out["variants"]: print(v["change"], v["setting"], v["results"]["FULL"]["rule"]["sharpe"], v["results"]["FULL"]["fixed_mix"]["sharpe"], v["beats_fixed_mix_full_sharpe"])

if __name__ == "__main__": main()
