"""ED-002 pure shared-cash model. No data access, orders or promotion authority."""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import math

from scripts.research.corrected_research_math import rebalance


ZERO, ONE = Fraction(0), Fraction(1)
QUALIFICATION = "MODELLED_FULL_FILL_NOT_EXECUTION_OR_PROMOTION_EVIDENCE"


class Incomplete(ValueError):
    """Required evidence or ledger reconciliation is unavailable."""


def number(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal, Fraction)):
        raise ValueError("invalid_number")
    try:
        value = value if isinstance(value, Fraction) else Fraction(Decimal(str(value)))
    except (InvalidOperation, ValueError, OverflowError):
        raise ValueError("invalid_number") from None
    if value < 0 or (positive and not value):
        raise ValueError("invalid_number")
    return value


def timestamp(value):
    if type(value) is not int or value < 0:
        raise ValueError("invalid_timestamp")
    return value


def floor(value, step):
    return (value // step) * step


def ceil(value, step):
    return -((-value) // step) * step


def weights(value, symbols):
    if not isinstance(value, dict) or set(value) - set(symbols):
        raise ValueError("invalid_target_mapping")
    result = {s: number(value.get(s, 0)) for s in symbols}
    if sum(result.values(), ZERO) > ONE:
        raise ValueError("leveraged_target")
    return result


def rule_at(rules, symbol, decision_ms, execution_ms, venue, quote):
    try:
        available = [r for r in rules.get(symbol, [])
                     if timestamp(r["known_at_ms"]) <= decision_ms
                     and timestamp(r["valid_from_ms"]) <= execution_ms < timestamp(r["valid_until_ms"])]
    except (KeyError, TypeError, ValueError):
        raise Incomplete("missing_dated_rule:" + symbol) from None
    if not available:
        raise Incomplete("missing_dated_rule:" + symbol)
    latest = max(r["known_at_ms"] for r in available)
    chosen = [r for r in available if r["known_at_ms"] == latest]
    if len(chosen) != 1:
        raise Incomplete("ambiguous_dated_rule:" + symbol)
    r = chosen[0]
    if r.get("venue") != venue or r.get("quote") != quote or type(r.get("eligible")) is not bool:
        raise Incomplete("invalid_permission:" + symbol)
    try:
        return {**r, **{k: number(r[k], positive=k in ("lot_step", "quote_step"))
                        for k in ("lot_step", "quote_step", "minimum_qty", "minimum_notional_gross")}}
    except (KeyError, ValueError):
        raise Incomplete("missing_precision_or_minimum:" + symbol) from None


def marks_at(prices, valuation_marks, symbols, ts):
    result = {s: number(p, positive=True) for s, p in prices.items() if s in symbols}
    for symbol in symbols:
        if symbol in result:
            continue
        observations = [m for m in valuation_marks.get(symbol, [])
                        if timestamp(m["ts_ms"]) == ts and timestamp(m["known_at_ms"]) <= ts]
        if len(observations) == 1:
            result[symbol] = number(observations[0]["price"], positive=True)
    return result


def nav(state, marks):
    if any(q and s not in marks for s, q in state["units"].items()):
        raise Incomplete("unknown_held_valuation")
    return state["cash"] + sum((q * marks[s] for s, q in state["units"].items() if q), ZERO)


def order(symbol, side, quantity, price, rule, fee, slip):
    q = floor(quantity, rule["lot_step"])
    gross = q * price * (ONE + slip if side == "buy" else ONE - slip)
    if not q or q < rule["minimum_qty"] or gross < rule["minimum_notional_gross"]:
        return None
    charge = gross * fee
    raw = gross + charge if side == "buy" else gross - charge
    settled = ceil(raw, rule["quote_step"]) if side == "buy" else floor(raw, rule["quote_step"])
    return {"symbol": symbol, "side": side, "qty": q, "raw_price": price,
            "execution_price": gross / q, "fee": charge, "slippage": q * price * slip,
            "rounding": settled - raw if side == "buy" else raw - settled,
            "cash_delta": -settled if side == "buy" else settled,
            "fill_model": "MODELLED_FULL_FILL"}


def settle(state, fill, ts, source_ts, terminal=False):
    symbol, q = fill["symbol"], fill["qty"]
    old_q, old_basis = state["units"][symbol], state["basis"][symbol]
    if fill["side"] == "sell":
        if q > old_q:
            raise Incomplete("oversell")
        released = old_basis if q == old_q else old_basis * q / old_q
        basis_delta, delta_q = -released, -q
        realized = fill["cash_delta"] - released
    else:
        basis_delta, delta_q, realized = -fill["cash_delta"], q, ZERO
    cash = state["cash"] + fill["cash_delta"]
    if cash < 0:
        raise Incomplete("unaffordable_rounded_order")
    state["cash"] = cash
    state["units"][symbol] += delta_q
    state["basis"][symbol] += basis_delta
    for bucket in ("fee", "slippage", "rounding"):
        state[bucket] += fill[bucket]
    state["realized"] += realized
    state["trades"].append({**fill, "ts_ms": ts, "signal_bar_ts_ms": source_ts,
                            "basis_delta": basis_delta, "realized_pnl": realized,
                            "terminal": terminal, "cash_after": cash})


def joint_quantities(cash, units, prices, desired, fee, slip):
    """Refine the float helper's same piecewise equation with exact rationals."""
    equity = cash + sum((units[s] * prices[s] for s in prices), ZERO)
    if not equity:
        return dict(units)
    inputs = [cash, *units.values(), *prices.values(), *desired.values(), equity]
    try:
        supported = all(math.isfinite(float(x)) and (not x or float(x) > 0) for x in inputs)
    except OverflowError:
        supported = False
    if not supported:
        raise Incomplete("unsupported_helper_range")
    target_weights = {s: float(desired[s] / equity) for s in prices}
    helper_cash, proposal = rebalance(float(cash), {s: float(units[s]) for s in prices},
        {s: float(prices[s]) for s in prices}, target_weights, float(fee), float(slip))
    if not all(math.isfinite(x) and x >= 0 for x in [helper_cash, *proposal.values()]):
        raise Incomplete("invalid_helper_proposal")
    post = number(helper_cash) + sum((number(proposal[s]) * prices[s] for s in prices), ZERO)
    buy_cost, sell_cost = (ONE + slip) * (ONE + fee) - ONE, ONE - (ONE - slip) * (ONE - fee)
    for _ in range(len(prices) + 3):
        buying = {s for s in prices if desired[s] * post / equity >= units[s] * prices[s]}
        numerator, denominator = equity, equity
        for s in prices:
            coefficient = buy_cost if s in buying else -sell_cost
            numerator += coefficient * units[s] * prices[s]
            denominator += coefficient * desired[s]
        if denominator <= 0:
            raise Incomplete("invalid_joint_solution")
        post = numerator * equity / denominator
        if buying == {s for s in prices if desired[s] * post / equity >= units[s] * prices[s]}:
            return {s: desired[s] * post / equity / prices[s] for s in prices}
    raise Incomplete("joint_solution_not_reconciled")


def batch(state, target, opens, marks, rules, *, ts, source_ts, interval, terminal=False):
    """Plan then commit atomically. Excluded symbols' target is not redistributed."""
    profile = state["profile"]
    fee, slip = profile["fee"], profile["slip"]
    before = nav(state, marks)
    executable, exclusions = {}, []
    for s in profile["symbols"]:
        if not state["units"][s] and not target[s]:
            continue
        r = rule_at(rules, s, source_ts + interval, ts, profile["venue"], profile["quote"])
        if not r["eligible"] or s not in opens:
            exclusions.append({"symbol": s, "reason": "ineligible" if not r["eligible"] else "missing_execution_open"})
        else:
            executable[s] = r
    prices = {s: number(opens[s], positive=True) for s in executable}
    free = state["cash"] + sum((state["units"][s] * prices[s] for s in prices), ZERO)
    desired = {s: target[s] * before for s in prices}
    total = sum(desired.values(), ZERO)
    scale = min(ONE, free / total) if total else ONE
    desired = {s: value * scale for s, value in desired.items()}
    quantities = joint_quantities(state["cash"], {s: state["units"][s] for s in prices}, prices, desired, fee, slip) if prices else {}
    working, buys = deepcopy(state), []
    for s in sorted(prices):
        delta = quantities[s] - state["units"][s]
        if not delta:
            continue
        side = "buy" if delta > 0 else "sell"
        q = delta if delta > 0 else min(-delta, state["units"][s])
        fill = order(s, side, q, prices[s], executable[s], fee, slip)
        if fill is None:
            exclusions.append({"symbol": s, "reason": "below_minimum_or_lot_dust"})
        elif side == "sell":
            settle(working, fill, ts, source_ts, terminal)
        else:
            buys.append(fill)

    def resized(factor):
        return [f for original in buys if (f := order(original["symbol"], "buy", original["qty"] * factor,
                prices[original["symbol"]], executable[original["symbol"]], fee, slip)) is not None]

    if -sum((f["cash_delta"] for f in buys), ZERO) > working["cash"]:
        lo, hi = ZERO, ONE
        for _ in range(96):
            mid = (lo + hi) / 2
            if -sum((f["cash_delta"] for f in resized(mid)), ZERO) <= working["cash"]:
                lo = mid
            else:
                hi = mid
        reduced = resized(lo)
        remaining_symbols = {f["symbol"] for f in reduced}
        exclusions.extend({"symbol": f["symbol"], "reason": "below_minimum_after_cash_rescale"}
                          for f in buys if f["symbol"] not in remaining_symbols)
        buys = reduced
    for fill in buys:
        settle(working, fill, ts, source_ts, terminal)
    cost = sum((working[b] - state[b] for b in ("fee", "slippage", "rounding")), ZERO)
    if before - nav(working, marks) != cost:
        raise Incomplete("trade_nav_cost_identity")
    working["events"].append({"ts_ms": ts, "signal_bar_ts_ms": source_ts,
                              "excluded": exclusions, "terminal": terminal})
    return working


def validate_resume(state, profile):
    if state["profile"] != profile or not state["valid"]:
        raise ValueError("resume_requires_same_contract_and_complete_state")
    if (state["cash"] < 0 or any(q < 0 for q in state["units"].values())
            or any(b < 0 for b in state["basis"].values())
            or state["last_ts"] != state["history"][-1]["ts_ms"]
            or state["last_nav"] != nav(state, state["last_marks"])):
        raise ValueError("resume_nav_or_state_mismatch")
    pending = state["pending"]
    if pending is not None and (pending["signal_ms"] != state["last_ts"]
            or pending["execution_ms"] != state["last_ts"] + profile["interval"]
            or weights(pending["weights"], profile["symbols"]) != pending["weights"]):
        raise ValueError("resume_pending_mismatch")
    cash = profile["initial_cash"]
    units, basis = dict.fromkeys(profile["symbols"], ZERO), dict.fromkeys(profile["symbols"], ZERO)
    totals = dict.fromkeys(("fee", "slippage", "rounding", "realized"), ZERO)
    for f in state["trades"]:
        cash += f["cash_delta"]
        units[f["symbol"]] += f["qty"] if f["side"] == "buy" else -f["qty"]
        basis[f["symbol"]] += f["basis_delta"]
        for bucket in ("fee", "slippage", "rounding"):
            totals[bucket] += f[bucket]
        totals["realized"] += f["realized_pnl"]
    if cash != state["cash"] or units != state["units"] or basis != state["basis"] or any(totals[k] != state[k] for k in totals):
        raise ValueError("resume_ledger_mismatch")


def simulate_shared_next_open(frames, target_fn, *, symbols, venue, quote, interval_ms,
        initial_cash, fee_bps, slippage_bps, rules, target_contract_id,
        valuation_marks=None, state=None, terminal_liquidation=False):
    """Each frame has ts_ms/open/close maps; target_fn sees completed frames only.

    Missing prices are absent keys, never zero/forward-filled prices. Rule minima
    are model execution gross (before fees), not inferred venue specifications.
    Decimal input parsing and exact Fraction settlement prevent tolerance-funded
    orders. Returned state is reusable; money/quantity outputs are Fraction values.
    """
    return _simulate(frames, target_fn, symbols=symbols, venue=venue, quote=quote,
        interval_ms=interval_ms, initial_cash=initial_cash, fee_bps=fee_bps,
        slippage_bps=slippage_bps, rules=rules, target_contract_id=target_contract_id,
        valuation_marks=valuation_marks or {}, state=state, terminal_liquidation=terminal_liquidation)


def _simulate(frames, target_fn, *, symbols, venue, quote, interval_ms, initial_cash,
        fee_bps, slippage_bps, rules, target_contract_id, valuation_marks, state, terminal_liquidation):
    if not isinstance(symbols, (list, tuple)) or not all(isinstance(s, str) and s for s in symbols):
        raise ValueError("explicit_symbols_required")
    symbols = tuple(sorted(symbols))
    if (not symbols or len(set(symbols)) != len(symbols) or not all(isinstance(s, str) and s for s in symbols)
            or not callable(target_fn) or not all(isinstance(v, str) and v for v in (venue, quote, target_contract_id))
            or type(interval_ms) is not int or interval_ms <= 0 or type(terminal_liquidation) is not bool or not frames
            or not isinstance(rules, dict) or not isinstance(valuation_marks, dict)):
        raise ValueError("explicit_profile_required")
    fee, slip = number(fee_bps) / 10000, number(slippage_bps) / 10000
    if fee >= 1 or slip >= 1:
        raise ValueError("invalid_cost_range")
    profile = {"symbols": symbols, "venue": venue, "quote": quote, "interval": interval_ms,
               "initial_cash": number(initial_cash, positive=True), "fee": fee, "slip": slip,
               "target_contract_id": target_contract_id}
    frames = deepcopy(frames)
    for i, frame in enumerate(frames):
        ts = timestamp(frame["ts_ms"])
        if ts % interval_ms or (i and ts != frames[i - 1]["ts_ms"] + interval_ms):
            raise ValueError("incomplete_or_unordered_grid")
        for side in ("open", "close"):
            if not isinstance(frame[side], dict) or set(frame[side]) - set(symbols):
                raise ValueError("invalid_price_map")
            for value in frame[side].values():
                number(value, positive=True)
    if state is None:
        if len(frames) < 2:
            raise ValueError("warmup_and_execution_frames_required")
        state = {"profile": profile, "cash": profile["initial_cash"], "units": dict.fromkeys(symbols, ZERO),
                 "basis": dict.fromkeys(symbols, ZERO), "fee": ZERO, "slippage": ZERO, "rounding": ZERO,
                 "realized": ZERO, "trades": [], "events": [], "history": [], "decision_index": 0,
                 "valid": True, "last_nav": profile["initial_cash"], "pending": None}
        first = frames.pop(0)
        state["last_ts"] = first["ts_ms"]
        _decision(state, first, target_fn)
    else:
        state = deepcopy(state)
        validate_resume(state, profile)
        if frames[0]["ts_ms"] != state["last_ts"] + interval_ms:
            raise ValueError("noncontiguous_resume")
    start_nav, equity, reason = state["last_nav"], [], None
    for frame in frames:
        ts = frame["ts_ms"]
        pending, state["pending"] = state["pending"], None
        try:
            opening = marks_at(frame["open"], valuation_marks, symbols, ts)
            nav(state, opening)
            if pending is not None:
                if pending["execution_ms"] != ts or pending["signal_ms"] + interval_ms != ts:
                    raise ValueError("pending_decision_time_mismatch")
                state = batch(state, pending["weights"], frame["open"], opening, rules,
                              ts=ts, source_ts=pending["signal_ms"], interval=interval_ms)
            closing = marks_at(frame["close"], valuation_marks, symbols, ts + interval_ms)
            state["last_nav"] = nav(state, closing)
            state["last_marks"] = closing
            state["last_ts"] = ts
            equity.append({"close_ms": ts + interval_ms, "nav": state["last_nav"], "cash": state["cash"],
                           "units": deepcopy(state["units"])})
            _decision(state, frame, target_fn)
        except Incomplete as error:
            state["valid"], state["last_nav"], reason = False, None, str(error)
            state["events"].append({"ts_ms": ts, "reason": reason, "decision_expired": pending is not None})
            break
    marked = state["last_nav"]
    result = {"status": "COMPLETE" if state["valid"] else "INCOMPLETE", "qualification": QUALIFICATION,
              "reason": reason, "state": state, "equity": equity, "phase_start_nav": start_nav,
              "phase_profit": None if marked is None else marked - start_nav,
              "marked_nav": marked, "net_profit": None if marked is None else marked - profile["initial_cash"],
              "fees_quote": state["fee"], "slippage_quote": state["slippage"],
              "rounding_loss_quote": state["rounding"], "realized_pnl_quote": state["realized"],
              "unrealized_pnl": None if marked is None else marked - state["cash"] - sum(state["basis"].values(), ZERO),
              "terminal_liquidation": None}
    if terminal_liquidation and state["valid"]:
        try:
            terminal = batch(state, dict.fromkeys(symbols, ZERO), state["history"][-1]["close"], state["last_marks"], rules,
                ts=state["last_ts"] + interval_ms, source_ts=state["last_ts"], interval=interval_ms, terminal=True)
            result["terminal_liquidation"] = {"status": "COMPLETE", "qualification": "MODELLED_CLOSE_LIQUIDATION_NOT_NEXT_OPEN",
                "cash": terminal["cash"], "units": terminal["units"], "basis": terminal["basis"],
                "marked_nav": nav(terminal, state["last_marks"]),
                "net_profit": nav(terminal, state["last_marks"]) - profile["initial_cash"],
                "realized_pnl_quote": terminal["realized"], "fees_quote": terminal["fee"],
                "slippage_quote": terminal["slippage"], "rounding_loss_quote": terminal["rounding"],
                "profit_basis": "marked_residual_holdings" if any(terminal["units"].values()) else "liquidated_cash",
                "excluded": terminal["events"][-1]["excluded"],
                "trades": terminal["trades"][len(state["trades"]):]}
        except Incomplete as error:
            result["terminal_liquidation"] = {"status": "INCOMPLETE", "reason": str(error)}
    return result


def _decision(state, frame, target_fn):
    state["history"] = [*state["history"], deepcopy(frame)]
    context = {"history": deepcopy(state["history"]), "decision_index": state["decision_index"],
               "cash": state["cash"], "units": deepcopy(state["units"]), "basis": deepcopy(state["basis"]),
               "marked_nav": state["last_nav"], "close_ms": frame["ts_ms"] + state["profile"]["interval"]}
    target = target_fn(context)
    state["decision_index"] += 1
    if target is not None:
        state["pending"] = {"weights": weights(target, state["profile"]["symbols"]),
            "signal_ms": frame["ts_ms"], "execution_ms": frame["ts_ms"] + state["profile"]["interval"]}


def simulate_shared_comparison(frames, candidate_targets, *, btc_symbol, eth_symbol, mix_weights,
                               target_contract_id, states=None, **kwargs):
    """Same engine/costs/capital for cash, fixed-unit controls and caller candidate."""
    if btc_symbol == eth_symbol or {btc_symbol, eth_symbol} - set(kwargs["symbols"]) or set(mix_weights) - {btc_symbol, eth_symbol}:
        raise ValueError("explicit_comparison_symbols_required")
    recipe = {"btc_symbol": btc_symbol, "eth_symbol": eth_symbol,
              "mix_weights": weights(mix_weights, kwargs["symbols"])}
    controls = {"cash": {}, "hold_btc": {btc_symbol: 1}, "declared_btc_eth_cash_mix": mix_weights}
    callbacks = {name: (lambda c, w=deepcopy(w): w if c["decision_index"] == 0 else None) for name, w in controls.items()}
    callbacks["candidate"] = candidate_targets
    if states is not None:
        if not isinstance(states, dict) or set(states) != set(callbacks):
            raise ValueError("all_control_states_required")
        if any(not isinstance(s, dict) or s.get("comparison_contract") != recipe for s in states.values()):
            raise ValueError("comparison_contract_changed")
    results = {name: simulate_shared_next_open(frames, callback,
        target_contract_id=target_contract_id + ":" + name,
        state=None if states is None else states[name], **kwargs) for name, callback in callbacks.items()}
    for result in results.values():
        result["state"]["comparison_contract"] = deepcopy(recipe)
    return results
