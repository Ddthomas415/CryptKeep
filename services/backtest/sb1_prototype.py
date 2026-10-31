"""NumPy-only SB-1 prototype. Supplied draws only; no RNG or promotion gate.

Corrected selector adapted from arch 7.2.0, (c) 2017 Kevin Sheppard.
License and attribution: docs/licenses/arch-7.2.0.txt.
The max-length/utility rules are CryptKeep hypotheses, not arch guarantees.
"""
import hashlib
import math
from numbers import Real

import numpy as np


DAY, DAYS, REPEATS, BATCH = 86400000, 182, 20000, 256
FAMILIES = ("breakout_default", "ema_cross_default", "mean_reversion_default")
ARMS = FAMILIES + ("incumbent", "cash", "hold_btc", "declared_btc_eth_cash_mix")


def stationary_length(series):
    """Corrected single-series stationary estimate; not a coverage result."""
    x = np.asarray(series)
    if x.shape != (DAYS,) or x.dtype.kind not in "fiu" or not np.isfinite(x).all():
        raise ValueError("finite_182_series_required")
    x = x.astype(np.float64)
    if np.all(x == x[0]):
        raise ValueError("constant_series_has_no_selector")
    n = len(x)
    with np.errstate(all="raise"):
        residual = x-x.mean()
        cap = np.ceil(min(3*np.sqrt(n), n/3))
        consecutive = max(5, int(np.log10(n)))
        max_lag = int(np.ceil(np.sqrt(n)))+consecutive
        threshold = 2*np.sqrt(np.log10(n)/n)
        covariance, correlations = np.zeros(max_lag+1), np.zeros(max_lag+1)
        first_quiet = None
        for lag in range(max_lag+1):
            left = residual[lag+1:] @ residual[lag+1:]
            right = residual[:-(lag+1)] @ residual[:-(lag+1)]
            cross = residual[lag:] @ residual[:n-lag]
            covariance[lag] = cross/n
            correlations[lag] = abs(cross)/np.sqrt(left*right)
            if lag >= consecutive and first_quiet is None and np.all(correlations[lag-consecutive:lag] < threshold):
                first_quiet = lag-consecutive
        width = min(2*max(first_quiet, 1), max_lag) if first_quiet is not None else max_lag
        g, long_variance = 0., covariance[0]
        for lag in range(1, width+1):
            taper = 1 if lag/width <= .5 else 2*(1-lag/width)
            g += 2*taper*lag*covariance[lag]
            long_variance += 2*taper*covariance[lag]
        estimate = min(((2*g*g)/(2*long_variance**2))**(1/3)*n**(1/3), cap)
    if not np.isfinite(estimate) or estimate < 0:
        raise ValueError("undefined_stationary_length")
    return float(estimate)


def select_mean_block(log_returns):
    logs = np.asarray(log_returns)
    if logs.shape != (DAYS, len(ARMS)) or logs.dtype.kind not in "fiu" or not np.isfinite(logs).all():
        raise ValueError("finite_seven_arm_logs_required")
    with np.errstate(all="raise"):
        try:
            features = {name: logs[:, i] for i, name in enumerate(ARMS)}
            features.update({name+"-incumbent": logs[:, i]-logs[:, 3] for i, name in enumerate(FAMILIES)})
            features.update({name+"_centered_square": (values-values.mean())**2
                             for name, values in list(features.items())})
        except FloatingPointError:
            return {"status": "INCOMPLETE", "reason": "unrepresentable_selector_features"}
    constants, estimates = [], {}
    for name, values in features.items():
        if np.all(values == values[0]):
            constants.append(name)
            continue
        try:
            estimates[name] = stationary_length(values)
        except (FloatingPointError, ValueError):
            return {"status": "INCOMPLETE", "reason": "undefined_selector:"+name,
                    "constant_columns": constants, "series_estimates": estimates}
    mean = max(1, math.ceil(max(estimates.values(), default=1)))
    result = {"status": "COMPLETE", "mean_block_length": mean, "effective_blocks": DAYS/mean,
        "constant_columns": constants, "series_estimates": estimates, "degenerate": not estimates}
    if DAYS/mean < 10:
        result.update(status="INCOMPLETE", reason="insufficient_effective_blocks")
    return result


def stationary_indices(starts, uniforms, mean_length):
    """Vectorized parity with arch's supplied-draw Python sampler; no RNG."""
    starts, uniforms = np.asarray(starts), np.asarray(uniforms)
    if (type(mean_length) is not int or mean_length < 1 or starts.ndim != 2 or starts.shape[1] < 1
            or starts.dtype.kind not in "iu" or uniforms.shape != starts.shape
            or uniforms.dtype.kind not in "fiu" or not np.isfinite(uniforms).all()
            or np.any(uniforms < 0) or np.any(uniforms >= 1)
            or np.any(starts < 0) or np.any(starts >= starts.shape[1])):
        raise ValueError("explicit_valid_stationary_draws_required")
    positions = np.arange(starts.shape[1])
    starts = starts.astype(np.int64, copy=False)
    restart = uniforms <= 1/mean_length
    restart[:, 0] = True
    origin = np.maximum.accumulate(np.where(restart, positions, 0), axis=1)
    return (np.take_along_axis(starts, origin, axis=1)+positions-origin) % starts.shape[1]


