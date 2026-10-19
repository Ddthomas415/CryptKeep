"""Calendar readiness only; collection continuity and statistical power are separate."""
from datetime import timedelta, timezone


def readiness(collection_start, event_time, now, horizon_days):
    if horizon_days not in (1, 7, 30):
        raise ValueError("registered horizon required")
    values = (collection_start, event_time, now)
    if any(value.utcoffset() is None for value in values):
        raise ValueError("aware times required")
    start, event, current = [value.astimezone(timezone.utc) for value in values]
    if not start <= event <= current:
        raise ValueError("collection/event/current ordering invalid")
    # Wait until the full approved endpoint window closes before choosing nearest.
    window_end = event + timedelta(days=horizon_days, hours=12)
    return {"collection_age_days": (current-start).total_seconds()/86400,
            "minimum_collection_age_reached": current >= start+timedelta(days=90),
            "endpoint_window_closed": current >= window_end,
            "endpoint_window_end": window_end, "scoring_authorized": False,
            "scope": "calendar_only_not_coverage_power_or_evidence_acceptance"}
