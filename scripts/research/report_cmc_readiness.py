"""Read-only coverage report, never a profit score or scheduler health proof."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.research.cmc_snapshot_evidence import load_snapshot


def report(directory, now):
    if now.utcoffset() is None:
        raise ValueError("aware report time required")
    now = now.astimezone(timezone.utc)
    observed, excluded = [], []
    for path in sorted(directory.glob("*.json")):
        try:
            evidence = load_snapshot(path)
            if evidence["snapshot_utc"] > now:
                raise ValueError("future snapshot")
            observed.append(evidence)
        except (ValueError, KeyError, TypeError) as exc:
            excluded.append({"file": str(path), "reason": str(exc)})
    valid_lists = [item for item in observed
                   if item["data"].get("trending_status") == "OBSERVED"
                   and not item["data"].get("source_errors")
                   and item["data"]["trending_hidden_boost"]]
    days = sorted({item["snapshot_utc"].date().isoformat() for item in valid_lists})
    start = min((item["snapshot_utc"] for item in valid_lists), default=None)
    return {"artifact_type": "cmc_collection_readiness_not_profit", "as_of_utc": now.isoformat(),
            "v3_envelopes": len(observed), "observed_nonempty_list_utc_days": days,
            "first_qualified_schema_list_utc": start.isoformat() if start else None,
            "elapsed_collection_days": (now-start).total_seconds()/86400 if start else None,
            "minimum_90_days_reached": bool(start and (now-start).total_seconds() >= 90*86400),
            "source_files": [{"file": item["file"], "sha256": item["sha256"]} for item in observed],
            "excluded_envelopes": excluded, "scoring_authorized": False,
            "unattended_schedule": "UNVERIFIED_BY_SNAPSHOTS",
            "limits": ["list_rows_not_semantically_validated", "no_cohort_or_return_scoring",
                       "no_quote_freshness_or_scheduler_proof", "old_schemas_preserved"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = report(args.snapshots, datetime.fromisoformat(args.as_of.replace("Z", "+00:00")))
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps({"v3_envelopes": result["v3_envelopes"],
                      "days": len(result["observed_nonempty_list_utc_days"]),
                      "minimum_90_days_reached": result["minimum_90_days_reached"]}))


if __name__ == "__main__":
    main()
