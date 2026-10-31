"""Pure seven-arm ED-002 comparison. Caller supplies all economic inputs."""
from copy import deepcopy

from services.backtest import delayed_signal_bridge as delayed
from services.backtest import frozen_signal_bridge as frozen
from services.backtest import shared_cash_research as ledger


CONTROL_NAMES = ("cash", "hold_btc", "declared_btc_eth_cash_mix")
ARM_NAMES = tuple(sorted(frozen.FAMILIES)) + ("incumbent",) + CONTROL_NAMES


class _FixedUnitsControl(delayed.DelayedSignalBridge):
    def __init__(self, *, name, target, **kwargs):
        super().__init__(family="ema_cross_default", **kwargs)
        self.target = ledger.weights(target, self.symbols)
        self.identity = {"policy": "ed002-initial-fixed-units-control-v1", "name": name,
            "initial_targets": self.target, "first_fill": "signal_start_plus_one_hour"}

    def __call__(self, context):
        frame, close = context["history"][-1], context["close_ms"]
        if close != frame["ts_ms"] + frozen.HOUR or set(context["units"]) != set(self.symbols):
            raise ledger.Incomplete("control_clock_or_universe_mismatch")
        required = {s for s in self.symbols if self.target[s] or context["units"][s]}
        self._check_outcome_frame(frame, required)
        target = deepcopy(self.target) if context["decision_index"] == 0 else None
        self.trace.append({"signal_bar_ts_ms": frame["ts_ms"],
            "strategy_signal_bar_ts_ms": None, "signal_close_ms": None,
            "receipt_cutoff_ms": close, "model_execution_ms": close,
            "actions": {s: "buy" if target and target[s] else "hold" for s in self.symbols},
            "readiness": dict.fromkeys(self.symbols, "predeclared_control"),
            "targets": target, "held_without_sell": []})
        return target


def _entry_evidence(result, expected, execution_ms):
    state = result.get("state")
    fills = [] if state is None else [t for t in state["trades"]
        if t["ts_ms"] == execution_ms and t["side"] == "buy" and t["qty"] > 0 and not t["terminal"]]
    actual = {t["symbol"] for t in fills}
    return {"status": "ACCEPTED" if set(expected) <= actual else "INCOMPLETE",
        "execution_ms": execution_ms, "expected_symbols": sorted(expected),
        "entered_symbols": sorted(actual), "missing_symbols": sorted(set(expected)-actual)}


