"""Integrated read-only CMC diagnostics; primary statistical scoring is not authorized."""
import argparse
import collections
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.research.cmc_daily_cohorts import build_cohorts
from scripts.research.cmc_diagnostic_evaluator import evaluate
from scripts.research.cmc_maturity import readiness
from scripts.research.cmc_quote_evidence import inspect_quote
from scripts.research.cmc_snapshot_evidence import load_snapshot
from scripts.research.cmc_statistics import summarize
from scripts.research.cmc_book_evidence import notional_sensitivity, timing_evidence


def run(directory, now):
    if now.utcoffset() is None:
        raise ValueError("aware report time required")
    now = now.astimezone(timezone.utc)
    envelopes, rejected = [], []
    for path in sorted(directory.glob("*.json")):
        try:
            item = load_snapshot(path)
            if item["snapshot_utc"] > now:
                raise ValueError("future snapshot")
            envelopes.append(item)
        except (KeyError, TypeError, ValueError) as exc:
            rejected.append({"file": str(path), "reason": str(exc)})
    cohorts = build_cohorts(envelopes)
    lookup = {item["file"]: item for item in envelopes}
    start = cohorts["qualified_collection_start_utc"]
    book_diagnostics = []
    for item in envelopes:
        books = item["data"].get("coinbase_level1_books")
        if books is None:
            book_diagnostics.append({"source_file": item["file"], "source_sha256": item["sha256"],
                                     "status": "MISSING_BOOK_CAPTURE", "scoring_authorized": False})
            continue
        if not isinstance(books, dict):
            book_diagnostics.append({"source_file": item["file"], "source_sha256": item["sha256"],
                                     "status": "INVALID_BOOK_CONTAINER", "scoring_authorized": False})
            continue
        expected = {row.get("coinbase_product") for row in item["data"]["tracked_coinbase"]
                    if isinstance(row, dict) and isinstance(row.get("coinbase_product"), str)}
        expected.update(("BTC-USD", "ETH-USD"))
        for product in sorted(expected | set(books)):
            evidence = (notional_sensitivity(books[product], product)
                        if product in books else {"status": "MISSING_PRODUCT_BOOK", "scoring_authorized": False})
            book_diagnostics.append({"source_file": item["file"], "source_sha256": item["sha256"],
                                     "product_id": product, **evidence,
                                     "timing_evidence": timing_evidence(books[product], now)
                                     if product in books else {"timing_status": "MISSING"}})
    outcomes = []
    for event in cohorts["events"]:
        source = lookup[event["first_snapshot_file"]]
        row = next(row for row in source["data"]["trending_hidden_boost"]
                   if row.get("type") == "listing" and str(int(row["cmc_id"])) == event["cmc_id"])
        base = {"cmc_id": event["cmc_id"], "utc_day": event["utc_day"],
                "source_sha256": event["first_snapshot_sha256"]}
        if event["cohort_status"] != "PRIMARY_COHORT_CANDIDATE":
            outcomes.append({**base, "status": event["cohort_status"]})
            continue
        if not event["identity_eligible_at_first_observation"]:
            outcomes.append({**base, "status": "EXCLUDED_IDENTITY"})
            continue
        quote = inspect_quote(row.get("coinbase", {}))
        if quote["status"] != "STRUCTURALLY_VALID":
            outcomes.append({**base, "status": "INVALID_ENTRY_QUOTE"})
            continue
        entry = {"cohort_status": event["cohort_status"], "identity_eligible": True,
                 "coin_quote": row["coinbase"],
                 "btc_quote": source["data"]["majors_coinbase"].get("BTC", {})}
        endpoints = []
        for item in envelopes:
            for tracked in item["data"]["tracked_coinbase"]:
                if not isinstance(tracked, dict):
                    continue
                if (str(tracked.get("cmc_id")) == event["cmc_id"]
                        and tracked.get("coinbase_product") == row.get("coinbase_product")):
                    endpoints.append({"identity_eligible": tracked.get("identity_eligible"),
                                      "coin_quote": tracked.get("quote", {}),
                                      "btc_quote": item["data"]["majors_coinbase"].get("BTC", {})})
        for horizon in (1, 7, 30):
            if quote["received_utc"] > now:
                outcomes.append({**base, "horizon_days": horizon, "status": "FUTURE_ENTRY_QUOTE"})
                continue
            calendar = readiness(start, quote["received_utc"], now, horizon)
            if not calendar["minimum_collection_age_reached"]:
                result = {"status": "NOT_READY_90_DAYS"}
            elif not calendar["endpoint_window_closed"]:
                result = {"status": "IMMATURE"}
            else:
                result = evaluate(entry, endpoints, horizon)
            outcomes.append({**base, "horizon_days": horizon, **result})
    return {"artifact_type": "integrated_cmc_diagnostic_report", "as_of_utc": now.isoformat(),
            "source_files": [{"file": item["file"], "sha256": item["sha256"]} for item in envelopes],
            "rejected_envelopes": rejected, "excluded_lists": cohorts["excluded_lists"],
            "excluded_context": cohorts["excluded_context"],
            "malformed_tracked_rows": sum(not isinstance(row, dict) for item in envelopes
                                           for row in item["data"]["tracked_coinbase"]),
            "observed_utc_days": cohorts["observed_utc_days"], "outcomes": outcomes,
            "qualified_collection_start_utc": start,
            "book_capacity_diagnostics": book_diagnostics,
            "book_status_counts": dict(collections.Counter(item["status"] for item in book_diagnostics)),
            "book_capacity_scope": "100USD_entry_notional_excluding_fees;not_fill_or_round_trip_proof",
            "status_counts": dict(collections.Counter(item["status"] for item in outcomes)),
            "statistics": summarize(outcomes, cohorts["observed_utc_days"],
                                    bool(start and (now-start).total_seconds() >= 90*86400)),
            "scoring_authorized": False, "unattended_schedule": "UNVERIFIED",
            "limits": ["daily_capture_convention_not_primary_policy", "freshness_unverified",
                       "no_statistical_inference_or_profitability_acceptance"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.snapshots, datetime.fromisoformat(args.as_of.replace("Z", "+00:00")))
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False,
                  default=lambda value: value.isoformat())
    print(json.dumps(result["status_counts"]))


if __name__ == "__main__":
    main()
