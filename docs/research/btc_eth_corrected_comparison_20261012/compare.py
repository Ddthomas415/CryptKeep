"""Corrected BTC/ETH trend comparison, 2026-10-12. Written BEFORE running. Research only.
Responds to the review of xs_momentum_20261012: the BTC/ETH figures there came from a new simulator that filled missing
candles with the last close. This script does NOT use that simulator. It imports the already reviewed, hash-checked corrected
harness (scripts/research/rerun_frozen_stress.py): decide at the Sunday close, trade at the NEXT day's OPEN, mark at closes. It
refuses to run on non-contiguous data. Inputs are the hash-checked majors daily files.
Frozen rule (unchanged): 28-day trend, vol-sized to 50%, weekly Sunday decision, BTC+ETH. No parameter changes.
Benchmarks, all with identical execution and costs (fee + 0.05% slippage per side on traded value, entry included):
  hold_btc; fixed_mix_matched (50/50 at the rule's own average exposure, hindsight given to the benchmark);
  fixed_mix_50 (50/50 at a constant 50% exposure, no hindsight); cash ($1,000, 0%).
Fees: 0.50% (observed taker tier, primary), 0.60%, 1.20% (registered stress primary).
Periods: the registered A/B/C/FULL, plus 2018-01-01..end to reconcile the xs_momentum table.
Output: comparison_result.json. Nothing here changes the registered REJECT verdict (1.2%) or any tracker."""
import hashlib, json, statistics, sys, datetime as dt
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECT = {"scripts/research/rerun_frozen_stress.py": "1f98513ae63c4f84819327746872a9dd0a73b3bc35e5e67364c57458ca395907",
          "docs/research/majors_trend_20261009/BTC-USD_d1.json": "64cab2cf912244babb251485a9949a266be30fb80840e95b80d4478a9cde07c0",
          "docs/research/majors_trend_20261009/ETH-USD_d1.json": "9fa81ca8395321dddc5453a2144b5081ada012e74ed3132c9c2c039e5e6206b8"}
got = {k: sha(ROOT / k) for k in EXPECT}
if got != EXPECT: raise SystemExit(f"hash mismatch {got}")
from scripts.research.rerun_frozen_stress import load_frozen, run
ns = load_frozen(sys.argv[1]); days = ns["days"]; st = ns["stats"]
def ix(lo, hi):
    ts = lambda s: int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())
    return next(i for i, d in enumerate(days) if d >= ts(lo)), max(i for i, d in enumerate(days) if d <= ts(hi))
PER = dict(ns["PER"]); PER["S2018"] = ix("2018-01-01", "2026-10-08")
out = {"artifact_type": "research_only_corrected_comparison", "not_promotion_evidence": True, "inputs_sha256": got,
       "script_sha256": sha(__file__), "periods": {k: [str(dt.date.fromtimestamp(days[a])), str(dt.date.fromtimestamp(days[b]))] for k, (a, b) in PER.items()}, "results": {}}
for fee in (0.005, 0.006, 0.012):
    R = out["results"][str(fee)] = {}
    for p, (lo, hi) in PER.items():
        c, e = run(ns, "rule", lo, hi, fee=fee)
        m, _ = run(ns, "fixed_mix", lo, hi, fee=fee, expo=e)
        f50, _ = run(ns, "fixed_mix", lo, hi, fee=fee, expo=0.5)
        h, _ = run(ns, "hold_btc", lo, hi, fee=fee)
        R[p] = {"rule": {**st(c), "avg_exposure_pct": round(e * 100, 1)}, "fixed_mix_matched": st(m), "fixed_mix_50": st(f50),
                "hold_btc": st(h), "cash": {"end_usd": 1000.0, "cagr_pct": 0.0, "max_drawdown_pct": 0.0, "sharpe": 0.0}}
stored = json.load(open(ROOT / "research/research_corrections_20261009/stress_corrected_v1.json"))["baseline"]
out["harness_check_vs_stored_stress_corrected_v1"] = all(out["results"][f][p][k] == {kk: vv for kk, vv in stored[f][p][k].items()}
    for f in ("0.005", "0.006", "0.012") for p in ("A", "B", "C", "FULL") for k in ("hold_btc",)) and \
    all(out["results"][f][p]["rule"] == stored[f][p]["rule"] for f in ("0.005", "0.006", "0.012") for p in ("A", "B", "C", "FULL"))
json.dump(out, open(Path(__file__).parent / "comparison_result.json", "x"), indent=1)
print("harness reproduces stored corrected stress results:", out["harness_check_vs_stored_stress_corrected_v1"])
for f in ("0.005", "0.012"):
    for p in ("A", "B", "C", "FULL", "S2018"):
        r = out["results"][f][p]
        print(f, p, " | ".join(f"{k}: ${v['end_usd']:,.0f} {v['cagr_pct']}%/yr SR {v['sharpe']} DD {v['max_drawdown_pct']}%" for k, v in r.items() if k != "cash"))
