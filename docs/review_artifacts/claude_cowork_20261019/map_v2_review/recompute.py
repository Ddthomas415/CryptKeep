"""Independent recomputation of the ENTR-CB-1 identity map (reviewer code, written from the rule text).

Rule (operator-approved, as given to the reviewer):
- never_listed if the CMC symbol is absent from the complete Coinbase product list, or present only
  with quotes other than USD/USDC/USDT, unless listed under a different ticker (then adjudicated).
- mapped only if ticker matches AND Coinbase currency name normalised == CMC slug, or an explicit
  adjudication accepts it. Ticker alone never maps.
- otherwise unknown.
"""
import csv, json, re, sys, unicodedata
from collections import defaultdict, Counter

D = sys.argv[1]
OUT = sys.argv[2]


def normalise(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


ids = list(csv.DictReader(open(f"{D}/control_ids_v2.csv")))
ent = {r["cmc_id"] for r in csv.DictReader(open(f"{D}/entrant_ids_v2.csv"))}
prods = json.load(open(f"{D}/01_products.json"))
curs = json.load(open(f"{D}/01_currencies.json"))
adj = json.load(open(f"{D}/identity_adjudications_v2.json"))["adjudications"]
cmap = json.load(open(f"{D}/identity_map.json"))["records"]

assert ent <= {r["cmc_id"] for r in ids}, "entrants not subset"
assert len(ids) == len({r["cmc_id"] for r in ids}) == 383
assert len(ent) == 107

usd_bases = defaultdict(list)
all_bases = set()
for p in prods:
    b = p["base_currency"].upper()
    all_bases.add(b)
    if p["quote_currency"].upper() in ("USD", "USDC", "USDT"):
        usd_bases[b].append(p["id"])
cur_name = {c["id"].upper(): c["name"] for c in curs}

mine = {}
for r in ids:
    cid, sym, slug = r["cmc_id"], r["symbol"].upper(), r["slug"]
    a = adj.get(cid)
    if sym in usd_bases:
        name = cur_name.get(sym)
        if name is not None and normalise(name) == slug:
            st, why = "mapped", "exact"
        elif a is not None:
            st, why = a["decision"], "adj"
        else:
            st, why = "unknown", "mismatch" if name else "nocur"
    else:
        # symbol absent or non-USD quotes only -> never_listed unless alternate ticker adjudicated
        if a is not None:
            st, why = a["decision"], "adj_alt"
        else:
            st, why = "never_listed", "absent" if sym not in all_bases else "nonusd"
    mine[cid] = (st, why)

diff = []
for cid, (st, why) in mine.items():
    b = cmap[cid]
    if b["status"] != st:
        diff.append((cid, b["symbol"], b["status"], st, b["reason"], why))
    if a := adj.get(cid):
        if a.get("coinbase_base") and b.get("coinbase_base") != a["coinbase_base"]:
            diff.append((cid, "coinbase_base mismatch"))
print("status counts mine:", Counter(s for s, _ in mine.values()))
print("status counts builder:", Counter(v["status"] for v in cmap.values()))
print("entrant counts mine:", Counter(mine[c][0] for c in ent))
print("entrant counts builder:", Counter(cmap[c]["status"] for c in ent))
print("differences:", diff)
# unused adjudications
print("adjudications not in id list:", [k for k in adj if k not in mine])
# product check: builder products equal usd_bases?
for cid, b in cmap.items():
    if b["status"] == "mapped":
        base = b.get("coinbase_base", b["symbol"])
        bp = sorted(p["id"] for p in b["products"])
        if bp != sorted(usd_bases[base]):
            print("product list mismatch", cid, bp, usd_bases[base])
# exactly one Coinbase asset per CMC id, and no Coinbase asset claimed by two CMC ids
claimed = defaultdict(list)
for cid, b in cmap.items():
    if b["status"] == "mapped":
        claimed[b.get("coinbase_base", b["symbol"])].append(cid)
print("coinbase bases claimed by >1 CMC id:", {k: v for k, v in claimed.items() if len(v) > 1})
json.dump({k: list(v) for k, v in mine.items()}, open(f"{OUT}/mine.json", "w"), indent=1)
