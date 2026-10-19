"""Fixed vectorized synthetic candidates, isolated from CMC scoring."""
import numpy as np

METHODS = ("entry_day", "block28", "block56")


def interval(history, method, seed, repeats=2000):
    if method not in METHODS or repeats < 100:
        raise ValueError("unknown method or insufficient resamples")
    if history["refusal_only"]:
        return {"status": "REFUSED_UNSUPPORTED_MODEL"}
    if not np.all(history["observed"]):
        return {"status": "REFUSED_MISSING_OUTCOMES"}
    days = history["days"]
    index, values = history["day_index"], history["truth"]
    if not np.isfinite(values).all():
        raise ValueError("finite outcomes required")
    totals = np.bincount(index, weights=values, minlength=days)
    counts = np.bincount(index, minlength=days)
    if method == "entry_day":
        units = np.flatnonzero(counts)
        totals, counts = totals[units], counts[units]
        block = 1
    else:
        block = int(method[5:])
    n = len(counts)
    if n < 2*block:
        return {"status": "INSUFFICIENT_DAYS"}
    rng = np.random.Generator(np.random.PCG64(seed))
    samples = np.empty(repeats)
    offsets = np.arange(block)
    # Bound memory independently of the eventual confirmation-grid size.
    for begin in range(0, repeats, 128):
        end = min(begin+128, repeats)
        starts = rng.integers(0, n-block+1, size=(end-begin, (n+block-1)//block))
        selected = (starts[:, :, None]+offsets).reshape(end-begin, -1)[:, :n]
        denominator = counts[selected].sum(axis=1)
        if np.any(denominator == 0):
            return {"status": "INCOMPLETE_EMPTY_RESAMPLE"}
        samples[begin:end] = totals[selected].sum(axis=1)/denominator
    samples.sort()
    return {"status": "DESCRIPTIVE", "p05": float(samples[int(.05*repeats)]),
            "p95": float(samples[int(.95*repeats)]), "repeats": repeats,
            "block_days": block, "method": method,
            "mean": float(values.mean()), "events": len(values)}
