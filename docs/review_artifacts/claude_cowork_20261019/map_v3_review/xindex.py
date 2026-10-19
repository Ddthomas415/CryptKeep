"""Cross-index every CMC contract (190 IDs) against every Coinbase currency's contracts (all 511, any product)."""
import json, sys, re
from pathlib import Path
IN = Path(sys.argv[1])
P = json.load(open(IN / "01_products.json")); C = json.load(open(IN / "01_currencies.json"))
CC = json.load(open(IN / "cmc_contracts.json"))["assets"]; M = json.load(open(IN / "identity_map.json"))["records"]
usd = {}
for p in P:
    if p["quote_currency"] in ("USD", "USDC", "USDT"): usd.setdefault(p["base_currency"].upper(), []).append(p["id"] + ":" + p["status"])
PH = {"0x" + "e" * 40, "0x" + "0" * 40}
def f(a):
    a = a.strip().lower()
    if not a or a in PH: return set()
    return {a, a[2:] if a.startswith("0x") else a}
idx = {}
for c in C:
    for n in c.get("supported_networks") or []:
        for x in f(n.get("contract_address") or ""):
            idx.setdefault(x, set()).add(c["id"].upper())
# placeholder-like addresses appearing in Coinbase or CMC data
from collections import Counter
cnt = Counter(x for c in C for n in (c.get("supported_networks") or []) for x in [(n.get("contract_address") or "").strip().lower()] if x)
print("Coinbase contract addresses used by >1 currency:", {k: v for k, v in cnt.items() if v > 1})
cmccnt = Counter(a.lower() for v in CC.values() for a in v["contracts"])
print("CMC addresses listed under >1 CMC ID:", {k: v for k, v in cmccnt.items() if v > 1})
for i, v in sorted(CC.items(), key=lambda x: int(x[0])):
    hits = set()
    for a in v["contracts"]:
        for x in f(a): hits |= idx.get(x, set())
    m = M[i]
    mapped = set(m.get("coinbase_bases") or ([m.get("coinbase_base", m["symbol"])] if m["status"] == "mapped" else []))
    if hits != mapped and hits:
        print(i, m["symbol"], m["status"], "mapped:", sorted(mapped), "contract hits:", {h: usd.get(h, "no USD product") for h in hits})
