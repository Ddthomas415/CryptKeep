"""Normalize accepted cohort evidence for a read-only completeness audit."""
from datetime import date, timedelta, timezone

from scripts.research.cmc_cohort_completeness import audit_calendar


def audit_cohorts(cohorts, outcomes, qualifications, now, *, start_day, end_day):
    if now.utcoffset() is None:
        raise ValueError("aware cutoff required")
    now = now.astimezone(timezone.utc)
    observed = sorted(set(cohorts["observed_utc_days"]))
    if not observed:
        return {"status": "NO_OBSERVED_CALENDAR", "scoring_authorized": False}
    # A full UTC entry day must finish before its seven-day +12h window closes.
    earliest = date.fromisoformat(observed[0]) + timedelta(days=30)
    first, end = map(date.fromisoformat, (start_day, end_day))
    mature = (now - timedelta(days=7, hours=12)).date() - timedelta(days=1)
    if end < first:
        return {"status": "NO_MATURE_PRIMARY_WINDOW", "scoring_authorized": False}
    if first < earliest or end > mature:
        raise ValueError("declared window lacks history or maturity")

    def index(records):
        result = {}
        for row in records:
            day = date.fromisoformat(row["utc_day"])
            if not first <= day <= end or row.get("horizon_days") != 7:
                continue
            key = (row["utc_day"], row["cmc_id"])
            if key in result:
                raise ValueError("duplicate seven-day record")
            result[key] = row
        return result

    results, qualified = index(outcomes), index(qualifications)
    normalized, entry_exclusions = [], []
    for event in cohorts["events"]:
        day = date.fromisoformat(event["utc_day"])
        if not first <= day <= end:
            continue
        key = (event["utc_day"], event["cmc_id"])
        status = event["cohort_status"]
        if status == "REPEAT_APPEARANCE":
            eligibility = "EXCLUDED"
        elif status != "PRIMARY_COHORT_CANDIDATE":
            eligibility = "UNKNOWN"
        elif event["identity_eligible_at_first_observation"] is not True:
            eligibility = "EXCLUDED"
        else:
            eligibility = "ELIGIBLE"
        row = {"event_id": event["cmc_id"], "utc_day": event["utc_day"],
               "eligibility": eligibility, "outcome_status": "UNAVAILABLE"}
        outcome = results.get(key)
        if outcome is not None and outcome.get("source_sha256") != event["first_snapshot_sha256"]:
            raise ValueError("cohort outcome source mismatch")
        capture = qualified.get(key, {})
        if eligibility == "ELIGIBLE" and capture.get("entry", {}).get("status") == "EXCLUDED":
            row["eligibility"] = "EXCLUDED"
            entry_exclusions.append({"utc_day": key[0], "cmc_id": key[1],
                                     "reasons": capture["entry"].get("reasons", [])})
        if (eligibility == "ELIGIBLE" and outcome is not None
                and outcome.get("status") == "DIAGNOSTIC"
                and capture.get("qualified") is True
                and capture.get("entry", {}).get("status") == "QUALIFIED"
                and capture.get("exit", {}).get("status") == "QUALIFIED"):
            row.update(outcome_status="AVAILABLE", excess_return=outcome["excess_return"])
        normalized.append(row)
    result = audit_calendar(normalized, observed, first.isoformat(), end.isoformat(), mature.isoformat())
    result["window"] = {"start_day": first.isoformat(), "end_day": end.isoformat(),
                        "as_of_utc": now.isoformat()}
    result["scope"] = "qualified_mature_calendar_diagnostic_not_inference"
    result["entry_rule_exclusions"] = entry_exclusions
    return result
