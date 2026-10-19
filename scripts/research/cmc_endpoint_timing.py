"""Approved endpoint timing only; not a quote validator or profit evaluator."""
from datetime import timedelta, timezone


def select_endpoint(entry_time, horizon_days, observations):
    """Select (aware timestamp, reference), preserving missing endpoints explicitly."""
    if entry_time.utcoffset() is None or horizon_days not in (1, 7, 30):
        raise ValueError("aware entry time and registered horizon required")
    entry_time = entry_time.astimezone(timezone.utc)
    target = entry_time + timedelta(days=horizon_days)
    candidates = []
    seen = set()
    for timestamp, reference in observations:
        if timestamp.utcoffset() is None:
            raise ValueError("aware observation time required")
        timestamp = timestamp.astimezone(timezone.utc)
        if timestamp in seen:
            raise ValueError("duplicate observation time requires explicit resolution")
        seen.add(timestamp)
        if timestamp <= entry_time:
            continue
        distance = abs(timestamp - target)
        if distance <= timedelta(hours=12):
            candidates.append((distance, timestamp, reference))
    if not candidates:
        return {"status": "MISSING", "target_time": target,
                "reason": "no observation within approved 12-hour tolerance"}
    _, timestamp, reference = min(candidates, key=lambda row: (row[0], row[1]))
    return {"status": "SELECTED", "target_time": target,
            "observation_time": timestamp, "reference": reference,
            "elapsed_seconds": (timestamp - entry_time).total_seconds(),
            "deviation_seconds": (timestamp - target).total_seconds()}
