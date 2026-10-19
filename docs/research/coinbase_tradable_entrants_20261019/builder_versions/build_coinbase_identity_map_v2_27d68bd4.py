"""ENTR-CB-1 Step B identity map: CMC ID -> Coinbase asset, by ticker plus name/slug.

Inputs (all saved, hash-checked by the caller): the ID list, Coinbase /products and /currencies
responses, and an explicit adjudications file for non-exact name matches. Output: identity_map.json
(one record per CMC ID with status, reason and evidence) and review.csv.

Rules (operator-approved 2026-10-19; frozen ENTR-CB-1 preregistration a7fb3662..., section 3):
- never_listed: the CMC symbol is absent from Coinbase's complete product list (which retains long-
  delisted products, shown in Step A), or appears only with quotes other than USD/USDC/USDT.
- mapped: ticker matches a Coinbase base currency that has USD/USDC/USDT products AND the Coinbase
  currency name normalised equals the CMC slug ("exact"), or an explicit adjudication accepts it.
- unknown: ticker matches but the name does not, and no adjudication accepts it (default), or no
  Coinbase currency record exists for the ticker.
- Alternate tickers (added in v2 of this script): if the CMC symbol is absent but the CMC slug matches
  a Coinbase currency name (exactly, or after removing one common suffix such as "-network" or
  "-chain") under a different ticker with USD/USDC/USDT products, the record needs an adjudication:
  "mapped" with an explicit "coinbase_base" from the candidates, or "never_listed" with a reason
  (e.g. a different project, or a redenominated predecessor token). Unadjudicated -> unknown.
A ticker alone never maps an asset.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

QUOTES = {"USD", "USDC", "USDT"}
SUFFIXES = ("-network", "-protocol", "-token", "-coin", "-finance", "-chain", "-new", "-v2", "-io")


def norm(text):
    text = text.lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def build(ids, products, currencies, adjudications):
    by_base, any_quote = {}, set()
    for p in products:
        base = p["base_currency"].upper()
        any_quote.add(base)
        if p["quote_currency"] in QUOTES:
            by_base.setdefault(base, []).append({"id": p["id"], "status": p["status"]})
    names = {c["id"].upper(): c["name"] for c in currencies}
    by_name = {}
    for c in currencies:
        by_name.setdefault(norm(c["name"]), set()).add(c["id"].upper())

    def alternates(symbol, slug):
        keys = [slug] + [slug[:-len(s)] for s in SUFFIXES if slug.endswith(s)]
        return sorted({b for k in keys for b in by_name.get(k, ()) if b in by_base and b != symbol})

    out = {}
    for row in ids:
        cmc_id, symbol, slug = row["cmc_id"], row["symbol"].upper(), row["slug"]
        rec = {"cmc_id": int(cmc_id), "symbol": symbol, "slug": slug}
        alt = alternates(symbol, slug) if symbol not in by_base else []
        if alt:
            rec.update(alternate_candidates=alt)
            adj = adjudications.get(cmc_id)
            if adj is None:
                rec.update(status="unknown", reason="alternate_ticker_candidate_unadjudicated")
            elif adj["decision"] == "mapped" and adj.get("coinbase_base") in alt and adj.get("reason"):
                base = adj["coinbase_base"]
                rec.update(status="mapped", coinbase_base=base, coinbase_name=names.get(base, ""),
                           products=sorted(by_base[base], key=lambda x: x["id"]),
                           reason="adjudicated_alternate_ticker: " + adj["reason"])
            elif adj["decision"] == "never_listed" and adj.get("reason"):
                rec.update(status="never_listed", reason="adjudicated_not_same_asset: " + adj["reason"])
            else:
                raise ValueError(f"bad alternate-ticker adjudication for {cmc_id}")
        elif symbol not in any_quote:
            rec.update(status="never_listed", reason="absent_from_products")
        elif symbol not in by_base:
            rec.update(status="never_listed", reason="no_usd_usdc_usdt_product")
        elif symbol not in names:
            rec.update(status="unknown", reason="no_currency_record", products=by_base[symbol])
        else:
            name = names[symbol]
            rec.update(coinbase_name=name, products=sorted(by_base[symbol], key=lambda x: x["id"]))
            if norm(name) == slug:
                rec.update(status="mapped", reason="exact_name_slug")
            elif cmc_id in adjudications:
                adj = adjudications[cmc_id]
                if adj["decision"] not in ("mapped", "unknown") or not adj.get("reason"):
                    raise ValueError(f"bad adjudication for {cmc_id}")
                rec.update(status=adj["decision"], reason="adjudicated: " + adj["reason"])
            else:
                rec.update(status="unknown", reason="name_slug_mismatch_unadjudicated")
        out[cmc_id] = rec
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("--ids", "--products", "--currencies", "--adjudications", "--output-dir"):
        parser.add_argument(name, type=Path, required=True)
    args = parser.parse_args()
    ids = list(csv.DictReader(open(args.ids)))
    products = json.loads(args.products.read_bytes())
    currencies = json.loads(args.currencies.read_bytes())
    adjudications = json.loads(args.adjudications.read_bytes())["adjudications"]
    result = build(ids, products, currencies, adjudications)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    doc = {"schema": "entr-cb1-identity-map-v1",
           "inputs": {str(p): digest(p) for p in (args.ids, args.products, args.currencies, args.adjudications)},
           "records": result}
    with open(args.output_dir / "identity_map.json", "x") as f:
        json.dump(doc, f, indent=2, sort_keys=True)
    with open(args.output_dir / "review.csv", "x", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cmc_id", "symbol", "cmc_slug", "coinbase_name", "status", "reason", "products"])
        for r in result.values():
            w.writerow([r["cmc_id"], r["symbol"], r["slug"], r.get("coinbase_name", ""), r["status"],
                        r["reason"], " ".join(p["id"] for p in r.get("products", []))])
    from collections import Counter
    print(json.dumps({"status": Counter(r["status"] for r in result.values()),
                      "reason": Counter(r["reason"].split(":")[0] for r in result.values())}))


if __name__ == "__main__":
    main()
