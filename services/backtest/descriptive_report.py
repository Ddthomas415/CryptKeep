"""Pure ED-002 ledger reporting, not inference, execution or a strategy run."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction as F

from services.backtest import delayed_research_comparison as comparison
from services.backtest import shared_cash_research as ledger


HOUR, DAY = 3_600_000, 86_400_000
COSTS = {"primary": F(50, 10000), "stress": F(90, 10000)}
CONTROLS = ("cash", "hold_btc", "declared_btc_eth_cash_mix", "incumbent")
BUCKETS = ("fee", "slippage", "rounding")


def _require(condition, reason):
    if not condition:
        raise ledger.Incomplete(reason)


def _risk(curve):
    peak, peak_time = curve[0]["nav"], curve[0]["close_ms"]
    drawdown, duration, underwater = F(0), 0, False
    for row in curve[1:]:
        if row["nav"] >= peak:
            if underwater:
                duration = max(duration, row["close_ms"] - peak_time)
            peak, peak_time = row["nav"], row["close_ms"]
            underwater = False
        else:
            drawdown = max(drawdown, (peak - row["nav"]) / peak)
            duration = max(duration, row["close_ms"] - peak_time)
            underwater = True
    return {"maximum_drawdown_fraction": drawdown,
            "maximum_underwater_hours": F(duration, HOUR)}


def _coverage(state, symbols):
    decisions = (state or {}).get("signal_bridge", {}).get("decisions", [])
    rows = []
    for symbol in symbols:
        counts = Counter(d.get("readiness", {}).get(symbol, "unreported") for d in decisions)
        rows.append({"symbol": symbol, "ready_decisions": counts.get("ready", 0),
                     "recorded_readiness_counts": dict(sorted(counts.items()))})
    return rows


def _diagnostic(arm, symbols):
    state, equity = arm.get("state"), arm.get("equity", [])
    return {"coverage": _coverage(state, symbols), "source_status": arm.get("status"),
            "source_reason": arm.get("reason"),
            "last_recorded_equity_not_completion": deepcopy(equity[-1]) if equity else None,
            "recorded_cost_totals": {key: arm.get(key) for key in
                ("fees_quote", "slippage_quote", "rounding_loss_quote")}}


def _reconcile_arm(chunks, name, recipe, symbols, fee, valuation_marks):
    arm = chunks[-1]["arms"][name]
    state = arm.get("state")
    _require(state is not None and arm.get("status") == "COMPLETE" and state.get("valid"),
             "incomplete_arm_or_missing_state")
    start, end = recipe["evaluation_start_ms"], recipe["evaluation_end_ms"]
    execution, midpoint = start + HOUR, (start + end) // 2
    profile = state["profile"]
    _require(profile["symbols"] == symbols and profile["venue"] == "coinbase"
             and profile["quote"] == "USD" and profile["interval"] == HOUR
             and profile["initial_cash"] == 1000 and profile["fee"] == fee
             and profile["slip"] == F(25, 10000), "unexpected_model_profile")
    _require(state.get("comparison_contract") == recipe and state["last_ts"] + HOUR == end,
             "incomplete_period_or_recipe")
    expected = ([recipe["btc_symbol"]] if name == "hold_btc" else
                [recipe["btc_symbol"], recipe["eth_symbol"]]
                if name == "declared_btc_eth_cash_mix" else [])
    entry = comparison._entry_evidence(arm, expected, execution)
    _require(entry["status"] == "ACCEPTED" and arm.get("benchmark_entry") == entry
             and state.get("comparison_entry") == entry, "benchmark_entry_not_reconciled")
    ledger.validate_resume(state, profile)

    equity = []
    for chunk in chunks:
        current = chunk["arms"][name]
        carried = current.get("state")
        _require(carried is not None and carried.get("valid") and carried["profile"] == profile
                 and carried.get("comparison_contract") == recipe, "invalid_chunk_state")
        ledger.validate_resume(carried, profile)
        upto = carried["last_ts"]
        _require(carried["history"] == [r for r in state["history"] if r["ts_ms"] <= upto]
                 and carried["trades"] == [t for t in state["trades"] if t["ts_ms"] <= upto],
                 "chunk_history_or_trade_prefix_mismatch")
        rows = current["equity"]
        _require(bool(rows) and rows[-1]["close_ms"] == upto + HOUR
                 and rows[-1]["nav"] == carried["last_nav"], "chunk_equity_endpoint_mismatch")
        equity.extend(rows)
    _require([r["close_ms"] for r in equity] == list(range(execution, end + HOUR, HOUR)),
             "missing_duplicate_or_unordered_equity")
    _require(equity[0]["cash"] == equity[0]["nav"] == 1000
             and not any(equity[0]["units"].values()), "initial_cash_hour_missing")
    decisions = state.get("signal_bridge", {}).get("decisions", [])
    _require(len(decisions) == state["decision_index"], "missing_decision_trace")
    triggers = {d["signal_bar_ts_ms"]: d for d in decisions}
    _require(len(triggers) == len(decisions), "duplicate_decision_trace")
    frames = {r["ts_ms"] + HOUR: r for r in state["history"]}
    _require(len(frames) == len(state["history"]), "duplicate_mark_frame")

    replay = {"cash": F(1000), "units": dict.fromkeys(symbols, F(0)),
              "basis": dict.fromkeys(symbols, F(0)), "realized": F(0), "trades": [],
              **dict.fromkeys(BUCKETS, F(0))}
    per_symbol = {s: {"symbol": s, "realized_pnl": F(0), "reference_turnover": F(0),
                     "incidental_reference_turnover": F(0), "fills": 0,
                     **dict.fromkeys(BUCKETS, F(0))} for s in symbols}
    cycle_pnl, cycles = dict.fromkeys(symbols, F(0)), []
    trades = state["trades"]
    _require([t["ts_ms"] for t in trades] == sorted(t["ts_ms"] for t in trades),
             "unordered_trade_journal")
    next_trade, snapshots, curve = 0, {}, [{"close_ms": start, "nav": F(1000), "cash": F(1000)}]
    initial = {s: F(0) for s in symbols}
    snapshots[start] = {"contribution": initial, "costs": dict.fromkeys(BUCKETS, F(0))}
    exposed, exposure_sum = 0, F(0)
    for row in equity:
        close = row["close_ms"]
        while next_trade < len(trades) and trades[next_trade]["ts_ms"] < close:
            trade = trades[next_trade]
            _require(execution <= trade["ts_ms"] < end and trade.get("terminal") is False
                     and trade["symbol"] in per_symbol and trade["side"] in ("buy", "sell"),
                     "invalid_primary_trade")
            qty = ledger.number(trade["qty"], positive=True)
            # Recheck reported settlement without claiming original lot eligibility.
            rule = {"lot_step": qty, "quote_step": F(1, 100),
                    "minimum_qty": F(0), "minimum_notional_gross": F(0)}
            fill = ledger.order(trade["symbol"], trade["side"], qty,
                ledger.number(trade["raw_price"], positive=True), rule, fee, profile["slip"])
            _require(all(trade.get(k) == v for k, v in fill.items()), "trade_cost_model_mismatch")
            ledger.settle(replay, fill, trade["ts_ms"], trade["signal_bar_ts_ms"])
            _require(replay["trades"][-1] == trade, "trade_basis_or_cash_mismatch")
            symbol = trade["symbol"]
            ps = per_symbol[symbol]
            for bucket in BUCKETS:
                ps[bucket] += trade[bucket]
            ps["realized_pnl"] += trade["realized_pnl"]
            ps["reference_turnover"] += qty * trade["raw_price"]
            ps["fills"] += 1
            trigger = triggers.get(trade["signal_bar_ts_ms"])
            _require(trigger is not None, "missing_trade_trigger")
            if symbol in trigger.get("held_without_sell", []):
                ps["incidental_reference_turnover"] += qty * trade["raw_price"]
            cycle_pnl[symbol] += trade["realized_pnl"]
            if not replay["units"][symbol]:
                cycles.append({"symbol": symbol, "closed_at_ms": trade["ts_ms"],
                               "net_realized_pnl": cycle_pnl[symbol]})
                cycle_pnl[symbol] = F(0)
            next_trade += 1
        _require(set(row["units"]) == set(symbols) and row["units"] == replay["units"]
                 and row["cash"] == replay["cash"], "hourly_wallet_mismatch")
        marks = ledger.marks_at(frames[close]["close"], valuation_marks, symbols, close)
        value = ledger.nav(replay, marks)
        _require(value == row["nav"], "hourly_nav_not_reconciled")
        contribution = {}
        for symbol, ps in per_symbol.items():
            market_value = replay["units"][symbol] * marks[symbol] if replay["units"][symbol] else F(0)
            ps.update({"units": replay["units"][symbol], "cost_basis": replay["basis"][symbol],
                       "market_value": market_value,
                       "unrealized_pnl": market_value - replay["basis"][symbol]})
            contribution[symbol] = ps["realized_pnl"] + ps["unrealized_pnl"]
        _require(sum(contribution.values(), F(0)) == value - 1000, "symbol_pnl_not_reconciled")
        if close in (midpoint, end):
            snapshots[close] = {"contribution": contribution,
                               "costs": {b: replay[b] for b in BUCKETS}}
        exposed += int(any(replay["units"].values()))
        exposure_sum += (value - replay["cash"]) / value if value else F(0)
        curve.append({"close_ms": close, "nav": value, "cash": replay["cash"]})
    _require(next_trade == len(trades), "unprocessed_or_endpoint_trade")
    for key in ("cash", "units", "basis", "realized", *BUCKETS):
        _require(replay[key] == state[key], "final_ledger_not_reconciled")
    _require(arm.get("marked_nav") == curve[-1]["nav"]
             and arm.get("net_profit") == curve[-1]["nav"] - 1000
             and arm.get("realized_pnl_quote") == replay["realized"]
             and arm.get("unrealized_pnl") == sum(p["unrealized_pnl"] for p in per_symbol.values())
             and all(arm.get(field) == replay[bucket] for field, bucket in (
                 ("fees_quote", "fee"), ("slippage_quote", "slippage"),
                 ("rounding_loss_quote", "rounding"))), "summary_not_reconciled")
    for symbol, ps in per_symbol.items():
        ps["net_pnl_contribution"] = snapshots[end]["contribution"][symbol]
    return {"curve": curve, "snapshots": snapshots, "symbols": list(per_symbol.values()),
            "completed_cycles": cycles, "time_in_market_fraction": F(exposed, len(equity)),
            "mean_hour_end_gross_exposure_fraction": exposure_sum / len(equity),
            "coverage": _coverage(state, symbols),
            "exclusion_counts": dict(Counter(x["reason"] for e in state["events"]
                                               for x in e.get("excluded", []))),
            "expired_decisions": sum(e.get("decision_expired", False) for e in state["events"])}


def _period(reconciled, start, end, monthly_overhead):
    curve = [r for r in reconciled["curve"] if start <= r["close_ms"] <= end]
    _require(curve[0]["close_ms"] == start and curve[-1]["close_ms"] == end,
             "period_anchor_missing")
    navs = {r["close_ms"]: r["nav"] for r in curve}
    first, last = curve[0]["nav"], curve[-1]["nav"]
    before, after = reconciled["snapshots"][start], reconciled["snapshots"][end]
    costs = {b: after["costs"][b] - before["costs"][b] for b in BUCKETS}
    profit = last - first
    overhead = monthly_overhead * 12 * F(end - start, DAY * 365)
    daily = [(navs[t] - navs[t-DAY]) / navs[t-DAY]
             for t in range(start + DAY, end + 1, DAY) if navs[t-DAY]]
    closed = [c for c in reconciled["completed_cycles"] if start <= c["closed_at_ms"] < end]
    return {"start_ms": start, "end_ms": end, "initial_marked_nav": first,
            "final_marked_nav": last, "net_profit_usd": profit,
            "net_return_fraction": profit / first if first else None,
            "separate_overhead_usd": overhead, "net_after_overhead_usd": profit - overhead,
            "model_costs_usd": costs,
            "same_fill_path_profit_before_explicit_costs_usd": profit + sum(costs.values(), F(0)),
            "symbol_contribution_usd": {s: after["contribution"][s] - value
                                       for s, value in before["contribution"].items()},
            "worst_complete_day_return_fraction": min(daily) if daily else None,
            "complete_days_with_defined_return": len(daily), "closed_position_cycles": len(closed),
            "worst_closed_cycle_lifetime_pnl_usd": min((c["net_realized_pnl"] for c in closed), default=None),
            **_risk(curve)}


def build_descriptive_report(cost_cases, *, symbols, monthly_overhead, valuation_marks=None):
    """Report ordered chunk journals; no fetching, strategy execution or inference.

    cost_cases has exactly primary/stress, each a nonempty ordered list of
    existing comparison outputs. Historical valuation sidecars must be supplied
    when the original ledger needed them. Fractions remain exact in the result.
    Synthetic short horizons are supported; this never activates a 182-day study.
    """
    if (not isinstance(symbols, (list, tuple)) or len(symbols) != 25
            or any(not isinstance(s, str) or not s for s in symbols) or len(set(symbols)) != 25
            or not isinstance(cost_cases, dict) or set(cost_cases) != set(COSTS)
            or any(not isinstance(v, (list, tuple)) or not v
                   or any(not isinstance(c, dict) for c in v) for v in cost_cases.values())):
        raise ValueError("explicit_25_symbols_and_both_chunk_journals_required")
    symbols = tuple(sorted(symbols))
    overhead = ledger.number(monthly_overhead)
    if overhead != 20:
        raise ValueError("adopted_separate_overhead_required")
    marks = valuation_marks or {}
    cases = {}
    common = cost_cases["primary"][0].get("comparison_contract")
    for label, fee in COSTS.items():
        chunks = cost_cases[label]
        last = chunks[-1]
        diagnostics = {name: _diagnostic(last.get("arms", {}).get(name, {}), symbols)
            for name in comparison.ARM_NAMES}
        try:
            _require(isinstance(common, dict) and tuple(common["symbols"]) == symbols
                     and all(c.get("comparison_contract") == common and set(c["arms"]) == set(comparison.ARM_NAMES)
                             for c in chunks), "comparison_recipe_or_arms_mismatch")
            start, end = common["evaluation_start_ms"], common["evaluation_end_ms"]
            _require(type(start) is int and type(end) is int and start >= 0
                     and start % DAY == 0 and end > start + HOUR and (end-start) % (2*DAY) == 0
                     and common["first_execution_ms"] == start + HOUR, "invalid_common_report_clock")
            _require(common["btc_symbol"] != common["eth_symbol"]
                     and {common["btc_symbol"], common["eth_symbol"]} <= set(symbols)
                     and common["mix"] == ledger.weights({common["btc_symbol"]: F(1,4),
                         common["eth_symbol"]: F(1,4)}, symbols), "unexpected_declared_control_mix")
            _require(last.get("economic_result_usable") is True and last.get("period_complete") is True
                     and last.get("status") == "COMPLETE", "source_comparison_incomplete")
            reference = cost_cases["primary"][-1]["arms"]["cash"]["state"]["history"]
            _require(all(last["arms"][name]["state"]["history"] == reference
                         and last["arms"][name]["state"]["signal_bridge"]["binding"] ==
                             cost_cases["primary"][-1]["arms"][name]["state"]["signal_bridge"]["binding"]
                         for name in comparison.ARM_NAMES), "arm_or_cost_case_market_inputs_differ")
            arms = {}
            for name in comparison.ARM_NAMES:
                checked = _reconcile_arm(chunks, name, common, symbols, fee, marks)
                midpoint = (start + end) // 2
                periods = {key: _period(checked, a, b, overhead) for key, a, b in (
                    ("whole", start, end), ("first_half", start, midpoint), ("second_half", midpoint, end))}
                arms[name] = {"periods": periods, "per_symbol": checked["symbols"],
                    "coverage": checked["coverage"], "time_in_market_fraction": checked["time_in_market_fraction"],
                    "mean_hour_end_gross_exposure_fraction": checked["mean_hour_end_gross_exposure_fraction"],
                    "reference_turnover_multiple_of_initial_cash": sum(p["reference_turnover"] for p in checked["symbols"]) / 1000,
                    "incidental_reference_turnover_usd": sum(p["incidental_reference_turnover"] for p in checked["symbols"]),
                    "exclusion_counts": checked["exclusion_counts"], "expired_decisions": checked["expired_decisions"],
                    "terminal_liquidation_sensitivity": None}
            for arm in arms.values():
                for key, period in arm["periods"].items():
                    period["profit_gap_usd_vs_controls"] = {control:
                        period["net_profit_usd"] - arms[control]["periods"][key]["net_profit_usd"]
                        for control in CONTROLS}
            cases[label] = {"status": "COMPLETE", "reason": None, "arms": arms, "diagnostics": diagnostics}
        except (ledger.Incomplete, ValueError, KeyError, TypeError) as error:
            cases[label] = {"status": "INCOMPLETE", "reason": str(error), "arms": None, "diagnostics": diagnostics}
    complete = all(c["status"] == "COMPLETE" for c in cases.values())
    return {"schema": "ed002-descriptive-ledger-report-v1",
        "status": "COMPLETE" if complete else "INCOMPLETE",
        "qualification": "MODELLED_DESCRIPTIVE_NOT_EDGE_OR_TRADING_QUALIFICATION",
        "statistics_calculated": False, "experiment_pass": None, "cases": cases,
        "net_profit_usd_by_alternative": {label: {name: arm["periods"]["whole"]["net_profit_usd"]
            for name, arm in case["arms"].items()} for label, case in cases.items()} if complete else None,
        "trial_accounting": {"families": 3, "symbol_family_considerations": 75,
            "symbol_family_cost_considerations": 150, "alternative_trajectories": 14,
            "independent_sample_size": None},
        "limitations": ["no confidence or expected-income claim", "hour-close not intrabar risk",
            "same-fill cost addback is not a fee-free rerun", "cycle PnL is lifetime, not phase-only",
            "caller ledger provenance not independently authenticated", "no terminal liquidation simulated"]}
