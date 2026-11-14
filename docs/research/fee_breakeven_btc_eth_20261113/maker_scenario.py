"""Maker-order scenario, ADDED AFTER seeing result.json (Claude, 2026-11-13). Research only, exploratory.
result.json charged 0.05% adverse slippage at every fee level. A maker (limit) order fills at its own limit price, so its
adverse slippage is taken as zero here. The account's observed spot tier (research/coinbase_fee_observation_20261008.json,
observed 2026-10-08) is maker 0.25%, taker 0.50%.
Scenarios, same harness, inputs, rule and periods as fee_breakeven.py; every account pays the same costs:
  taker_now : fee 0.50% + slippage 0.05% (the frozen primary model)
  maker_all : fee 0.25% + slippage 0     (EVERY order fills as maker at the next daily open: an upper bound)
Not modelled: unfilled maker orders, waiting-time price drift, fallback to taker. Not a new strategy configuration."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(ROOT))
from scripts.research.rerun_frozen_stress import load_frozen, run
ns = load_frozen(Path(sys.argv[1])); st = ns["stats"]
PER = dict(ns["PER"])
base = json.load(open(Path(__file__).parent / "result.json"))
PER["S2018"] = None
out = {}
for name, fee, slip in (("taker_now", 0.005, 0.0005), ("maker_all", 0.0025, 0.0)):
    out[name] = {}
    for p in base["periods"]:
        lo, hi = ns["PER"][p] if p in ns["PER"] else None, None
        if p == "S2018":
            import datetime as dt
            days = ns["days"]; ts = lambda s: int(dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc).timestamp())
            lo = next(i for i, d in enumerate(days) if d >= ts("2018-01-01")); hi = max(i for i, d in enumerate(days) if d <= ts("2026-10-08"))
        else:
            lo, hi = ns["PER"][p]
        c, _ = run(ns, "rule", lo, hi, fee=fee, slip=slip)
        m, _ = run(ns, "fixed_mix", lo, hi, fee=fee, slip=slip, expo=0.5)
        h, _ = run(ns, "hold_btc", lo, hi, fee=fee, slip=slip)
        out[name][p] = {"rule": st(c), "mix_25_25_50": st(m), "hold_btc": st(h)}
ok = all(out["taker_now"][p]["rule"]["end_usd"] == base["results"]["0.005"][p]["rule"]["end_usd"] for p in base["periods"])
if not ok: raise RuntimeError("taker_now does not reproduce result.json at 0.50%")
json.dump({"artifact_type": "research_only_exploratory_maker_scenario", "added_after_result_json": True, "results": out},
          open(Path(__file__).parent / "maker_scenario_result.json", "x"), indent=1)
for p in base["periods"]:
    t, mk = out["taker_now"][p], out["maker_all"][p]
    print(p, f"taker: rule {t['rule']['end_usd']:.0f} (dd {t['rule']['max_drawdown_pct']}%, sh {t['rule']['sharpe']}) BTC {t['hold_btc']['end_usd']:.0f} (dd {t['hold_btc']['max_drawdown_pct']}%) mix {t['mix_25_25_50']['end_usd']:.0f}",
          f"| maker: rule {mk['rule']['end_usd']:.0f} (dd {mk['rule']['max_drawdown_pct']}%, sh {mk['rule']['sharpe']}) BTC {mk['hold_btc']['end_usd']:.0f} mix {mk['mix_25_25_50']['end_usd']:.0f}")
