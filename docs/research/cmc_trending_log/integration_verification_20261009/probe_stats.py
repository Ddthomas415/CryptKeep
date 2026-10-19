import json, sys, tempfile
from datetime import timedelta
from pathlib import Path
sys.path.insert(0, "."); sys.path.insert(0, sys.argv[1])
from probe_e2e import T0, q
from scripts.research.run_cmc_diagnostic_report import run
d = Path(tempfile.mkdtemp())
for day in range(0, 101):
    t = T0 + timedelta(days=day)
    coins = [200 + i for i in range(0, 60) if day >= 31 + i]
    rows = [{"type": "listing", "cmc_id": c, "identity_eligible": True, "coinbase_product": f"C{c}-USD", "coinbase": q(t, 100, 101)} for c in [1] + coins]
    tr = [{"cmc_id": c, "coinbase_product": f"C{c}-USD", "identity_eligible": True, "quote": q(t, 103 + (c % 3), 104 + (c % 3))} for c in coins]
    data = {"schema_version": 3, "artifact_type": "research_only_forward_log_v3", "places_orders": False, "snapshot_utc": t.isoformat(),
            "trending_status": "OBSERVED", "source_errors": [], "trending_hidden_boost": rows, "tracked_coinbase": tr, "majors_coinbase": {"BTC": q(t, 100, 101)}}
    (d / f"s{day:03d}.json").write_text(json.dumps(data))
r = run(d, T0 + timedelta(days=101))
s = r["statistics"]
print({k: s[k] for k in ("status", "events", "entry_days", "mean_excess_return")}, s["registered_entry_day_bootstrap"]["status"],
      {k: v["status"] for k, v in s["serial_dependence_sensitivities_not_replacement_gate"].items()})
print("7d statuses", sorted({o["status"] for o in r["outcomes"] if o.get("horizon_days") == 7}))
