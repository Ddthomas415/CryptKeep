"""Read-only identity check of CMC-to-exchange ticker joins in saved trending snapshots. Research only.
Does not modify any snapshot, the logger, its schedule or any identity map. Fetches one public Coinbase
/currencies response (saved raw with SHA256) to get each Coinbase asset's own name.

Rules fixed before running (2026-10-09):
  price_dev_pct = (exchange mid / CMC price at the same snapshot - 1) * 100, mid = (bid + ask) / 2
  name_match    = normalized CMC token name equals or contains / is contained in the Coinbase currency name
                  (lowercase, letters and digits only)
  MISMATCH      if |price_dev_pct| > 20                      (the quote cannot be the same asset)
  CONSISTENT    if |price_dev_pct| <= 5 and name_match       (evidence only, NOT identity proof)
  REVIEW        otherwise (including Binance rows, which have no name to compare)
These labels are evidence for a future versioned evaluation amendment. They change no existing artifact."""
import json, sys, re, hashlib, glob, os, urllib.request, datetime as dt
SNAPS, OUT = sys.argv[1], sys.argv[2]
norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())
req = urllib.request.Request("https://api.exchange.coinbase.com/currencies", headers={"User-Agent": "cryptkeep-research"})
raw = urllib.request.urlopen(req, timeout=30).read(); recv = dt.datetime.now(dt.timezone.utc).isoformat()
names = {c["id"].upper(): c.get("name") for c in json.loads(raw)}
def classify(dev, nm):
    if dev is None: return "REVIEW"
    if abs(dev) > 20: return "MISMATCH"
    if abs(dev) <= 5 and nm: return "CONSISTENT"
    return "REVIEW"
def row(snapfile, cmc_id, sym, cmc_name, cmc_price, venue, bid, ask):
    try: bid, ask, c = float(bid), float(ask), float(cmc_price)
    except Exception: return None
    mid = (bid + ask) / 2; dev = (mid / c - 1) * 100 if c > 0 else None
    exname = names.get(sym.upper()) if venue == "coinbase" else None
    a, b = norm(cmc_name), norm(exname)
    nm = bool(a and b and (a == b or a in b or b in a)) if venue == "coinbase" else None
    st = classify(dev, nm) if venue == "coinbase" else ("MISMATCH" if dev is not None and abs(dev) > 20 else "REVIEW")
    return {"snapshot": os.path.basename(snapfile), "cmc_id": cmc_id, "symbol": sym, "cmc_name": cmc_name, "cmc_price": c, "venue": venue,
            "exchange_name": exname, "mid": mid, "price_dev_pct": round(dev, 3) if dev is not None else None, "name_match": nm, "status": st}
rows = []
for f in sorted(glob.glob(os.path.join(SNAPS, "*.json"))):
    d = json.load(open(f))
    th = {r.get("cmc_id"): r for r in d.get("trending_hidden_boost", []) if isinstance(r, dict)}
    if "tracked_coinbase" in d:   # v2 schema
        for t in d["tracked_coinbase"]:
            q = (t.get("quote") or {}).get("payload") or {}
            src = (th.get(t.get("cmc_id")) or {}).get("source_record") or {}
            price = src.get("cmc_price") or src.get("priceUsd"); name = src.get("name") or src.get("tokenName")
            if price is None: continue      # retained coin no longer on the list: no same-snapshot CMC price
            r = row(f, t.get("cmc_id"), t.get("symbol"), name, price, "coinbase", q.get("bid"), q.get("ask"))
            if r: rows.append(r)
    else:                             # v1 schema
        for r0 in d.get("trending_hidden_boost", []):
            for venue in ("coinbase", "binance"):
                q = r0.get(venue) or {}
                if "bid" in q:
                    r = row(f, r0.get("cmc_id"), r0.get("symbol"), r0.get("name"), r0.get("cmc_price"), venue, q.get("bid"), q.get("ask"))
                    if r: rows.append(r)
summary = {}
for r in rows: summary.setdefault(r["snapshot"], {}).setdefault(r["status"], 0); summary[r["snapshot"]][r["status"]] += 1
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, "coinbase_currencies_raw.json"), "wb").write(raw)
out = {"artifact_type": "research_only_identity_evidence", "script_sha256": hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
       "coinbase_currencies_sha256": hashlib.sha256(raw).hexdigest(), "coinbase_currencies_received_utc": recv,
       "summary_by_snapshot": summary, "mismatches": [r for r in rows if r["status"] == "MISMATCH"],
       "review": [r for r in rows if r["status"] == "REVIEW"], "rows": rows}
json.dump(out, open(os.path.join(OUT, "identity_check.json"), "w"), indent=1)
print(json.dumps({"summary": summary, "mismatches": [(r["snapshot"][:22], r["venue"], r["symbol"], r["cmc_name"], r["exchange_name"], r["price_dev_pct"]) for r in out["mismatches"]]}, indent=1))
