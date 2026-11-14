"""ED-002 versioned synthetic policy core; no acquisition or activation authority."""
from __future__ import annotations

from bisect import bisect_left
from copy import deepcopy
from fractions import Fraction as F
import math

from services.backtest import delayed_signal_bridge as delayed
from services.backtest import frozen_signal_bridge as frozen
from services.backtest import shared_cash_research as ledger
from services.risk.exit_controls import evaluate_strategy_exit_stack


HOUR = frozen.HOUR
CONFIGURATIONS = {
    "breakout_default": ("breakout_default", False),
    "ema_cross_default": ("ema_cross_default", False),
    "mean_reversion_default": ("mean_reversion_default", False),
    "breakout_exit_unblocked": ("breakout_default", True),
    "ema_cross_exit_unblocked": ("ema_cross_default", True),
    "mean_reversion_exit_unblocked": ("mean_reversion_default", True),
}
EXIT_MODELS = ("S", "R-H1D")


def policy_recipe(configuration, exit_model):
    if not isinstance(configuration, str) or not isinstance(exit_model, str) or configuration not in CONFIGURATIONS or exit_model not in EXIT_MODELS:
        raise ValueError("unknown_dual_exit_policy")
    family, unblocked = CONFIGURATIONS[configuration]
    return {"schema": "ed002-dual-exit-core-v1", "configuration": configuration,
            "family": family, "exit_model": exit_model, "snapshot_sha256": frozen.SNAPSHOT_SHA256,
            "overlay": {"filters_apply_to_sell": False} if unblocked else {},
            "allocation": frozen.POLICY, "delay_ms": HOUR,
            "stack": {"stop_loss_pct": F(3, 100), "trailing_stop_pct": F(2, 100),
                      "take_profit_pct": F(6, 100), "max_bars_hold": 60}}


def derive_positions(trades, units, panel, signal_close_ms, *, price_peaks):
    """Rebuild active-cycle state from actual MODEL fills, never a saved peak."""
    close = ledger.timestamp(signal_close_ms)
    if type(price_peaks) is not bool or not isinstance(trades, list):
        raise ledger.Incomplete("missing_model_fill_evidence")
    cycles, quantities, previous = {}, dict.fromkeys(units, F(0)), -1
    for trade in trades:
        try:
            ts = ledger.timestamp(trade["ts_ms"])
            symbol, side = trade["symbol"], trade["side"]
            qty, price = ledger.number(trade["qty"], positive=True), ledger.number(trade["execution_price"], positive=True)
            if ts % HOUR or ts < previous or ts > close or symbol not in units or trade.get("terminal") is not False:
                raise ValueError("invalid_fill_clock_or_identity")
            previous = ts
            if side == "buy":
                if not quantities[symbol]:
                    cycles[symbol] = []
                quantities[symbol] += qty
                cycles[symbol].append((ts, side, qty, price))
            elif side == "sell" and qty <= quantities[symbol]:
                quantities[symbol] -= qty
                cycles[symbol].append((ts, side, qty, price))
                if not quantities[symbol]:
                    cycles.pop(symbol)
            else:
                raise ValueError("invalid_fill_side_or_oversell")
        except (KeyError, TypeError, ValueError, OverflowError) as error:
            raise ledger.Incomplete("invalid_model_fill_evidence") from error
    if quantities != {s: ledger.number(q) for s, q in units.items()}:
        raise ledger.Incomplete("model_fill_units_mismatch")
    positions = {}
    for symbol, fills in cycles.items():
        events = [(ts, 0, (side, qty, price)) for ts, side, qty, price in fills]
        if price_peaks:
            first = fills[0][0]
            times = panel.times.get(symbol, [])
            left, right = bisect_left(times, first), bisect_left(times, close)
            records = panel.rows.get(symbol, [])[left:right]
            if [r["row"][0] for r in records] != list(range(first, close, HOUR)):
                raise ledger.Incomplete("missing_exit_peak_history:" + symbol)
            for record in records:
                row, end = record["row"], record["row"][0] + HOUR
                try:
                    frozen.validate_bars([row], interval_ms=HOUR)
                    if ledger.timestamp(record["known_at_ms"]) > end + HOUR:
                        raise ValueError("late_peak_observation")
                except (ValueError, TypeError, IndexError) as error:
                    raise ledger.Incomplete("invalid_exit_peak_history:" + symbol) from error
                events.append((end, 1, ledger.number(row[4], positive=True)))
        state, held = None, F(0)
        for ts, kind, event in sorted(events, key=lambda e: (e[0], e[1])):
            if kind:
                if state is not None and ts > state["last_reference_fill_ts"]:
                    state["peak"] = max(state["peak"], event)
                continue
            side, qty, price = event
            if side == "buy":
                if state is None:
                    state = {"original_entry_fill_ts": ts, "last_reference_fill_ts": ts,
                             "reference": price, "peak": price}
                else:
                    state["reference"] = (held * state["reference"] + qty * price) / (held + qty)
                    state["last_reference_fill_ts"] = ts
                held += qty
            else:
                held -= qty
        positions[symbol] = {**state, "qty": held}
    return positions


