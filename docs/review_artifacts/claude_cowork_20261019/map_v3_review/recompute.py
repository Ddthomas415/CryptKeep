"""Reviewer's independent recomputation of identity map v3 from the inputs (does not import the builder)."""
import csv, json, re, sys
from pathlib import Path
IN = Path(sys.argv[1]); OUT = Path(sys.argv[2])
ids = list(csv.DictReader(open(IN / "control_ids_v2.csv")))
P = json.load(open(IN / "01_products.json")); C = json.load(open(IN / "01_currencies.json"))
ADJ = json.load(open(IN / "identity_adjudications_v3.json"))["adjudications"]
CC = json.load(open(IN / "cmc_contracts.json"))["assets"]
OK_Q = {"USD", "USDC", "USDT"}
def slugify(s): return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and")).strip("-")
prods = {}; allbases = set()
for p in P:
    b = p["base_currency"].upper(); allbases.add(b)
    if p["quote_currency"] in OK_Q: prods.setdefault(b, []).append((p["id"], p["status"]))
cur = {c["id"].upper(): c for c in C}
cname = {k: v["name"] for k, v in cur.items()}
SUF = ["-network", "-protocol", "-token", "-coin", "-finance", "-chain", "-new", "-v2", "-io"]
def stems(s): return {s} | {s[: -len(x)] for x in SUF if s.endswith(x)}
def cands(sym, slug):
    r = []
    for b in prods:
        if b == sym: continue
        n = slugify(cname.get(b, ""))
        hit = False
        if n:
            if stems(n) & stems(slug): hit = True
            if len(n) >= 3 and (n == slug.split("-")[0] or slug == n.split("-")[0]): hit = True
        if len(sym) >= 3 and sym in b: hit = True
        if hit: r.append(b)
    return sorted(r)
PH = {"0x" + "e" * 40, "0x" + "0" * 40}
def forms(addrs):
    s = set()
    for a in addrs:
        a = a.strip().lower()
        if not a or a in PH: continue
        s.add(a); s.add(a[2:] if a.startswith("0x") else a)
    return s
def cb_check(base, cmcf):
    nets = cur[base].get("supported_networks") or []
    addrs = [(n.get("contract_address") or "").strip() for n in nets]
    f = forms([a for a in addrs if a])
    native = any(not a for a in addrs)
    if f & cmcf: return "match"
    if native or not f or not cmcf: return "not_comparable"
    return "mismatch"
res = {}
for row in ids:
    i, sym, slug = row["cmc_id"], row["symbol"].upper(), row["slug"]
    a = ADJ.get(i)
    r = {"status": None, "bases": [], "alt": []}
    exact = sym in prods and sym in cname and slugify(cname[sym]) == slug
    alt = [] if exact else cands(sym, slug)
    r["alt"] = alt
    if alt:
        if not a: r["status"] = "unknown"
        elif a["decision"] == "mapped":
            b = a.get("coinbase_base", sym)
            assert b in alt or (b == sym and sym in prods), i
            r["status"] = "mapped"; r["bases"] = [b]
        else: r["status"] = a["decision"]
    elif sym not in allbases or sym not in prods: r["status"] = "never_listed"
    elif sym not in cname: r["status"] = "unknown"
    elif slugify(cname[sym]) == slug: r["status"] = "mapped"; r["bases"] = [sym]
    elif a: r["status"] = a["decision"]; r["bases"] = [sym] if a["decision"] == "mapped" else []
    else: r["status"] = "unknown"
    if r["status"] == "mapped" and a and a.get("coinbase_bases"):
        r["bases"] = list(a["coinbase_bases"])
    if r["status"] == "mapped":
        if i not in CC: r["status"] = "unknown"; r["why"] = "nocmc"
        else:
            cf = forms(CC[i]["contracts"])
            r["cc"] = {b: cb_check(b, cf) for b in r["bases"]}
            if len(r["bases"]) > 1: assert all(v == "match" for v in r["cc"].values()), i
            if "mismatch" in r["cc"].values() and not (a and a.get("contract_override")):
                r["status"] = "unknown"; r["why"] = "mismatch"
    r["products"] = sorted(p for b in r["bases"] for p in prods[b]) if r["status"] == "mapped" else []
    res[i] = r
json.dump(res, open(OUT / "mine.json", "w"), indent=1, sort_keys=True)
M = json.load(open(IN / "identity_map.json"))["records"]
assert set(M) == set(res) and len(res) == 383
nd = 0
for i, r in res.items():
    m = M[i]
    mb = m.get("coinbase_bases") or ([m.get("coinbase_base", m["symbol"])] if m["status"] == "mapped" else [])
    mp = sorted((p["id"], p["status"]) for p in m.get("products", [])) if m["status"] == "mapped" else []
    if (m["status"], mb, mp, m.get("alternate_candidates", []), m.get("contract_check")) != (r["status"], r["bases"], r["products"], r["alt"], r.get("cc")):
        nd += 1; print("DIFF", i, m["status"], mb, r)
print("differences:", nd)
from collections import Counter
ent = {r["cmc_id"]: r for r in csv.DictReader(open(IN / "entrant_ids_v2.csv"))}
print("all:", Counter(r["status"] for r in res.values()))
print("entrants:", Counter(res[i]["status"] for i in ent), "entrant selections:", Counter(res[i]["status"] for i in ent for _ in range(int(ent[i]["selections"]))))
print("contract checks:", Counter(v for r in res.values() for v in r.get("cc", {}).values()))
print("mapped records by worst check:", Counter(("mismatch" if "mismatch" in r["cc"].values() else "not_comparable" if "not_comparable" in r["cc"].values() else "match") for r in res.values() if r.get("cc") and r["status"]=="mapped"))
