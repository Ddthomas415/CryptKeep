"""Independent end-to-end probes of run_cmc_diagnostic_report.run (reviewer-written; synthetic data only)."""
import json, sys, tempfile, collections
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, ".")
from scripts.research.run_cmc_diagnostic_report import run

T0 = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)
def q(t, bid, ask):
    return {"payload": {"bid": str(bid), "ask": str(ask)}, "request_started_utc": t.isoformat(), "received_utc": t.isoformat()}
def snap(d, day, listed, tracked, btc=(100, 101), name=None, minute=0, eligible=True, raw=None):
    t = T0 + timedelta(days=day, minutes=minute)
    rows = [{"type": "listing", "cmc_id": c, "identity_eligible": eligible if c == 42 else True,
             "coinbase_product": f"C{c}-USD", "coinbase": q(t, 100, 101)} for c in listed]
    tr = [{"cmc_id": c, "coinbase_product": f"C{c}-USD", "identity_eligible": e, "quote": q(t, b, b + 1)} for c, b, e in tracked]
    data = {"schema_version": 3, "artifact_type": "research_only_forward_log_v3", "places_orders": False,
            "snapshot_utc": t.isoformat(), "trending_status": "OBSERVED", "source_errors": [],
            "trending_hidden_boost": rows, "tracked_coinbase": tr,
            "majors_coinbase": {"BTC": q(t, *btc)} if btc else {}}
    (d / (name or f"s{day:03d}_{minute:02d}.json")).write_text(raw if raw is not None else json.dumps(data))

def scenario(**kw):
    d = Path(tempfile.mkdtemp())
    gap = kw.get("gap_day"); entry_day = 40
    for day in range(0, 101):
        if day == gap: continue
        listed = [1] + ([42] if day >= entry_day else [])
        exit_bid = 120 if day == entry_day + 7 else 110
        tracked = [(42, exit_bid, kw.get("exit_eligible", True))] if day >= entry_day else []
        btc = None if (kw.get("no_btc_exit") and day == entry_day + 7) or (kw.get("no_btc_entry") and day == entry_day) else (100, 101)
        snap(d, day, listed, tracked, btc=btc, eligible=kw.get("entry_eligible", True))
    if kw.get("dup"): snap(d, entry_day, [1, 42], [(42, 105, True)], minute=30)
    if kw.get("malformed"): snap(d, 50, [], [], name="zz_bad.json", raw="{not json")
    return run(d, T0 + timedelta(days=101))

def show(label, r, coin="42"):
    rows = [o for o in r["outcomes"] if o["cmc_id"] == coin]
    by = collections.Counter((o.get("horizon_days"), o["status"]) for o in rows)
    print(label, dict(by), "| rejected", len(r["rejected_envelopes"]), "| stats", r["statistics"].get("status"))
    return rows

ex = lambda e, x, f=.012: x * (1 - f) / (e * (1 + f)) - 1
want = ex(101, 120) - ex(101, 100)
rows = show("A happy path", scenario())
d7 = [o for o in rows if o.get("horizon_days") == 7 and o["status"] == "DIAGNOSTIC"]
print("  7d excess", d7[0]["excess_return"] if d7 else None, "expected", round(want, 6))
show("B gap 10 days before entry", scenario(gap_day=30))
show("C1 entry identity collision", scenario(entry_eligible=False))
show("C2 endpoint identity excluded", scenario(exit_eligible=False))
show("D duplicate same-day capture", scenario(dup=True))
show("E1 missing BTC at entry", scenario(no_btc_entry=True))
show("E2 missing BTC at 7d endpoint", scenario(no_btc_exit=True))
show("F malformed snapshot file", scenario(malformed=True))
