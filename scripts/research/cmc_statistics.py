"""Entry-day clustered diagnostic intervals; never independent profitability proof."""
import math
import random
import statistics
from collections import Counter
from datetime import date, timedelta


def summarize(outcomes, observed_days, collection_ready, repeats=2000, seed=20261009):
    seven_day = Counter(row.get("status", "UNSPECIFIED") for row in outcomes
                        if row.get("horizon_days") == 7)
    coverage = {"seven_day_status_counts": dict(seven_day),
                "seven_day_records": sum(seven_day.values()),
                "available_seven_day_returns": seven_day["DIAGNOSTIC"],
                "unavailable_seven_day_returns": sum(seven_day.values())-seven_day["DIAGNOSTIC"],
                "pre_horizon_exclusions": dict(Counter(row.get("status", "UNSPECIFIED")
                    for row in outcomes if row.get("horizon_days") is None)),
                "scope": "record_counts_not_complete_cohort_or_missingness_adjustment"}
    if not collection_ready:
        return {"status": "NOT_READY_90_DAYS", "scoring_authorized": False, "coverage": coverage}
    groups = {}
    for row in outcomes:
        if row.get("status") == "DIAGNOSTIC" and row.get("horizon_days") == 7:
            value = row["excess_return"]
            if isinstance(value, bool) or not math.isfinite(value):
                raise ValueError("finite excess returns required")
            groups.setdefault(row["utc_day"], []).append(value)
    if len(groups) < 2:
        return {"status": "INSUFFICIENT_ENTRY_DAYS", "scoring_authorized": False, "coverage": coverage}
    if repeats < 100:
        raise ValueError("adequate bootstrap repeats required")
    days = sorted(set(observed_days))
    if not set(groups) <= set(days):
        raise ValueError("event day lacks observed list coverage")
    values = [value for group in groups.values() for value in group]

    def interval(units, block):
        if len(units) < 2*block:
            return {"status": "INSUFFICIENT_DAYS"}
        rng = random.Random(seed)
        samples, undefined = [], 0
        for _ in range(repeats):
            drawn = []
            while len(drawn) < len(units):
                start = rng.randrange(len(units)-block+1)
                drawn.extend(units[start:start+block])
            sample = [value for day in drawn[:len(units)] for value in groups.get(day, [])]
            if sample:
                samples.append(statistics.mean(sample))
            else:
                undefined += 1
        if undefined:
            return {"status": "INCOMPLETE", "undefined_replicates": undefined}
        samples.sort()
        return {"status": "DESCRIPTIVE", "p05": samples[int(repeats*.05)],
                "p95": samples[int(repeats*.95)], "block_days": block,
                "repeats": repeats, "seed": seed}

    primary = interval(sorted(groups), 1)
    parsed = [date.fromisoformat(day) for day in days]
    continuous = all(b-a == timedelta(days=1) for a,b in zip(parsed, parsed[1:]))
    sensitivities = {str(block): interval(days, block) if continuous else {"status": "MISSING_CALENDAR_COVERAGE"}
                     for block in (7,14,28)}
    return {"status": "DIAGNOSTIC", "primary_horizon_days": 7,
            "coverage": coverage,
            "events": len(values), "entry_days": len(groups),
            "mean_excess_return": statistics.mean(values),
            "median_excess_return": statistics.median(values),
            "registered_entry_day_bootstrap": primary,
            "serial_dependence_sensitivities_not_replacement_gate": sensitivities,
            "scoring_authorized": False, "limits": ["stationarity_unverified",
                "missing_outcome_selection_not_corrected",
                "calendar_blocks_include_partial_and_immature_observation_days",
                "intervals_describe_available_outcomes_not_full_cohort_uncertainty",
                "not_execution_or_profitability_acceptance"]}
