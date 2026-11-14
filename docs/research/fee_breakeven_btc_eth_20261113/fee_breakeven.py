"""Fee break-even for the frozen BTC+ETH 28-day trend rule. Claude (Cowork), 2026-11-13. WRITTEN BEFORE RUNNING.
Research only, exploratory. Owner request: real work that advances the project; execution cost is the active focus
(owner direction 2026-11-12, option C).

Question: at what fee per side does the frozen rule's end value equal
  (a) holding BTC, and
  (b) the fixed 25% BTC / 25% ETH / 50% cash weekly mix (fixed_mix at constant 50% exposure; the frozen v3.3 Q1 comparator),
with the same 0.05% slippage per side on every account?

Method: the reviewed corrected harness scripts/research/rerun_frozen_stress.py (decide at the Sunday close, trade at the
next day's open, mark at closes) on the same hash-checked daily inputs as btc_eth_corrected_comparison_20261012/compare.py.
The rule is unchanged (L=28, V=0.5, Sunday). Only the fee varies: 0, 0.10, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60,
0.90, 1.20%. Benchmarks pay the same fee and slippage. Periods: registered A, B, C, FULL, plus S2018 (as compare.py).
Check before reporting: at 0.50% the end values of rule, fixed_mix_50 and hold_btc must equal the stored
comparison_result.json for every period, or the script stops without writing.
Break-even: linear interpolation of (rule end - benchmark end) between adjacent fee levels where its sign changes.

Limits: fee scenarios are not a new strategy configuration; nothing here changes a verdict, the frozen v3.3 criteria or any
tracker. Every order is assumed to fill at the next daily open at the stated fee. A lower fee from maker (limit) orders is
reachable only if those orders fill; unfilled orders and their cost are NOT modelled. Historical, in-sample.
Output: result.json next to this script (refuses to overwrite)."""
import hashlib, json, sys, datetime as dt
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
EXPECT = {"scripts/research/rerun_frozen_stress.py": "1f98513ae63c4f84819327746872a9dd0a73b3bc35e5e67364c57458ca395907",
          "docs/research/majors_trend_20261009/BTC-USD_d1.json": "64cab2cf912244babb251485a9949a266be30fb80840e95b80d4478a9cde07c0",
          "docs/research/majors_trend_20261009/ETH-USD_d1.json": "9fa81ca8395321dddc5453a2144b5081ada012e74ed3132c9c2c039e5e6206b8"}
DATA = Path(sys.argv[1])
got = {k: sha(ROOT / k) for k in EXPECT}
got_copy = {a: sha(DATA / "maj" / f"{a}-USD_d1.json") for a in ("BTC", "ETH")}
if got != EXPECT or got_copy["BTC"] != EXPECT["docs/research/majors_trend_20261009/BTC-USD_d1.json"] \
        or got_copy["ETH"] != EXPECT["docs/research/majors_trend_20261009/ETH-USD_d1.json"]:
    raise RuntimeError(f"input hash mismatch {got} {got_copy}")
from scripts.research.rerun_frozen_stress import load_frozen, run
ns = load_frozen(DATA); days = ns["days"]; st = ns["stats"]
def ix(lo, hi):
    ts = lambda s: int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())
    return next(i for i, d in enumerate(days) if d >= ts(lo)), max(i for i, d in enumerate(days) if d <= ts(hi))
PER = dict(ns["PER"]); PER["S2018"] = ix("2018-01-01", "2026-10-08")
FEES = [0.0, 0.001, 0.002, 0.0025, 0.003, 0.0035, 0.004, 0.005, 0.006, 0.009, 0.012]
res = {}
for f in FEES:
    res[f] = {}
    for p, (lo, hi) in PER.items():
        c, e = run(ns, "rule", lo, hi, fee=f)
        m, _ = run(ns, "fixed_mix", lo, hi, fee=f, expo=0.5)
        h, _ = run(ns, "hold_btc", lo, hi, fee=f)
        res[f][p] = {"rule": {**st(c), "avg_exposure_pct": round(e * 100, 1)}, "mix_25_25_50": st(m), "hold_btc": st(h)}
stored = json.load(open(ROOT / "docs/research/btc_eth_corrected_comparison_20261012/comparison_result.json"))["results"]["0.005"]
check = {p: (res[0.005][p]["rule"]["end_usd"] == stored[p]["rule"]["end_usd"],
             res[0.005][p]["mix_25_25_50"]["end_usd"] == stored[p]["fixed_mix_50"]["end_usd"],
             res[0.005][p]["hold_btc"]["end_usd"] == stored[p]["hold_btc"]["end_usd"]) for p in PER}
if not all(all(v) for v in check.values()):
    raise RuntimeError(f"harness does not reproduce stored 0.50% results: {check}")
def breakeven(p, bench):
    d = [(f, res[f][p]["rule"]["end_usd"] - res[f][p][bench]["end_usd"]) for f in FEES]
    if all(x > 0 for _, x in d): return "rule ahead at every fee up to 1.20%"
    if all(x <= 0 for _, x in d): return "rule behind even at 0% fee"
    for (f1, x1), (f2, x2) in zip(d, d[1:]):
        if x1 > 0 >= x2: return round(100 * (f1 + (f2 - f1) * x1 / (x1 - x2)), 3)
    return "sign pattern not monotonic: see table"
out = {"artifact_type": "research_only_exploratory_fee_breakeven", "not_promotion_evidence": True, "author": "Claude (Cowork)",
       "inputs_sha256": got, "script_sha256": sha(__file__), "harness_check_at_0.50pct": check,
       "periods": {k: [str(dt.datetime.fromtimestamp(days[a], dt.timezone.utc).date()), str(dt.datetime.fromtimestamp(days[b], dt.timezone.utc).date())] for k, (a, b) in PER.items()},
       "slippage_per_side": 0.0005, "fees": FEES, "results": {str(f): v for f, v in res.items()},
       "breakeven_fee_pct_per_side": {p: {"vs_hold_btc": breakeven(p, "hold_btc"), "vs_mix_25_25_50": breakeven(p, "mix_25_25_50")} for p in PER}}
json.dump(out, open(Path(__file__).parent / "result.json", "x"), indent=1)
print("harness check:", check)
print("break-even fee % per side:", json.dumps(out["breakeven_fee_pct_per_side"], indent=1))
for p in PER:
    print(p, " | ".join(f"{100*f:.2f}%: rule {res[f][p]['rule']['end_usd']:.0f} / BTC {res[f][p]['hold_btc']['end_usd']:.0f} / mix {res[f][p]['mix_25_25_50']['end_usd']:.0f}" for f in FEES))
