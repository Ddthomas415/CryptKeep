"""Identity-only correction; reuse the preserved version-1 cohort engine."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.research import test_low_value_top100 as original


ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS = ROOT / "docs/research/low_value_top100_20261018"
ENGINE_HASH = "388dc98ac004fe24339291e4d8a0ad4da52d0151a692e70ff0d365f16de4fa59"
MAP_HASH = "3b3a40106d3a63ff17139a97059e45302d1d53cdc7615e8a9c7a534b513e5399"
DELTA_HASH = "11f01b56723cff940bf6416a2c6f6243c7c005954455c6d6ba43bb62292d55f4"


def corrected_view(snapshots, mapping):
    excluded = {item["id"]: item["slug"] for item in mapping["exclusions"]}
    if len(excluded) != len(mapping["exclusions"]):
        raise ValueError("Duplicate exclusion identity")
    for snapshot in snapshots:
        for identity, expected_slug in excluded.items():
            if identity in snapshot and snapshot[identity][2] != expected_slug:
                raise ValueError(f"Identity/slug mismatch for CMC ID {identity}")
    return [{i: row for i, row in snapshot.items() if i not in excluded}
            for snapshot in snapshots]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for path, expected in (
        (Path(original.__file__), ENGINE_HASH),
        (ARTIFACTS / "PROTOCOL.md", original.PROTOCOL_HASH),
        (ARTIFACTS / "instrument_correction_v2.json", MAP_HASH),
        (ARTIFACTS / "CORRECTION_V2.md", DELTA_HASH),
    ):
        if original.digest(path) != expected:
            raise ValueError(f"Frozen component changed: {path.name}")
    mapping = json.loads((ARTIFACTS / "instrument_correction_v2.json").read_text())
    dates, snapshots, hashes = original.load(args.archive, args.input_manifest)
    result = original.run(dates, corrected_view(snapshots, mapping))
    result["provenance"] = {
        "evidence": "MODELLED_EXPLORATORY_CMC_REFERENCE_PRICES_CORRECTED_V2",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": original.digest(__file__), "engine_sha256": ENGINE_HASH,
        "protocol_sha256": original.PROTOCOL_HASH, "correction_map_sha256": MAP_HASH,
        "correction_protocol_sha256": DELTA_HASH,
        "archive_sha256": original.digest(args.archive),
        "manifest_sha256": original.digest(args.input_manifest),
        "weekly_member_sha256": hashes, "snapshots": len(dates),
        "excluded_instrument_ids": sorted(item["id"] for item in mapping["exclusions"]),
        "first_snapshot": dates[0].isoformat(), "last_snapshot": dates[-1].isoformat(),
        "cash_per_independent_cycle": 1000, "fee_per_side": .005,
        "adverse_per_side": .0025, "stress_fee_per_side": .012,
        "supersedes_for_summary": "results.json (preserved, not accepted universe)",
    }
    with args.output.open("x") as target:
        json.dump(result, target, indent=2, allow_nan=False)
        target.write("\n")
    for arm, summary in result["summary"].items():
        print(arm, json.dumps({k: summary[k] for k in (
            "distinct_ids", "funded_cycles", "selections", "unresolved_exits",
            "mean_net_dollars_lower", "median_net_dollars_lower", "worst_cycle_dollars_lower",
            "profitable_cycles_lower", "mean_net_interval")}, sort_keys=True))


if __name__ == "__main__":
    main()
