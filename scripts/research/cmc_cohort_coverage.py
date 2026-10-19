"""Daily sampled cohort coverage, using already validated list observations."""
from datetime import timedelta


def classify_appearance(event_day, cmc_id, daily_lists):
    """daily_lists maps UTC dates to sets of CMC IDs; absent dates are unknown."""
    if event_day not in daily_lists or str(cmc_id) not in {str(x) for x in daily_lists[event_day]}:
        return {"status": "NOT_OBSERVED", "missing_days": []}
    prior = [event_day - timedelta(days=n) for n in range(1, 31)]
    missing = sorted(day for day in prior if day not in daily_lists)
    appeared = any(str(cmc_id) in {str(x) for x in daily_lists[day]}
                   for day in prior if day in daily_lists)
    if appeared:
        return {"status": "REPEAT_APPEARANCE", "missing_days": missing}
    if missing:
        return {"status": "HISTORY_UNCERTAIN", "missing_days": missing}
    return {"status": "PRIMARY_COHORT_CANDIDATE", "missing_days": [],
            "coverage_scope": "daily_sampled_not_continuous_absence",
            "scoring_authorized": False}
