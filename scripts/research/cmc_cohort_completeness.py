"""Read-only audit of an explicitly declared mature cohort; no inference gate."""
import math
from datetime import date, timedelta


def audit_calendar(events, observed_days, start_day, end_day, mature_through):
    """Accept normalized eligibility records, not raw logger snapshots.

    Eligibility is ELIGIBLE, EXCLUDED or UNKNOWN. Eligible records require an
    available finite excess_return. The caller must derive maturity from the
    registered endpoint window; this helper never infers it from price data.
    """
    start, end, mature = map(date.fromisoformat,
                             (start_day, end_day, mature_through))
    if start > end or end > mature:
        raise ValueError("window must be ordered and fully mature")
    days = []
    current = start
    while current <= end:
        days.append(current.isoformat())
        current += timedelta(days=1)
    observed = set(observed_days)
    for day in observed:
        date.fromisoformat(day)
    rows = {day: {"day": day, "list_observed": day in observed,
                  "eligible": 0, "excluded": 0, "unknown": 0,
                  "missing_outcomes": 0, "sum": 0.0} for day in days}
    seen = set()
    for event in events:
        day = event["utc_day"]
        date.fromisoformat(day)
        if day not in rows:
            continue  # No return is inspected outside the mature window.
        identity = (day, event["event_id"])
        if identity in seen:
            raise ValueError("duplicate event")
        seen.add(identity)
        row = rows[day]
        eligibility = event["eligibility"]
        if eligibility == "UNKNOWN":
            row["unknown"] += 1
        elif eligibility == "EXCLUDED":
            row["excluded"] += 1
        elif eligibility == "ELIGIBLE":
            row["eligible"] += 1
            value = event.get("excess_return")
            if (event.get("outcome_status") != "AVAILABLE"
                    or isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value)):
                row["missing_outcomes"] += 1
            else:
                row["sum"] += value
                if not math.isfinite(row["sum"]):
                    raise ValueError("return sum overflow")
        else:
            raise ValueError("explicit eligibility required")
    complete = True
    for row in rows.values():
        valid = (row["list_observed"] and not row["unknown"]
                 and not row["missing_outcomes"])
        row["pair"] = [row["sum"], row["eligible"]] if valid else None
        row["status"] = "COMPLETE_DAY" if valid else "UNRESOLVED_DAY"
        complete = complete and valid
        del row["sum"]
    count = sum(row["eligible"] for row in rows.values())
    mean = None
    if complete and count:
        try:
            total = math.fsum(row["pair"][0] for row in rows.values())
        except OverflowError as exc:
            raise ValueError("aggregate return sum overflow") from exc
        mean = total / count
        if not math.isfinite(mean):
            raise ValueError("nonfinite event mean")
    return {"status": "COMPLETE_FULL_COHORT" if complete else "INCOMPLETE_FULL_COHORT",
            "calendar": list(rows.values()), "eligible_events": count,
            "unknown_events": sum(row["unknown"] for row in rows.values()),
            "missing_outcomes": sum(row["missing_outcomes"] for row in rows.values()),
            "event_weighted_mean": mean, "scoring_authorized": False,
            "limits": ["normalized_input_not_identity_verification",
                       "caller_declared_maturity", "no_statistical_certification"]}
