"""Offline contract evidence proposals; no identity map activation."""
import argparse
import hashlib
import json
from pathlib import Path

NETWORKS = {"Ethereum": "ethereum", "Base": "base", "Solana": "solana",
            "BNB Smart Chain (BEP20)": "bsc", "Robinhood Chain": "robinhood"}


def match(source, currency):
    network = NETWORKS.get(source.get("platformName"))
    address = source.get("tokenAddress")
    if not network or not address:
        return "UNRESOLVED_NO_CONTRACT"
    for row in currency.get("supported_networks", []):
        candidate = row.get("contract_address")
        if row.get("id") != network or not candidate:
            continue
        evm = network != "solana" and address.startswith("0x") and candidate.startswith("0x")
        if (address.lower() == candidate.lower()) if evm else (address == candidate):
            return "MATCHING_CHAIN_AND_CONTRACT_PROPOSAL"
    return "UNRESOLVED_CONTRACT_OR_NETWORK"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path("docs/research/cmc_trending_log")
    currency_path = root / "identity_check_20261009/coinbase_currencies_raw.json"
    currencies = {r["id"]: r for r in json.loads(currency_path.read_bytes())}
    sources, hashes, latest = {}, {}, None
    for path in sorted((root / "snapshots").glob("v2_*.json")):
        raw = path.read_bytes()
        snap = json.loads(raw)
        hashes[str(path)] = hashlib.sha256(raw).hexdigest()
        for row in snap.get("trending_hidden_boost", []):
            if "source_record" in row:
                sources[str(row["cmc_id"])] = {"source": row["source_record"], "snapshot": str(path)}
        if snap.get("schema_version") == 3:
            latest = snap
    if latest is None:
        raise ValueError("v3 capture required")
    rows = []
    for row in latest["tracked_coinbase"]:
        evidence = sources.get(str(row["cmc_id"]), {})
        source = evidence.get("source", {})
        currency = currencies.get(row["coinbase_product"].removesuffix("-USD"), {})
        status = "KNOWN_MISMATCH" if row["identity_status"] == "KNOWN_MISMATCH" else match(source, currency)
        rows.append({"cmc_id": row["cmc_id"], "product": row["coinbase_product"], "status": status,
                     "source_snapshot": evidence.get("snapshot"), "cmc_source": source,
                     "coinbase_currency": currency})
    output = {"artifact_type": "offline_identity_proposals_not_authorization", "rows": rows,
              "input_sha256": {**hashes, str(currency_path): hashlib.sha256(currency_path.read_bytes()).hexdigest()},
              "source": Path(__file__).read_text()}
    with args.out.open("x") as stream:
        json.dump(output, stream, allow_nan=False)
    print(json.dumps({s: sum(r["status"] == s for r in rows) for s in sorted({r["status"] for r in rows})}))


if __name__ == "__main__":
    main()
