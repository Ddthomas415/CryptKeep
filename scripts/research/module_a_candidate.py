"""Offline Module A candidate repair, not an activated study or trading engine.

Original external draft and its thresholds remain preserved. Missing observations
stop this candidate; they never imply delisting, recovery proceeds or executable
stale prices. All fills and balances here are MODELLED. No I/O on import.
"""
from __future__ import annotations

import math

from scripts.research.corrected_research_math import rebalance


class IncompleteSimulation(ValueError):
    """Retain account state when a required observation is unavailable."""

    def __init__(self, day, phase, asset, cash, units):
        super().__init__(f"INCOMPLETE: missing {phase} price for {asset} on day {day}")
        self.day, self.phase, self.asset = day, phase, asset
        self.cash, self.units = cash, dict(units)


def _positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def capped_weights(inv_vol, cap):
    """Preserved capped inverse-volatility allocation, with finite inputs."""
    if not _positive(cap) or cap > 1 or any(not _positive(v) for v in inv_vol.values()):
        raise ValueError("invalid allocation inputs")
    if not inv_vol:
        return {}
    if cap * len(inv_vol) < 1 - 1e-12:
        raise ValueError("cap too low for the number of assets")
    fixed, free, remaining = {}, dict(inv_vol), 1.0
    while free:
        total = sum(free.values())
        if not math.isfinite(total):
            raise ValueError("invalid allocation sum")
        trial = {a: remaining * score / total for a, score in free.items()}
        over = sorted(a for a, weight in trial.items() if weight > cap + 1e-12)
        if not over:
            fixed.update(trial)
            break
        for asset in over:
            fixed[asset] = cap
            remaining -= cap
            del free[asset]
    return fixed


def trailing_vol(closes, i, lookback):
    if type(lookback) is not int or lookback < 2 or not 0 <= i < len(closes):
        raise ValueError("invalid volatility window")
    if i < lookback:
        return None
    window = closes[i - lookback:i + 1]
    if any(not _positive(c) for c in window):
        return None
    returns = [math.log(window[k + 1] / window[k]) for k in range(lookback)]
    mean = sum(returns) / lookback
    variance = sum((r - mean) ** 2 for r in returns) / (lookback - 1)
    return math.sqrt(variance * 365)


def module_a_target(closes, i, eligible, lookback=60, cap=0.30, min_assets=4):
    """Illustrative original settings, not approved study parameters.

    The caller must supply point-in-time eligibility; this function does not
    establish historical listing status from candle availability.
    """
    if not _positive(cap) or cap > 1 or type(min_assets) is not int or min_assets < 1:
        raise ValueError("invalid target settings")
    inv = {}
    for asset in eligible:
        volatility = trailing_vol(closes[asset], i, lookback)
        if volatility and volatility > 0:
            inv[asset] = 1.0 / volatility
    if not inv:
        return {}
    if len(inv) < min_assets:
        return {a: min(cap, 1.0 / len(inv)) for a in inv}
    return capped_weights(inv, cap)


def _target(target_fn, day, assets):
    result = target_fn(day)
    if result is None:
        return None
    result = dict(result)
    if (set(result) - assets or any(not isinstance(w, (int, float)) or isinstance(w, bool)
            or not math.isfinite(w) or w < 0 for w in result.values())
            or sum(result.values()) > 1 + 1e-12):
        raise ValueError("long-only, unlevered target required")
    return result


def simulate(opens, closes, weekday, lo, hi, target_fn, fee, slip,
             recovery=None, cash0=5000.0, *, trace=None):
    """Return (close NAVs, annualized gross turnover, close decisions).

    Retains the original initial-close and subsequent Sunday-close schedule.
    Full-fill-only joint rebalance, sells-first modeled settlement; not venue
    settlement, capacity, shared-prefix or partial-fill proof. cash0 is a test
    fixture default, not operator capital. No terminal liquidation is implied.
    Missing held/required execution prices refuse; missing held close marks
    stop AFTER that day's opening execution, with state retained in the error.
    A trace exposes actual modeled cash steps for synthetic verification.
    """
    if recovery is not None:
        raise ValueError("recovery requires a separately frozen, dated settlement contract")
    if (set(opens) != set(closes) or not 0 <= lo < hi < len(weekday)
            or any(len(v) <= hi for v in list(opens.values()) + list(closes.values()))
            or not _positive(cash0) or not 0 <= fee < 1 or not 0 <= slip < 1):
        raise ValueError("invalid simulation inputs")
    cash, units, traded = cash0, {}, 0.0
    navs, decisions = [], []
    pending = _target(target_fn, lo, set(closes))
    decisions.append((lo, None if pending is None else dict(pending)))

    def record(**row):
        if trace is not None:
            trace.append({"evidence": "MODELLED", **row})

    for day in range(lo + 1, hi + 1):
        # Only opening observations enter execution; today's close is read below.
        if pending is not None:
            needed = set(units) | {a for a, weight in pending.items() if weight > 0}
            prices = {}
            for asset in sorted(needed):
                price = opens[asset][day]
                if not _positive(price):
                    raise IncompleteSimulation(day, "open", asset, cash, units)
                prices[asset] = price
            weights = {a: w for a, w in pending.items() if w > 0}
            before = cash + sum(units[a] * prices[a] for a in units)
            new_cash, new_units = rebalance(cash, units, prices, weights, fee, slip)
            fills = [(a, new_units.get(a, 0.0) - units.get(a, 0.0)) for a in prices]
            # Reconcile the helper against explicit sells-first cash credits/debits.
            ledger_cash = cash
            tolerance = 1e-10 * max(1.0, before)
            for asset, delta in sorted(fills, key=lambda row: (row[1] >= 0, row[0])):
                if delta == 0:
                    continue
                prior_cash = ledger_cash
                multiplier = (1 - slip) * (1 - fee) if delta < 0 else (1 + slip) * (1 + fee)
                ledger_cash -= delta * prices[asset] * multiplier
                if not math.isfinite(ledger_cash) or ledger_cash < -tolerance:
                    raise ValueError("unaffordable modeled fill")
                record(day=day, phase="fill", asset=asset, quantity=delta,
                       reference_price=prices[asset], cash_before=prior_cash,
                       cash_after=ledger_cash)
            if not math.isclose(ledger_cash, new_cash, rel_tol=1e-10, abs_tol=tolerance):
                raise ValueError("modeled cash does not reconcile")
            if not math.isfinite(new_cash) or new_cash < 0:
                raise ValueError("invalid modeled cash")
            traded += sum(abs(delta) * prices[a] for a, delta in fills) / before if before else 0.0
            cash, units = new_cash, {a: q for a, q in new_units.items() if q > 0}
            pending = None
        record(day=day, phase="open", cash=cash, units=dict(units))
        marks = {}
        for asset in sorted(units):
            price = closes[asset][day]
            if not _positive(price):
                raise IncompleteSimulation(day, "close", asset, cash, units)
            marks[asset] = price
        nav = cash + sum(q * marks[a] for a, q in units.items())
        if not math.isfinite(nav):
            raise ValueError("invalid modeled NAV")
        navs.append(nav)
        record(day=day, phase="close", cash=cash, units=dict(units), nav=nav)
        if day < hi and weekday[day] == 6:
            pending = _target(target_fn, day, set(closes))
            decisions.append((day, None if pending is None else dict(pending)))
    return navs, traded / ((hi - lo) / 365.0), decisions
