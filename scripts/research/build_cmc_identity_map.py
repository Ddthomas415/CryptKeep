"""Build a separate candidate map from reviewed, hashed identity evidence."""
import argparse
import hashlib
import json
from pathlib import Path


def build(proposal_path):
    raw = proposal_path.read_bytes()
    proposal = json.loads(raw)
    for path, expected in proposal["input_sha256"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
            raise ValueError("identity evidence changed: " + path)
    result = {}
    for row in proposal["rows"]:
        if row["status"] != "MATCHING_CHAIN_AND_CONTRACT_PROPOSAL":
            continue
        key = str(row["cmc_id"])
        if key in result or key in {"40925", "40780"}:
            raise ValueError("duplicate or denied identity")
        result[key] = {"coinbase_product": row["product"],
                       "evidence": {"proposal_path": str(proposal_path),
                                    "proposal_sha256": hashlib.sha256(raw).hexdigest(),
                                    "source_snapshot": row["source_snapshot"],
                                    "basis": "same_chain_and_contract_saved_metadata",
                                    "scope": "identity_only_not_execution_or_scoring_authorization"}}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.proposal)
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({"candidate_mappings": len(result), "activated": False}))


if __name__ == "__main__":
    main()
