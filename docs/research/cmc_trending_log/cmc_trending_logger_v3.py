"""Identity-qualified forward log; v2 snapshots and collector remain unchanged."""
import argparse
import fcntl
import hashlib
import json
import ssl
from pathlib import Path
from urllib.parse import quote as encode_product
import urllib.request

import certifi

import cmc_trending_logger_v2 as base

# Exact CMC ID/product pairs, not ticker-wide exclusions or price heuristics.
COLLISIONS = {("40925", "AI-USD"), ("40780", "META-USD")}
EVIDENCE = Path(__file__).parent / "identity_check_20261009/identity_check.json"


def verified_request(url, body=None):
    """Use the installed CA bundle, including on Python installs without roots."""
    started = base.utcnow()
    try:
        context = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.Request(
            url, data=json.dumps(body).encode() if body is not None else None,
            headers={"User-Agent": "cryptkeep-research-v2", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30, context=context) as response:
            raw = response.read()
        return {"payload": json.loads(raw), "request_started_utc": base.stamp(started),
                "received_utc": base.stamp(base.utcnow()),
                "response_sha256": hashlib.sha256(raw).hexdigest()}
    except Exception as exc:
        return {"payload": None, "request_started_utc": base.stamp(started),
                "received_utc": base.stamp(base.utcnow()), "error": str(exc)}


def qualify(result, evidence):
    shown = {(str(r["cmc_id"]), r["symbol"].upper() + "-USD")
             for r in evidence["mismatches"] if r["venue"] == "coinbase"}
    if not COLLISIONS <= shown:
        raise ValueError("required collision evidence missing")
    for row in result["tracked_coinbase"]:
        key = (str(row["cmc_id"]), row["coinbase_product"])
        if key in COLLISIONS:
            row["identity_status"] = "KNOWN_MISMATCH"
            row["identity_evidence"] = "identity_check_20261009/identity_check.json"
        row["identity_eligible"] = row["identity_status"] == "OPERATOR_MAPPED"
        row["scoring_status"] = "IDENTITY_ONLY_QUALIFIED" if row["identity_eligible"] else "IDENTITY_EXCLUDED"
    lookup = {(str(r["cmc_id"]), r["coinbase_product"]): r for r in result["tracked_coinbase"]}
    for row in result["trending_hidden_boost"]:
        key = (str(row["cmc_id"]), row.get("coinbase_product"))
        if key in lookup:
            row["identity_status"] = lookup[key]["identity_status"]
            row["identity_eligible"] = lookup[key]["identity_eligible"]
    result.update(artifact_type="research_only_forward_log_v3", schema_version=3,
                  collector_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  base_collector_sha256=hashlib.sha256(Path(base.__file__).read_bytes()).hexdigest(),
                  identity_policy="exact_collision_exclusion_v1; evidence-backed map required otherwise; not full scoring authorization")
    return result


def capture_books(result, fetch):
    """Retain raw L1 evidence separately; never replace registered ticker prices."""
    products = {row["coinbase_product"] for row in result["tracked_coinbase"]}
    products.update(("BTC-USD", "ETH-USD"))
    books = {}
    for product in sorted(products):
        url = base.CB + "/products/" + encode_product(product, safe="") + "/book?level=1"
        try:
            response = fetch(url)
        except Exception as exc:
            response = {"payload": None, "error": str(exc)}
        books[product] = {"product_id": product, "request_url": url,
                          "response": response, "execution": "NOT_FILL_PROOF"}
    result["coinbase_level1_books"] = books
    result["book_capture_policy"] = "optional_l1_raw_evidence_v1; auction quotes indicative; no scoring authorization"
    return result


def collect(directory, identities=None, capture_level1=False, **kwargs):
    kwargs.setdefault("fetch", verified_request)
    raw = EVIDENCE.read_bytes()
    result = qualify(base.collect(directory, identities, **kwargs), json.loads(raw))
    result["collision_evidence_sha256"] = hashlib.sha256(raw).hexdigest()
    if kwargs["fetch"] is verified_request:
        result["tls_policy"] = "certifi_ca_bundle; certificate_and_hostname_verification_required"
        result["ca_bundle_sha256"] = hashlib.sha256(Path(certifi.where()).read_bytes()).hexdigest()
    else:
        result["tls_policy"] = "CUSTOM_TRANSPORT_UNVERIFIED"
    if capture_level1:
        capture_books(result, kwargs.get("fetch", base.request))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--identity-map", type=Path)
    parser.add_argument("--capture-level1", action="store_true")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    identities = json.loads(args.identity_map.read_text()) if args.identity_map else {}
    with (args.out / ".collector.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = collect(args.out, identities, capture_level1=args.capture_level1)
        # Existing immutable publisher retained; schema_version, not filename,
        # identifies v3. This preserves the tested publication/cleanup contract.
        target = base.save(args.out, result)
    print(json.dumps({"file": str(target), "schema_version": 3,
                      "trending_status": result["trending_status"],
                      "identity_excluded": sum(not r["identity_eligible"] for r in result["tracked_coinbase"])}))
    return 0 if result["trending_status"] == "OBSERVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
