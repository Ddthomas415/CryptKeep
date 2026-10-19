"""Isolated conditional-method candidate; never authorizes market scoring."""
import hashlib
import json
import math
from datetime import date, timedelta
from pathlib import Path

import numpy as np


CONTRACT = Path(__file__).resolve().parents[2] / "docs/research/cmc_trending_log/paired_ratio_candidate_contract_20261010.md"
REPLICATES = 2000


def _count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def block_length(n):
    root = 1
    while root ** 3 < n:
        root += 1
    return max(7, root)


def sample_pairs(pairs, rng, length):
    n = len(pairs)
    starts = rng.integers(0, n, size=(n + length - 1) // length)
    return [pairs[(int(start) + offset) % n]
            for start in starts for offset in range(length)][:n]


def _ratio(pairs):
    total = math.fsum(pair[0] for pair in pairs)
    count = sum(pair[1] for pair in pairs)
    if count <= 0:
        raise ValueError("zero denominator")
    result = total / count
    if not math.isfinite(result):
        raise ValueError("nonfinite ratio")
    return result


def candidate_interval(audit, *, seed):
    """Consume the normalized completeness audit, not raw snapshots or prices."""
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise ValueError("nonnegative integer seed required")
    if audit.get("status") != "COMPLETE_FULL_COHORT":
        raise ValueError("complete cohort required")
    if (not _count(audit.get("eligible_events"))
            or not _finite_number(audit.get("event_weighted_mean"))):
        raise ValueError("invalid aggregate metadata")
    calendar = audit["calendar"]
    pairs = []
    previous = None
    for row in calendar:
        day = date.fromisoformat(row["day"])
        if previous is not None and day != previous + timedelta(days=1):
            raise ValueError("consecutive calendar required")
        previous = day
        if any(not _count(row.get(key)) for key in
               ("eligible", "excluded", "unknown", "missing_outcomes")):
            raise ValueError("invalid count metadata")
        if (row.get("status") != "COMPLETE_DAY" or row.get("list_observed") is not True
                or row.get("unknown") != 0 or row.get("missing_outcomes") != 0):
            raise ValueError("unresolved calendar day")
        pair = row["pair"]
        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
            raise ValueError("pair required")
        value, count = pair
        if (not _finite_number(value) or not _count(count)
                or count != row.get("eligible") or (count == 0 and value != 0)):
            raise ValueError("invalid calendar pair")
        pairs.append([value, count])
    n = len(pairs)
    length = block_length(n)
    if n < 2 * length:
        raise ValueError("insufficient computational blocks")
    if sum(pair[1] for pair in pairs) != audit.get("eligible_events"):
        raise ValueError("event count mismatch")
    try:
        estimate = _ratio(pairs)
    except (ValueError, OverflowError) as exc:
        raise ValueError("invalid original ratio") from exc
    if estimate != audit.get("event_weighted_mean"):
        raise ValueError("event mean mismatch")
    result = {
        "status": "INCOMPLETE", "event_weighted_mean": estimate,
        "interval": None, "calendar_days": n,
        "eligible_events": audit["eligible_events"], "block_length": length,
        "replicates": REPLICATES, "seed": seed,
        "input_sha256": hashlib.sha256(json.dumps(audit, sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
        "contract_sha256": hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "numpy_version": np.__version__,
        "python_version": __import__("platform").python_version(),
        "scoring_authorized": False,
        "qualification": "UNVALIDATED_CONDITIONAL_METHOD_CANDIDATE",
    }
    rng = np.random.Generator(np.random.PCG64(seed))
    differences = []
    try:
        for _ in range(REPLICATES):
            difference = _ratio(sample_pairs(pairs, rng, length)) - estimate
            if not math.isfinite(difference):
                raise ValueError("nonfinite centered replicate")
            differences.append(difference)
        differences.sort()
        low = estimate - differences[1900]
        high = estimate - differences[100]
        if not math.isfinite(low) or not math.isfinite(high):
            raise ValueError("nonfinite interval")
    except (ValueError, OverflowError) as exc:
        result["reason"] = str(exc)
        result["completed_replicates"] = len(differences)
        return result
    result.update(status="DEGENERATE" if low == high else "CANDIDATE_INTERVAL",
                  interval=[low, high], completed_replicates=REPLICATES,
                  reason="not_statistical_certification")
    return result
