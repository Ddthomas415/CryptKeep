"""ED-002 approximate wealth screen. No data access or promotion authority."""
import math
from numbers import Real

import numpy as np


DAY = 86400000
DAYS, REPEATS, SEED = 182, 20000, 20261027
FAMILIES = ("breakout_default", "ema_cross_default", "mean_reversion_default")
ARMS = FAMILIES + ("incumbent", "cash", "hold_btc", "declared_btc_eth_cash_mix")
BLOCKS = (7, 14, 28)
BATCH = 256


def circular_indices(starts, block_days, days=DAYS):
    """Identical calendar indices are used for every arm of a replicate."""
    if (type(block_days) is not int or block_days not in BLOCKS
            or type(days) is not int or days < block_days):
        raise ValueError("invalid_block_grid")
    starts = np.asarray(starts)
    if (starts.ndim != 2 or starts.shape[1] != math.ceil(days / block_days)
            or starts.dtype.kind not in "iu" or np.any(starts < 0) or np.any(starts >= days)):
        raise ValueError("invalid_block_starts")
    return ((starts[:, :, None] + np.arange(block_days)) % days).reshape(len(starts), -1)[:, :days]


def _panel(daily_panel):
    if not isinstance(daily_panel, dict) or set(daily_panel) != set(ARMS):
        raise ValueError("all_seven_daily_arms_required")
    calendars, values = [], []
    for arm in ARMS:
        records = daily_panel[arm]
        if not isinstance(records, (list, tuple)) or len(records) != DAYS:
            raise ValueError("exactly_182_complete_days_required")
        times, returns = [], []
        for record in records:
            if not isinstance(record, dict) or set(record) != {"day_end_ms", "return"}:
                raise ValueError("explicit_daily_schema_required")
            ts, r = record["day_end_ms"], record["return"]
            if type(ts) is not int or ts < DAY or ts % DAY:
                raise ValueError("utc_day_end_required")
            if isinstance(r, (bool, np.bool_)) or not isinstance(r, Real) or not math.isfinite(r) or r < -1:
                raise ValueError("invalid_daily_simple_return")
            times.append(ts)
            returns.append(float(r))
        if any(b-a != DAY for a, b in zip(times, times[1:])):
            raise ValueError("contiguous_daily_calendar_required")
        if -1 in returns and any(r != 0 for r in returns[returns.index(-1)+1:]):
            raise ValueError("nonzero_return_after_exhaustion")
        calendars.append(times)
        values.append(returns)
    if any(times != calendars[0] for times in calendars[1:]):
        raise ValueError("paired_calendars_must_match")
    return np.array(values, dtype=np.float64).T, calendars[0]


def _wealth(log_returns, initial_cash, axis):
    with np.errstate(over="raise", invalid="raise", under="raise"):
        return initial_cash * np.exp(np.sum(log_returns, axis=axis))


def paired_wealth_screen(daily_panel, *, initial_cash, block_days=7):
    """Compute the proposed 1/60 lower percentile; NEVER certify its coverage.

    Caller must supply complete cost-inclusive daily returns anchored to cash
    before initial fills. Return validation cannot authenticate their provenance.
    Resampling portfolio returns does not recreate executable trade paths.
    """
    if (isinstance(initial_cash, (bool, np.bool_)) or not isinstance(initial_cash, Real)
            or not math.isfinite(initial_cash) or initial_cash <= 0 or float(initial_cash) != 1000.):
        raise ValueError("adopted_1000_model_capital_required")
    if type(block_days) is not int or block_days not in BLOCKS:
        raise ValueError("declared_block_length_required")
    values, times = _panel(daily_panel)
    output = {"computation_status": "INCOMPLETE", "statistical_validation": "INCOMPLETE",
        "coverage_certified": False, "experiment_pass": None,
        "days": DAYS, "repeats": REPEATS, "seed": SEED, "generator": "PCG64",
        "numpy_version": np.__version__, "block_days": block_days,
        "primary_method": block_days == 7, "one_sided_tail": "1/60",
        "one_based_order_rank": (REPEATS+59)//60,
        "first_day_end_ms": times[0], "last_day_end_ms": times[-1],
        "qualification": "APPROXIMATE_PORTFOLIO_RETURN_BOOTSTRAP_NOT_EXECUTABLE_PATH_OR_COVERAGE_PROOF",
        "contrasts": None}
    # -100% gives log wealth -infinity and exact zero, not a NaN replicate.
    with np.errstate(divide="ignore"):
        logs = np.log1p(values)
    try:
        observed = _wealth(logs, float(initial_cash), axis=0)
        differences = np.empty((REPEATS, len(FAMILIES)), dtype=np.float64)
        rng = np.random.Generator(np.random.PCG64(SEED))
        count = math.ceil(DAYS / block_days)
        for first in range(0, REPEATS, BATCH):
            size = min(BATCH, REPEATS-first)
            starts = rng.integers(0, DAYS, size=(size, count), dtype=np.int64)
            indices = circular_indices(starts, block_days)
            wealth = _wealth(logs[indices], float(initial_cash), axis=1)
            differences[first:first+size] = wealth[:, :3] - wealth[:, 3, None]
        if not np.isfinite(observed).all() or not np.isfinite(differences).all():
            raise FloatingPointError("nonfinite_wealth")
    except FloatingPointError:
        output["reason"] = "unrepresentable_wealth_no_replicates_dropped"
        return output
    rank = output["one_based_order_rank"] - 1
    bounds = np.partition(differences, rank, axis=0)[rank]
    output["computation_status"] = "COMPLETE"
    output["contrasts"] = {name: {"observed_net_wealth_difference": float(observed[i]-observed[3]),
        "approximate_lower_bound": float(bounds[i]), "lower_bound_exceeds_zero": bool(bounds[i] > 0)}
        for i, name in enumerate(FAMILIES)}
    return output
