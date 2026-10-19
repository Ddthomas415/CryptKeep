"""Research corrections only; no production imports or exchange access."""

import math
import random
import statistics


def gap_aware_stop(entry, stop, opening, low):
    """Gross stop return; OHLC approximation, not a liquidity/fill guarantee."""
    if min(entry, stop, opening, low) <= 0 or not all(
        math.isfinite(x) for x in (entry, stop, opening, low)
    ):
        raise ValueError("prices must be finite and positive")
    if low > stop:
        return None
    return min(opening, stop) / entry - 1


def purged_training(events, split):
    """Events are (entry_time, label_end_time, ...); labels ending at split excluded."""
    return [event for event in events if event[0] < split and event[1] < split]


def corrected_event_exit(rows, signal, tp, sl, max_h, trail=None):
    """Next-open entry, gap-aware stop; missing/incomplete paths remain unknown.

    OHLC cannot prove queue position, intrabar ordering or execution liquidity.
    Stop is checked before target when both are touched, as in the frozen rule.
    """
    first = signal + 1
    if first >= len(rows) or rows[first][0] - rows[signal][0] != 3600:
        return None
    entry = rows[first][1]
    peak = entry
    start = rows[first][0]
    for j in range(first, len(rows)):
        if j > first and rows[j][0] - rows[j - 1][0] != 3600:
            return None
        opening, high, low = rows[j][1:4]
        held = (rows[j][0] - start) / 3600
        if held >= max_h:
            return opening / entry - 1, held, "time_next_open"
        stop = entry * (1 - sl) if sl else None
        if trail:
            stop = max(stop or 0, peak * (1 - trail))
        stopped = gap_aware_stop(entry, stop, opening, low) if stop else None
        if stopped is not None:
            return stopped, held, "stop_ohlc_model"
        if tp and high >= entry * (1 + tp):
            return tp, held, "target_ohlc_model"
        peak = max(peak, high)
    return None


def corrected_forward(rows, signal, hours):
    result = corrected_event_exit(rows, signal, None, None, hours)
    return None if result is None else result[0]


def paired_block_sharpe(left, right, block=56, repeats=2000, seed=7):
    """Paired calendar-day blocks preserve market-wide portfolio dependence.

    Inputs must be aligned complete daily portfolio returns, including cash days.
    Descriptive sensitivity only: does not undo prior data access or selection.
    """
    if len(left) != len(right) or len(left) < block or block < 2 or repeats < 20:
        raise ValueError("aligned returns and adequate sample/block/repeats required")
    if not all(math.isfinite(x) for x in list(left) + list(right)):
        raise ValueError("missing/non-finite return")

    def sharpe(values):
        sd = statistics.pstdev(values)
        if sd == 0:
            raise ValueError("Sharpe undefined for constant returns")
        return statistics.mean(values) / sd * math.sqrt(365)

    rng = random.Random(seed)
    differences = []
    undefined = 0
    observed = sharpe(left) - sharpe(right)
    n = len(left)
    for _ in range(repeats):
        indices = []
        while len(indices) < n:
            start = rng.randrange(n - block + 1)
            indices.extend(range(start, start + block))
        indices = indices[:n]
        try:
            differences.append(sharpe([left[i] for i in indices]) - sharpe([right[i] for i in indices]))
        except ValueError:
            undefined += 1
    if undefined:
        return {"status": "INCOMPLETE", "observed": observed, "p05": None, "p95": None,
                "undefined_replicates": undefined, "block_days": block,
                "repeats": repeats, "seed": seed, "not_independent_confirmation": True}
    differences.sort()
    return {"observed": sharpe(left) - sharpe(right), "p05": differences[int(repeats * .05)],
            "p95": differences[int(repeats * .95)], "block_days": block,
            "repeats": repeats, "seed": seed, "not_independent_confirmation": True}


def rebalance(cash, units, prices, weights, fee, slip):
    """Solve post-cost target equity, avoiding negative cash from full allocation."""
    if not math.isfinite(cash) or cash < 0 or set(units) - set(prices) or set(weights) - set(prices):
        raise ValueError("invalid cash or missing asset price")
    if any(not math.isfinite(p) or p <= 0 for p in prices.values()) or any(
        not math.isfinite(q) or q < 0 for q in units.values()
    ):
        raise ValueError("invalid price or quantity")
    if not 0 <= fee < 1 or not 0 <= slip < 1:
        raise ValueError("invalid costs")
    if any(w < 0 or not math.isfinite(w) for w in weights.values()) or sum(weights.values()) > 1 + 1e-12:
        raise ValueError("long-only, unlevered target required")
    before = cash + sum(units.get(a, 0) * prices[a] for a in prices)

    def cost(equity):
        total = 0.0
        for asset, price in prices.items():
            delta = weights.get(asset, 0) * equity - units.get(asset, 0) * price
            total += delta * ((1 + slip) * (1 + fee) - 1) if delta >= 0 else -delta * (1 - (1 - slip) * (1 - fee))
        return total

    lo, hi = 0.0, before
    for _ in range(80):
        mid = (lo + hi) / 2
        if mid + cost(mid) > before:
            hi = mid
        else:
            lo = mid
    after = (lo + hi) / 2
    new_units = {a: weights.get(a, 0) * after / price for a, price in prices.items()}
    return after * max(0.0, 1 - sum(weights.values())), new_units
