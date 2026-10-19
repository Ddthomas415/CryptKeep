"""Run the v3 candidate net (reviewer reimplementation) on ALL 383 records incl. exact matches, plus a looser
fuzzy net (difflib on names/slugs, any Coinbase currency incl. no-USD ones) for never_listed records."""
import csv, json, re, sys, difflib
from pathlib import Path
IN = Path(sys.argv[1])
ids = list(csv.DictReader(open(IN / "control_ids_v2.csv")))
ent = {r["cmc_id"] for r in csv.DictReader(open(IN / "entrant_ids_v2.csv"))}
P = json.load(open(IN / "01_products.json")); C = json.load(open(IN / "01_currencies.json"))
M = json.load(open(IN / "identity_map.json"))["records"]
def slugify(s): return re.sub(r"[^a-z0-9]+", "-", s.lower().replace("&", "and")).strip("-")
usd = {}
for p in P:
    if p["quote_currency"] in ("USD", "USDC", "USDT"): usd.setdefault(p["base_currency"].upper(), []).append(p["id"] + ":" + p["status"])
anyp = {p["base_currency"].upper() for p in P}
cname = {c["id"].upper(): c["name"] for c in C}
SUF = ["-network", "-protocol", "-token", "-coin", "-finance", "-chain", "-new", "-v2", "-io", "-dao", "-ai", "-labs", "-foundation"]
def stems(s): return {s} | {s[: -len(x)] for x in SUF if s.endswith(x)}
print("== candidate net on records that skipped it (exact matches) ==")
for r in ids:
    i, sym, slug = r["cmc_id"], r["symbol"].upper(), r["slug"]
    m = M[i]
    if "alternate_candidates" in m: continue
    used = set(m.get("coinbase_bases") or [m.get("coinbase_base", sym)])
    hits = []
    for b in usd:
        if b in used: continue
        n = slugify(cname.get(b, ""))
        if (n and (stems(n) & stems(slug) or (len(n) >= 3 and (n == slug.split("-")[0] or slug == n.split("-")[0])))) or (len(sym) >= 3 and sym in b):
            hits.append(b)
    if hits: print(i, "E" if i in ent else "C", sym, slug, m["status"], sorted(used), "->", {h: (cname.get(h), usd[h]) for h in hits})
print("== fuzzy net for never_listed/unknown (all Coinbase currencies, ratio>=0.8 or first-word match) ==")
for r in ids:
    i, sym, slug = r["cmc_id"], r["symbol"].upper(), r["slug"]
    m = M[i]
    if m["status"] == "mapped": continue
    out = []
    for c in C:
        n = slugify(c["name"]); b = c["id"].upper()
        ratio = difflib.SequenceMatcher(None, n, slug).ratio()
        fw = slug.split("-")[0]
        if ratio >= 0.8 or (len(fw) >= 4 and fw in n.split("-")) or b == sym:
            out.append((b, c["name"], round(ratio, 2), usd.get(b, "no-usd" if b in anyp else "no-product")))
    if out: print(i, "E" if i in ent else "C", sym, slug, m["status"], m["reason"][:30], out)
