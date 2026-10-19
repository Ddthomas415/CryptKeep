"""ENTR-CB-1 Step B identity map: CMC ID -> Coinbase asset, by ticker, name/slug and contract address.

Inputs (all saved, hash-checked by the caller): the ID list, Coinbase /products and /currencies
responses, an explicit adjudications file, and (v3) CMC contract addresses per CMC ID. Output:
identity_map.json (one record per CMC ID with status, reason and evidence) and review.csv.

Rules (operator-approved 2026-10-19; frozen ENTR-CB-1 preregistration a7fb3662..., section 3):
- never_listed: the CMC symbol is absent from Coinbase's complete product list (which retains long-
  delisted products, shown in Step A), or appears only with quotes other than USD/USDC/USDT, and no
  alternate-ticker candidate exists (or an adjudication rejects every candidate).
- mapped: ticker matches a Coinbase base currency that has USD/USDC/USDT products AND the Coinbase
  currency name normalised equals the CMC slug ("exact"), or an explicit adjudication accepts it.
- unknown: ticker matches but the name does not, and no adjudication accepts it (default), or no
  Coinbase currency record exists for the ticker.
- Alternate tickers (v2, widened in v3): every record that is not an exact match is checked for other
  Coinbase bases with USD/USDC/USDT products that may be the same asset (name equals slug exactly or
  after one common suffix on either side; whole name equals the slug's first word or the reverse; the
  CMC ticker embedded in a longer Coinbase ticker). v2 skipped this whenever the CMC ticker existed on
  Coinbase under another project. Any candidate forces an adjudication: "mapped" with "coinbase_base"
  (one of the candidates or the CMC ticker), "never_listed" or "unknown", each with a reason.
  Unadjudicated -> unknown.
- Contract addresses (v3, prereg section 3.1 "contract address where one exists"): for every mapped
  record, each Coinbase base's contract addresses (from /currencies) are compared with the contract
  addresses CMC lists for that CMC ID. "match" (an address in common) or "not_comparable" (Coinbase
  lists the coin on its own network, or one side has no contract) keep the mapping; "mismatch" makes
  the record unknown unless the adjudication gives a "contract_override" reason; missing CMC data for a
  mapped ID makes it unknown.
- Continuation (v3): an adjudication may list several Coinbase bases ("coinbase_bases") for one CMC ID
  when Coinbase moved the same asset to a new ticker 1:1 (for example a chain migration). Accepted only
  if every listed base has USD/USDC/USDT products and a contract "match" with the CMC ID; the record's
  products are then the union. Mapped records whose products are all delisted while a same-name
  Coinbase base is online are annotated "continuation_candidates" for review; that annotation alone
  changes nothing.
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


def build(ids, products, currencies, adjudications, cmc_contracts=None):
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

    def keys(text):
        return {text} | {text[:-len(s)] for s in SUFFIXES if text.endswith(s)}

    def alternates(symbol, slug):
        """Coinbase bases other than the CMC ticker that might be the same asset (v3: wider net).

        A candidate never maps by itself; it forces an explicit adjudication."""
        found = set()
        for base in by_base:
            if base == symbol:
                continue
            name = norm(names.get(base, ""))
            if name and keys(slug) & keys(name):
                found.add(base)  # name equals slug, exactly or after one common suffix on either side
            elif name and len(name) >= 3 and (slug.split("-")[0] == name or name.split("-")[0] == slug):
                found.add(base)  # whole name equals the slug's first word, or the reverse
            elif len(symbol) >= 3 and symbol in base:
                found.add(base)  # ticker embedded in a longer Coinbase ticker (CORECHAIN, WLUNA)
        return sorted(found)

    out = {}
    for row in ids:
        cmc_id, symbol, slug = row["cmc_id"], row["symbol"].upper(), row["slug"]
        rec = {"cmc_id": int(cmc_id), "symbol": symbol, "slug": slug}
        exact = symbol in by_base and symbol in names and norm(names[symbol]) == slug
        alt = [] if exact else alternates(symbol, slug)
        if alt:
            rec.update(alternate_candidates=alt)
            allowed = set(alt) | ({symbol} if symbol in by_base else set())
            adj = adjudications.get(cmc_id)
            if adj is None:
                rec.update(status="unknown", reason="alternate_ticker_candidate_unadjudicated")
            elif adj["decision"] == "mapped" and adj.get("coinbase_base", symbol) in allowed and adj.get("reason"):
                base = adj.get("coinbase_base", symbol)
                rec.update(status="mapped", coinbase_base=base, coinbase_name=names.get(base, ""),
                           products=sorted(by_base[base], key=lambda x: x["id"]),
                           reason=("adjudicated_alternate_ticker: " if base != symbol else "adjudicated: ")
                           + adj["reason"])
            elif adj["decision"] == "never_listed" and adj.get("reason"):
                rec.update(status="never_listed", reason="adjudicated_not_same_asset: " + adj["reason"])
            elif adj["decision"] == "unknown" and adj.get("reason"):
                rec.update(status="unknown", reason="adjudicated: " + adj["reason"])
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
    if cmc_contracts is not None:
        apply_contracts_and_continuations(out, by_base, currencies, adjudications, cmc_contracts)
    annotate(out, by_base, names)
    return out


PLACEHOLDERS = {"0x" + "e" * 40, "0x" + "0" * 40}  # native-coin stand-ins shared by many coins; never evidence


def address_forms(addresses):
    """Comparable forms: lowercased, with and without a leading 0x (Coinbase writes the Avalanche
    X-Chain asset id as 0x + lowercased id); placeholder addresses dropped."""
    forms = set()
    for address in addresses:
        a = address.strip().lower()
        if a and a not in PLACEHOLDERS:
            forms |= {a, a[2:] if a.startswith("0x") else a}
    return forms


def coinbase_contracts(currency):
    """(comparable contract forms, listed on its own network?) from a /currencies record."""
    addresses, native = [], False
    for network in currency.get("supported_networks") or []:
        address = (network.get("contract_address") or "").strip()
        if address:
            addresses.append(address)
        else:
            native = True
    return address_forms(addresses), native


def contract_result(currency, cmc_addresses):
    addresses, native = coinbase_contracts(currency)
    if addresses & cmc_addresses:
        return "match"
    if native or not addresses or not cmc_addresses:
        return "not_comparable"
    return "mismatch"


def apply_contracts_and_continuations(out, by_base, currencies, adjudications, cmc_contracts):
    by_id = {c["id"].upper(): c for c in currencies}
    for cmc_id, rec in out.items():
        adj = adjudications.get(cmc_id) or {}
        if rec["status"] == "mapped" and adj.get("coinbase_bases"):
            bases = adj["coinbase_bases"]
            current = rec.get("coinbase_base", rec["symbol"])
            if (current not in bases or len(set(bases)) != len(bases) or not adj.get("reason")
                    or any(b not in by_base or b not in by_id for b in bases)):
                raise ValueError(f"bad continuation adjudication for {cmc_id}")
            rec.update(coinbase_bases=list(bases), continuation_reason=adj["reason"],
                       products=sorted((p for b in bases for p in by_base[b]), key=lambda x: x["id"]))
        if rec["status"] != "mapped":
            continue
        asset = cmc_contracts.get(cmc_id)
        if asset is None:
            rec.update(status="unknown", reason="cmc_contract_data_missing (was: " + rec["reason"] + ")")
            continue
        cmc_addresses = address_forms(asset["contracts"])
        bases = rec.get("coinbase_bases") or [rec.get("coinbase_base", rec["symbol"])]
        checks = {b: contract_result(by_id[b], cmc_addresses) for b in bases}
        rec["contract_check"] = checks
        if "coinbase_bases" in rec and any(v != "match" for v in checks.values()):
            raise ValueError(f"continuation for {cmc_id} needs a contract match on every base: {checks}")
        if "mismatch" in checks.values():
            if adj.get("contract_override"):
                rec["contract_override"] = adj["contract_override"]
            else:
                rec.update(status="unknown", reason="contract_mismatch (was: " + rec["reason"] + ")")


def annotate(out, by_base, names):
    shared = {}
    for cmc_id, rec in out.items():
        if rec["status"] == "mapped":
            for base in rec.get("coinbase_bases") or [rec.get("coinbase_base", rec["symbol"])]:
                shared.setdefault(base, []).append(cmc_id)
    for ids_on_base in shared.values():
        if len(ids_on_base) > 1:  # e.g. a legacy token and its migrated successor; disclosed, not decided here
            for cmc_id in ids_on_base:
                out[cmc_id]["shares_coinbase_base_with"] = sorted(i for i in ids_on_base if i != cmc_id)
    online = {b for b, ps in by_base.items() if any(p["status"] == "online" for p in ps)}
    for rec in out.values():
        if rec["status"] != "mapped" or any(p["status"] == "online" for p in rec["products"]):
            continue
        used = set(rec.get("coinbase_bases") or [rec.get("coinbase_base", rec["symbol"])])
        words = {norm(names.get(b, "")).split("-")[0] for b in used} | {rec["slug"].split("-")[0]}
        found = sorted(b for b in online - used if norm(names.get(b, "")).split("-")[0] in words)
        if found:
            rec["continuation_candidates"] = found


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("--ids", "--products", "--currencies", "--adjudications", "--output-dir"):
        parser.add_argument(name, type=Path, required=True)
    parser.add_argument("--cmc-contracts", type=Path, required=True,
                        help='JSON {"schema": "entr-cb1-cmc-contracts-v1", "assets": {"<cmc_id>": {"contracts": [...]}}}')
    args = parser.parse_args(argv)
    ids = list(csv.DictReader(open(args.ids)))
    products = json.loads(args.products.read_bytes())
    currencies = json.loads(args.currencies.read_bytes())
    adjudications = json.loads(args.adjudications.read_bytes())["adjudications"]
    contracts_doc = json.loads(args.cmc_contracts.read_bytes())
    if contracts_doc.get("schema") != "entr-cb1-cmc-contracts-v1":
        raise SystemExit("bad CMC contracts file")
    result = build(ids, products, currencies, adjudications, contracts_doc["assets"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    doc = {"schema": "entr-cb1-identity-map-v3",
           "inputs": {str(p): digest(p) for p in (args.ids, args.products, args.currencies, args.adjudications,
                                                   args.cmc_contracts)},
           "records": result}
    with open(args.output_dir / "identity_map.json", "x") as f:
        json.dump(doc, f, indent=2, sort_keys=True)
    with open(args.output_dir / "review.csv", "x", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cmc_id", "symbol", "cmc_slug", "coinbase_name", "status", "reason", "products",
                    "contract_check", "alternate_candidates", "continuation_candidates", "shares_coinbase_base_with"])
        for r in result.values():
            w.writerow([r["cmc_id"], r["symbol"], r["slug"], r.get("coinbase_name", ""), r["status"],
                        r["reason"], " ".join(p["id"] for p in r.get("products", [])),
                        " ".join(f"{b}={v}" for b, v in sorted(r.get("contract_check", {}).items())),
                        " ".join(r.get("alternate_candidates", [])), " ".join(r.get("continuation_candidates", [])),
                        " ".join(r.get("shares_coinbase_base_with", []))])
    from collections import Counter
    print(json.dumps({"status": Counter(r["status"] for r in result.values()),
                      "reason": Counter(r["reason"].split(":")[0] for r in result.values())}))


if __name__ == "__main__":
    main()