def _daily_values(panel):
    if not isinstance(panel, dict) or set(panel) != set(ARMS):
        raise ValueError("seven_daily_arms_required")
    calendars, values = [], []
    for arm in ARMS:
        records = panel[arm]
        if not isinstance(records, (list, tuple)) or len(records) != DAYS:
            raise ValueError("exact_182_day_panel_required")
        times, column = [], []
        for record in records:
            if not isinstance(record, dict) or set(record) != {"day_end_ms", "return"}:
                raise ValueError("explicit_daily_schema_required")
            ts, value = record["day_end_ms"], record["return"]
            if type(ts) is not int or ts < DAY or ts % DAY:
                raise ValueError("utc_day_end_required")
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real) or not math.isfinite(value) or value < -1:
                raise ValueError("invalid_daily_simple_return")
            times.append(ts)
            column.append(float(value))
        if any(b-a != DAY for a, b in zip(times, times[1:])):
            raise ValueError("contiguous_daily_calendar_required")
        if -1 in column and any(value != 0 for value in column[column.index(-1)+1:]):
            raise ValueError("nonzero_return_after_exhaustion")
        calendars.append(times)
        values.append(column)
    if any(times != calendars[0] for times in calendars[1:]):
        raise ValueError("paired_calendars_must_match")
    return np.array(values, dtype=np.float64).T, calendars[0]


def sb1_screen(panel, *, initial_cash, starts, uniforms):
    """Deterministic prototype evaluation of supplied draws, not an audit runner."""
    if (isinstance(initial_cash, (bool, np.bool_)) or not isinstance(initial_cash, Real)
            or not math.isfinite(initial_cash) or float(initial_cash) != 1000.):
        raise ValueError("adopted_1000_model_capital_required")
    values, dates = _daily_values(panel)
    output = {"method": "SB-1-prototype", "computation_status": "INCOMPLETE",
        "statistical_validation": "INCOMPLETE", "coverage_certified": False,
        "experiment_pass": None, "prototype_only": True, "contrasts": None,
        "days": DAYS, "repeats": REPEATS, "one_based_order_rank": (REPEATS+59)//60,
        "first_day_end_ms": dates[0], "last_day_end_ms": dates[-1]}
    if np.any(values == -1):
        output["reason"] = "account_exhaustion_not_supported_by_log_selector"
        return output
    logs = np.log1p(values)
    selection = select_mean_block(logs)
    output["selection"] = selection
    if selection["status"] != "COMPLETE":
        output["reason"] = selection["reason"]
        return output
    starts, uniforms = np.asarray(starts), np.asarray(uniforms)
    if starts.shape != (REPEATS, DAYS) or uniforms.shape != starts.shape:
        raise ValueError("exact_supplied_20000_by_182_draws_required")
    if (starts.dtype.kind not in "iu" or uniforms.dtype.kind not in "fiu"
            or np.any(starts < 0) or np.any(starts >= DAYS) or not np.isfinite(uniforms).all()
            or np.any(uniforms < 0) or np.any(uniforms >= 1)):
        raise ValueError("explicit_valid_stationary_draws_required")
    output["draws_sha256"] = {name: hashlib.sha256(memoryview(np.ascontiguousarray(array)).cast("B")).hexdigest()
                              for name, array in (("starts", starts), ("uniforms", uniforms))}
    differences = np.empty((REPEATS, len(FAMILIES)))
    try:
        with np.errstate(over="raise", invalid="raise", under="raise"):
            observed = float(initial_cash)*np.exp(logs.sum(axis=0))
            for first in range(0, REPEATS, BATCH):
                last = min(first+BATCH, REPEATS)
                indices = stationary_indices(starts[first:last], uniforms[first:last], selection["mean_block_length"])
                wealth = float(initial_cash)*np.exp(logs[indices].sum(axis=1))
                differences[first:last] = wealth[:, :3]-wealth[:, 3, None]
    except FloatingPointError:
        output["reason"] = "unrepresentable_wealth_no_draws_dropped"
        return output
    rank = output["one_based_order_rank"]-1
    lower = np.partition(differences, rank, axis=0)[rank]
    output["computation_status"] = "COMPLETE"
    output["contrasts"] = {name: {"observed_net_wealth_difference": float(observed[i]-observed[3]),
        "approximate_lower_bound": float(lower[i]), "lower_bound_exceeds_zero": bool(lower[i] > 0)}
        for i, name in enumerate(FAMILIES)}
    return output