def stack_exit(position, mark, signal_close_ms, strategy):
    """Decision clock T, never later execution E. No trigger-price fill promise."""
    ts = ledger.timestamp(signal_close_ms)
    original = ledger.timestamp(position["original_entry_fill_ts"])
    reference_ts = ledger.timestamp(position["last_reference_fill_ts"])
    age = ts - original
    if age < 0 or not original <= reference_ts <= ts:
        raise ledger.Incomplete("exit_observation_before_entry")
    mark = ledger.number(mark, positive=True)
    for key in ("reference", "peak", "qty"):
        ledger.number(position[key], positive=True)
    if ts <= reference_ts:
        return "time_stop" if age >= 60 * HOUR else None
    values = [position["reference"], position["peak"], position["qty"], mark]
    try:
        numeric = [float(v) for v in values]
        if not all(math.isfinite(v) and v > 0 for v in numeric):
            raise ValueError("unsupported_numeric_range")
    except (OverflowError, ValueError) as error:
        raise ledger.Incomplete("unsupported_exit_numeric_range") from error
    reference, peak, qty, price = numeric
    result = evaluate_strategy_exit_stack(entry_price=reference, current_price=price, qty=qty,
        strategy=strategy, side="long", stop_loss_pct=.03, trailing_stop_pct=.02,
        take_profit_pct=.06, trailing_peak_price=peak, bars_held=age // HOUR, max_bars_hold=60)
    return result["stack_rule"] if result["action"] == "exit" else None


def validate_fill_ledger(state, bridge):
    """Replay recorded batches with bound opens/rules and the existing settlement model."""
    try:
        profile = state["profile"]
        if (state.get("valid") is not True or profile.get("decision_trade_context") is not True
                or profile.get("model_event_schema") != "target-and-pre-units-v1"):
            raise ValueError("invalid_context_state")
        ledger.validate_resume(state, profile)
        symbols = profile["symbols"]
        history = state["history"]
        times = [ledger.timestamp(f["ts_ms"]) for f in history]
        if not times or times != list(range(times[0], times[-1] + HOUR, HOUR)) or any(t % HOUR for t in times):
            raise ValueError("invalid_carried_frame_grid")
        held, index = dict.fromkeys(symbols, F(0)), 0
        for frame in history:
            required = {s for s, q in held.items() if q}
            while index < len(state["trades"]) and state["trades"][index]["ts_ms"] <= frame["ts_ms"]:
                fill = state["trades"][index]
                required.add(fill["symbol"])
                held[fill["symbol"]] += fill["qty"] if fill["side"] == "buy" else -fill["qty"]
                index += 1
            bridge._check_outcome_frame(frame, required)
        if index != len(state["trades"]) or held != state["units"]:
            raise ValueError("carried_fill_grid_mismatch")
        last_marks = ledger.marks_at(history[-1]["close"], bridge.marks, symbols, times[-1] + HOUR)
        if ledger.nav(state, last_marks) != state["last_nav"]:
            raise ValueError("carried_source_nav_mismatch")
        scratch = {"profile": profile, "cash": profile["initial_cash"], "units": dict.fromkeys(symbols, F(0)),
                   "basis": dict.fromkeys(symbols, F(0)), "fee": F(0), "slippage": F(0), "rounding": F(0),
                   "realized": F(0), "trades": [], "events": []}
        frames = {f["ts_ms"]: f for f in state["history"]}
        for event in state["events"]:
            ts = ledger.timestamp(event["ts_ms"])
            source = ledger.timestamp(event["signal_bar_ts_ms"])
            if (event["terminal"] is not False or source + HOUR != ts
                    or event["pre_batch_units"] != scratch["units"]):
                raise ValueError("invalid_batch_event")
            target = ledger.weights(event["target_weights"], symbols)
            opening = ledger.marks_at(frames[ts]["open"], bridge.marks, symbols, ts)
            before = deepcopy(scratch["units"])
            scratch = ledger.batch(scratch, target, frames[ts]["open"], opening, bridge.rules,
                                   ts=ts, source_ts=source, interval=HOUR)
            scratch["events"][-1].update({"target_weights": target, "pre_batch_units": before})
            if scratch["events"][-1] != event:
                raise ValueError("batch_event_mismatch")
        keys = ("cash", "units", "basis", "fee", "slippage", "rounding", "realized", "trades")
        if any(scratch[k] != state[k] for k in keys):
            raise ValueError("batch_settlement_mismatch")
    except (KeyError, TypeError, ValueError, ArithmeticError) as error:
        raise ValueError("dual_exit_fill_ledger_mismatch") from error


def check_required_exits(events):
    for event in events:
        try:
            required = {s for s, q in event["pre_batch_units"].items() if q and not event["target_weights"][s]}
            if any(e["symbol"] in required and e["reason"] in {"ineligible", "missing_execution_open"}
                   for e in event["excluded"]):
                raise ledger.Incomplete("required_held_exit_unavailable")
        except (KeyError, TypeError) as error:
            raise ledger.Incomplete("missing_required_exit_evidence") from error


class DualExitBridge(delayed.DelayedSignalBridge):
    """Six explicit configs over the unchanged frozen snapshot, one policy per wallet."""

    def __init__(self, *, configuration, exit_model, **inputs):
        self.recipe = policy_recipe(configuration, exit_model)
        super().__init__(family=self.recipe["family"], **inputs)
        self.config["strategy"].update(self.recipe["overlay"])
        self._config_digest = frozen.digest(self.config)
        self.identity = {**self.identity, "dual_exit_recipe": deepcopy(self.recipe)}
        self._recipe_digest = frozen.digest(self.recipe)

    def positions(self, trades, units, signal_close_ms):
        return derive_positions(trades, units, self.panel, signal_close_ms,
                                price_peaks=self.recipe["exit_model"] == "R-H1D")

    def __call__(self, context):
        if frozen.digest(self.recipe) != self._recipe_digest:
            raise ValueError("dual_exit_recipe_changed")
        if "model_trades" not in context:
            raise ledger.Incomplete("explicit_model_fill_context_required")
        if "model_events" not in context:
            raise ledger.Incomplete("explicit_model_exit_context_required")
        check_required_exits(context["model_events"])
        super().__call__(context)
        trace = self.trace[-1]
        close, cutoff = trace["signal_close_ms"], trace["receipt_cutoff_ms"]
        positions = self.positions(context["model_trades"], context["units"], close)
        source_actions, actions = deepcopy(trace["actions"]), deepcopy(trace["actions"])
        marks, reasons = {}, {}
        for symbol in self.symbols:
            if context["units"][symbol] or actions[symbol] == "buy":
                rows = frozen.HourlyPanel.window(self.panel, symbol, close, 1, available_by_ms=cutoff)
                if rows is None:
                    raise ledger.Incomplete("missing_dual_exit_mark:" + symbol)
                marks[symbol] = ledger.number(rows[-1][4], positive=True)
            if symbol in positions:
                rule = ledger.rule_at(self.rules, symbol, close, close, self.venue, self.quote)
                if not rule["eligible"]:
                    raise ledger.Incomplete("held_exit_permission_unavailable:" + symbol)
                if self.recipe["exit_model"] == "R-H1D":
                    reason = stack_exit(positions[symbol], marks[symbol], close, self.config["strategy"]["name"])
                    if reason:
                        actions[symbol], reasons[symbol] = "sell", reason
        signal_context = {**context, "marked_nav": ledger.number(context["cash"]) + sum(
            (ledger.number(q) * marks[s] for s, q in context["units"].items() if q), F(0))}
        target = frozen.event_targets(signal_context, actions, marks)
        trace.update({"strategy_actions": source_actions, "actions": actions, "exit_rules": reasons,
                      "targets": deepcopy(target), "derived_positions": positions,
                      "held_without_sell": [s for s, q in context["units"].items() if q and actions[s] != "sell"]})
        return target


def simulate_dual_exit_bridge(frames, bridge, *, state=None, **profile):
    """Usable policy core; not the event-aware 16-arm comparison or study activation."""
    if not isinstance(bridge, DualExitBridge) or profile.get("terminal_liquidation", False):
        raise ValueError("explicit_dual_exit_primary_marked_policy_required")
    if state is not None:
        validate_fill_ledger(state, bridge)
        expected = {"recipe": bridge.recipe, "signal_close_ms": state["last_ts"],
                    "positions": bridge.positions(state["trades"], state["units"], state["last_ts"])}
        if state.get("dual_exit") != expected:
            raise ValueError("dual_exit_resume_state_mismatch")
    result = delayed.simulate_delayed_bridge(frames, bridge, state=state, decision_trade_context=True, **profile)
    current = result.get("state")
    if current is not None and current["valid"]:
        current["dual_exit"] = {"recipe": deepcopy(bridge.recipe), "signal_close_ms": current["last_ts"],
                               "positions": bridge.positions(current["trades"], current["units"], current["last_ts"])}
    traces = {t["signal_bar_ts_ms"]: t for t in current["signal_bridge"]["decisions"]} if current else {}
    for trade in result.get("bridge_trades", []):
        note = traces.get(trade["signal_bar_ts_ms"], {})
        trade["strategy_action"] = note.get("strategy_actions", {}).get(trade["symbol"])
        trade["exit_rule"] = note.get("exit_rules", {}).get(trade["symbol"])
    result.update({"policy_recipe": deepcopy(bridge.recipe), "scope": "SYNTHETIC_DUAL_EXIT_POLICY_CORE",
                   "event_policy_implemented": False, "comparison_ready": False, "study_ready": False})
    return result