def simulate_delayed_comparison(frames, *, symbols, observations, rules, venue, quote,
        snapshot_bytes, btc_symbol, eth_symbol, mix_weights, evaluation_start_ms,
        evaluation_end_ms, initial_cash, fee_bps, slippage_bps, target_contract_id,
        recent_listings=None, valuation_marks=None, states=None):
    """Seven alternative accounts, not additive capital or an activated study.

    A=evaluation_start, first fill E=A+1h, B=evaluation_end (exclusive).
    The first hour is cash-only for every arm and explicitly included in equity.
    Partial chunks preserve state but are not completed-period economic evidence.
    No parameters, market data, horizon, overhead or statistical method are chosen.
    """
    symbols = tuple(sorted(symbols))
    start, end = ledger.timestamp(evaluation_start_ms), ledger.timestamp(evaluation_end_ms)
    if (not frames or start % frozen.HOUR or end % frozen.HOUR or end <= start + frozen.HOUR
            or btc_symbol == eth_symbol or {btc_symbol, eth_symbol} - set(symbols)
            or set(mix_weights) - {btc_symbol, eth_symbol}):
        raise ValueError("explicit_comparison_clock_and_controls_required")
    mix = ledger.weights(mix_weights, symbols)
    if not mix[btc_symbol] or not mix[eth_symbol]:
        raise ValueError("both_declared_mix_assets_required")
    recipe = {"schema": "ed002-delayed-seven-arm-v1", "symbols": symbols,
        "btc_symbol": btc_symbol, "eth_symbol": eth_symbol, "mix": mix,
        "evaluation_start_ms": start, "first_execution_ms": start + frozen.HOUR,
        "evaluation_end_ms": end}
    controls = {"cash": {}, "hold_btc": {btc_symbol: 1},
                "declared_btc_eth_cash_mix": mix_weights}
    if states is None:
        if frames[0]["ts_ms"] != start or len(frames) < 2:
            raise ValueError("comparison_initial_frames_required")
    else:
        if not isinstance(states, dict) or set(states) != set(ARM_NAMES):
            raise ValueError("all_seven_comparison_states_required")
        for name, state in states.items():
            if (not isinstance(state, dict) or state.get("comparison_contract") != recipe
                    or not state.get("valid")):
                raise ValueError("comparison_carry_contract_or_entry_invalid")
            expected = [s for s, weight in controls.get(name, {}).items() if ledger.number(weight)]
            try:
                entry = _entry_evidence({"state": state}, expected, start + frozen.HOUR)
            except (KeyError, TypeError, ValueError):
                raise ValueError("comparison_carry_contract_or_entry_invalid") from None
            if entry["status"] != "ACCEPTED" or state.get("comparison_entry") != entry:
                raise ValueError("comparison_carry_contract_or_entry_invalid")
        clocks = {state["last_ts"] for state in states.values()}
        if len(clocks) != 1 or frames[0]["ts_ms"] != next(iter(clocks)) + frozen.HOUR:
            raise ValueError("comparison_carry_clock_mismatch")
    if frames[-1]["ts_ms"] + frozen.HOUR > end:
        raise ValueError("comparison_frames_beyond_endpoint")

    profile = dict(symbols=symbols, venue=venue, quote=quote, interval_ms=frozen.HOUR,
        initial_cash=initial_cash, fee_bps=fee_bps, slippage_bps=slippage_bps,
        rules=rules, valuation_marks=valuation_marks or {})
    inputs = dict(symbols=symbols, observations=observations, rules=rules, venue=venue,
        quote=quote, snapshot_bytes=snapshot_bytes, recent_listings=recent_listings,
        valuation_marks=valuation_marks)
    arms = {}
    for name in ARM_NAMES:
        if name in controls:
            bridge = _FixedUnitsControl(name=name, target=controls[name], **inputs)
        elif name == "incumbent":
            bridge = delayed.DelayedSignalBridge(incumbent=(btc_symbol, eth_symbol), **inputs)
        else:
            bridge = delayed.DelayedSignalBridge(family=name, **inputs)
        result = delayed.simulate_delayed_bridge(frames, bridge,
            state=None if states is None else states[name],
            target_contract_id=target_contract_id + ":" + name, **profile)
        state = result.get("state")
        expected = [s for s, weight in controls.get(name, {}).items() if ledger.number(weight)]
        entry = (_entry_evidence(result, expected, start + frozen.HOUR) if states is None
                 else deepcopy(states[name]["comparison_entry"]))
        if state is not None:
            state["comparison_contract"], state["comparison_entry"] = deepcopy(recipe), entry
        if states is None and state is not None:
            result["equity"].insert(0, {"close_ms": start + frozen.HOUR,
                "nav": ledger.number(initial_cash, positive=True),
                "cash": ledger.number(initial_cash, positive=True), "units": dict.fromkeys(symbols, ledger.ZERO)})
        result["ledger_status"] = result["status"]
        result["benchmark_entry"] = entry
        if entry["status"] != "ACCEPTED":
            result["status"] = "INCOMPLETE"
            result["reason"] = "benchmark_initial_entry_missing:" + ",".join(entry["missing_symbols"])
            result["marked_nav"] = result["net_profit"] = result["phase_profit"] = result["unrealized_pnl"] = None
        arms[name] = result

    period_complete = all(r.get("state") is not None and r["state"]["last_ts"] + frozen.HOUR == end
                          for r in arms.values())
    usable = period_complete and all(r["status"] == "COMPLETE" for r in arms.values())
    return {"status": "COMPLETE" if usable else "INCOMPLETE",
        "qualification": ledger.QUALIFICATION, "period_complete": period_complete,
        "economic_result_usable": usable, "comparison_contract": recipe,
        "arms": arms, "states": {name: r.get("state") for name, r in arms.items()},
        "net_profit_by_arm": {name: r["net_profit"] if usable else None for name, r in arms.items()},
        "initial_hour_cash_only": True, "statistics_calculated": False}
