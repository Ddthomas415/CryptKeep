"""Registered + quote-qualified CMC views (operator policy 2026-10-09). Diagnostic only.

Wraps the integrated report without changing it. Every DIAGNOSTIC outcome is re-checked at its entry capture
and at its selected endpoint capture; an outcome enters the QUALIFIED view only if both qualify. The gate
condition (both views, every interval above zero) is reported descriptively; primary scoring stays blocked
because the statistical method returned NO_CERTIFIED_SAMPLE (confirmation_result_v2_20261009.md).
"""
import argparse
import collections
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.research.cmc_quote_qualification import POLICY, _time, all_ranges_above_zero, qualify_capture
from scripts.research.cmc_snapshot_evidence import load_snapshot
from scripts.research.cmc_statistics import summarize
from scripts.research.run_cmc_diagnostic_report import run


def _endpoint(envelopes, cmc_id, product, observed):
    found = []
    for item in envelopes:
        for row in item["data"]["tracked_coinbase"]:
            if (isinstance(row, dict) and str(row.get("cmc_id")) == cmc_id
                    and row.get("coinbase_product") == product):
                try:
                    if _time(row["quote"]["received_utc"]) == observed:
                        found.append((item, row))
                except (KeyError, TypeError, ValueError):
                    continue
    if len(found) != 1:
        raise ValueError(f"endpoint capture not uniquely identified ({len(found)})")
    return found[0]


def run_qualified(directory, now):
    from scripts.research.cmc_completeness_adapter import audit_cohorts
    from scripts.research.cmc_daily_cohorts import build_cohorts
    from datetime import date, timedelta
    report = run(directory, now)
    envelopes = []
    cutoff = _time(report["as_of_utc"])
    # Reuse the base report's accepted evidence set, not a second directory scan.
    for source in report["source_files"]:
        item = load_snapshot(Path(source["file"]))
        if item["sha256"] != source["sha256"] or item["snapshot_utc"] > cutoff:
            raise ValueError("accepted_snapshot_changed_during_qualification")
        envelopes.append(item)
    by_sha = {item["sha256"]: item for item in envelopes}
    rows, qualified, counts = [], [], collections.Counter()
    for outcome in report["outcomes"]:
        if outcome.get("status") != "DIAGNOSTIC":
            continue
        horizon = outcome["horizon_days"]
        entry = {"status": "UNRESOLVED", "reasons": [], "flags": []}
        try:
            entry_env = by_sha[outcome["source_sha256"]]
            listing = next(r for r in entry_env["data"]["trending_hidden_boost"]
                           if r.get("type") == "listing" and str(int(r["cmc_id"])) == outcome["cmc_id"])
            product = listing["coinbase_product"]
            entry = qualify_capture(entry_env["data"], product, listing["coinbase"], "buy",
                                    identity_eligible=listing.get("identity_eligible"))
            exit_env, tracked = _endpoint(envelopes, outcome["cmc_id"], product, outcome["observation_time"])
            exit_ = qualify_capture(exit_env["data"], product, tracked["quote"], "sell",
                                    quantity=entry["quantity"], identity_eligible=tracked.get("identity_eligible"))
            if entry["quantity"] is None and "SIZE_UNVERIFIED_NO_QUANTITY" not in exit_["reasons"]:
                exit_["reasons"].append("SIZE_UNVERIFIED_NO_QUANTITY")
                exit_["status"] = "EXCLUDED"
        except (KeyError, StopIteration, TypeError, ValueError) as exc:
            exit_ = {"status": "EXCLUDED", "reasons": [f"LINKAGE_ERROR: {exc}"], "flags": []}
            if entry["status"] == "UNRESOLVED":
                entry["reasons"] = [f"LINKAGE_ERROR: {exc}"]
        for leg, result in (("entry", entry), ("exit", exit_)):
            for reason in result["reasons"]:
                counts[(horizon, leg, reason.split(":")[0])] += 1
            for flag in result.get("flags", []):
                counts[(horizon, leg, "flag:" + flag)] += 1
        ok = entry["status"] == exit_["status"] == "QUALIFIED"
        rows.append({"cmc_id": outcome["cmc_id"], "utc_day": outcome["utc_day"], "horizon_days": horizon,
                     "qualified": ok, "entry": entry, "exit": exit_})
        if ok:
            qualified.append(outcome)
    ready = report["statistics"].get("status") != "NOT_READY_90_DAYS"
    registered_stats = report["statistics"]
    qualified_stats = summarize(qualified, report["observed_utc_days"], ready)
    diag7 = sum(o.get("status") == "DIAGNOSTIC" and o.get("horizon_days") == 7 for o in report["outcomes"])
    cohort = build_cohorts(envelopes)
    if cohort["observed_utc_days"]:
        audit_start = date.fromisoformat(cohort["observed_utc_days"][0]) + timedelta(days=30)
        audit_end = (cutoff - timedelta(days=7, hours=12)).date() - timedelta(days=1)
        completeness = audit_cohorts(cohort, report["outcomes"], rows, cutoff,
                                    start_day=audit_start.isoformat(), end_day=audit_end.isoformat())
    else:
        completeness = {"status": "NO_OBSERVED_CALENDAR", "scoring_authorized": False}
    return {"artifact_type": "cmc_registered_and_qualified_views", "as_of_utc": report["as_of_utc"],
            "policy": {k: str(v) for k, v in POLICY.items()},
            "registered_view": {"statistics": registered_stats, "status_counts": report["status_counts"]},
            "qualified_view": {"statistics": qualified_stats,
                               "seven_day_diagnostic_outcomes": diag7,
                               "seven_day_qualified_outcomes": sum(o["horizon_days"] == 7 for o in qualified)},
            "exclusions_by_horizon_leg_reason": [{"horizon_days": h, "leg": l, "reason": r, "count": n}
                                                 for (h, l, r), n in sorted(counts.items(), key=str)],
            "qualification_rows": rows,
            "cohort_completeness": completeness,
            "gate_condition_descriptive": {"registered_all_ranges_above_zero": all_ranges_above_zero(registered_stats),
                                           "qualified_all_ranges_above_zero": all_ranges_above_zero(qualified_stats)},
            "primary_gate": "BLOCKED_STATISTICAL_METHOD_NOT_CERTIFIED",
            "scoring_authorized": False,
            "source_report_rejected_envelopes": report["rejected_envelopes"],
            "limits": ["displayed_size_not_fill_proof", "btc_benchmark_quotes_structural_only",
                       "clock_offset_unmeasured_beyond_book_age", "no_profitability_acceptance"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run_qualified(args.snapshots, datetime.fromisoformat(args.as_of.replace("Z", "+00:00")))
    with args.out.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False, default=lambda v: v.isoformat() if hasattr(v, "isoformat") else str(v))
    print(json.dumps({"qualified_view": result["qualified_view"]["seven_day_qualified_outcomes"],
                      "diagnostic_7d": result["qualified_view"]["seven_day_diagnostic_outcomes"]}))


if __name__ == "__main__":
    main()
