import sys, json, hashlib, importlib
sys.path.insert(0, sys.argv[1])
from services.market_data import group_b_selection as g
rank_at = "2026-11-16T00:05:00+00:00"; gen = "2026-11-16T00:06:00+00:00"; now = "2026-11-18T12:00:00+00:00"
inputs = [{"symbol": s, "product_id": None, "exclusion": "no_coinbase_usd_pair",
           "metadata_sha256": "0"*64, "observed_at": "2026-11-16T00:02:00+00:00"} for s in g.UNIVERSE]
body = {"policy": g.POLICY, "venue": "coinbase", "rank_at": rank_at, "generated_at": gen,
        "valid_until": "2026-11-23T00:05:00+00:00", "code": dict(g.FROZEN), "producer_code": g.producer_identity(),
        "inputs": inputs, "ranked": [], "previous_slots": [None, None, None], "previous_sha256": None,
        "slots": [None, None, None]}
art = {**body, "sha256": g.digest(body)}
print("step1 valid artifact accepted:", g.validate_selection(art, now=now) is art)
p = sys.argv[1] + "/services/analytics/group_b_weekly_selection.py"
open(p, "a").write("\n# one-line comment added after publication\n")
try:
    g.validate_selection(art, now=now); print("step2 after producer edit: ACCEPTED")
except ValueError as e:
    print("step2 after producer edit: REFUSED", e)
