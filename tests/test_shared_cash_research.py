"""Synthetic accounting contracts only: no market data, network or trading."""
from copy import deepcopy
from fractions import Fraction as F
import socket
import subprocess

import pytest

from services.backtest import shared_cash_research as model


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("synthetic adapter attempted external work")
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, forbidden)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, forbidden)


def frames(n=4, symbols=("A", "B"), price=100):
    return [{"ts_ms": i * 10, "open": dict.fromkeys(symbols, price),
             "close": dict.fromkeys(symbols, price)} for i in range(n)]


def permissions(symbols=("A", "B"), **updates):
    rule = {"known_at_ms": 0, "valid_from_ms": 0, "valid_until_ms": 100000,
            "venue": "SYNTHETIC", "quote": "USD", "eligible": True,
            "lot_step": ".01", "quote_step": ".01", "minimum_qty": 0,
            "minimum_notional_gross": 0, **updates}
    return {s: [deepcopy(rule)] for s in symbols}


def args(**updates):
    return {"symbols": ("A", "B"), "venue": "SYNTHETIC", "quote": "USD", "interval_ms": 10,
            "initial_cash": 1000, "fee_bps": 0, "slippage_bps": 0,
            "rules": permissions(), "target_contract_id": "synthetic-frozen-v1", **updates}


def decisions(*sequence):
    return lambda context: sequence[context["decision_index"]] if context["decision_index"] < len(sequence) else None


def test_joint_allocation_and_sells_before_buys_hand_calculated():
    result = model.simulate_shared_next_open(frames(), decisions({"A": ".5", "B": ".5"}, {"B": 1}), **args())
    state = result["state"]
    assert result["status"] == "COMPLETE" and result["marked_nav"] == 1000
    assert state["cash"] == 0 and state["units"] == {"A": 0, "B": 10}
    assert [t["side"] for t in state["trades"] if t["ts_ms"] == 20] == ["sell", "buy"]
    assert all(t["cash_after"] >= 0 and t["fill_model"] == "MODELLED_FULL_FILL" for t in state["trades"])
    assert [t["signal_bar_ts_ms"] for t in state["trades"]] == [0, 0, 10, 10]


def test_two_leg_fee_slippage_and_basis_are_not_double_charged():
    r = model.simulate_shared_next_open(frames(3), decisions({"A": 1}, {}),
                                      **args(initial_cash="102.01", fee_bps=100, slippage_bps=100))
    s = r["state"]
    assert [t["qty"] for t in s["trades"]] == [1, 1]
    assert s["cash"] == F("98.01") and r["net_profit"] == -4
    assert s["fee"] == 2 and s["slippage"] == 2 and s["rounding"] == 0
    assert s["basis"]["A"] == 0 and s["realized"] == -4 and r["unrealized_pnl"] == 0


def test_zero_fee_quote_rounding_can_lose_money():
    r = model.simulate_shared_next_open(frames(3, price=".333"), decisions({"A": 1}, {}),
        **args(initial_cash=1, rules=permissions(lot_step=1, quote_step=".1")))
    s = r["state"]
    assert s["cash"] == F(".9") and s["rounding"] == F(".1")
    assert s["fee"] == s["slippage"] == 0 and r["net_profit"] == -s["rounding"]
    assert s["trades"][0]["rounding"] == F(".001")
    assert s["trades"][1]["rounding"] == F(".099")


def test_basis_addition_partial_sale_and_dust_reconcile():
    data = frames(4, price=10)
    for row in data[2:]:
        row["open"]["A"] = row["close"]["A"] = 20
    r = model.simulate_shared_next_open(data, decisions({"A": ".5"}, {"A": 1}, {"A": ".5"}),
                                       **args(initial_cash=100))
    s = r["state"]
    assert s["units"]["A"] == F("3.75") and s["basis"]["A"] == 50
    assert s["cash"] == 75 and s["realized"] == 25 and r["unrealized_pnl"] == 25
    assert r["net_profit"] == s["realized"] + r["unrealized_pnl"]


def test_changed_lot_leaves_proportional_basis_dust():
    rules = permissions(lot_step=1)
    rules["A"][0]["valid_until_ms"] = 20
    rules["A"].append({**rules["B"][0], "known_at_ms": 10, "valid_from_ms": 20, "lot_step": 3})
    r = model.simulate_shared_next_open(frames(3, price=10), decisions({"A": 1}, {}),
                                       **args(initial_cash=105, rules=rules), terminal_liquidation=True)
    assert r["state"]["units"]["A"] == 1 and r["state"]["basis"]["A"] == 10
    assert r["state"]["cash"] == 95 and r["marked_nav"] == 105
    assert r["terminal_liquidation"]["units"]["A"] == 1


def test_float_joint_helper_is_refined_before_lot_floor():
    data = frames(3)
    rules = permissions()
    rules["A"][0]["valid_until_ms"] = 20
    rules["A"].append({**rules["B"][0], "known_at_ms": 10, "valid_from_ms": 20, "eligible": False})
    r = model.simulate_shared_next_open(data, decisions({"A": ".4"}, {"B": ".2"}), **args(rules=rules))
    assert r["state"]["units"] == {"A": 4, "B": 2}
    assert r["state"]["cash"] == 400


def test_frozen_holding_caps_executable_capital_without_redistribution():
    rules = permissions()
    rules["A"][0]["valid_until_ms"] = 20
    rules["A"].append({**rules["B"][0], "known_at_ms": 10, "valid_from_ms": 20, "eligible": False})
    r = model.simulate_shared_next_open(frames(3), decisions({"A": ".4"}, {"B": ".8"}), **args(rules=rules))
    assert r["state"]["units"] == {"A": 4, "B": 6}
    assert r["state"]["cash"] == 0 and r["marked_nav"] == 1000
    assert any(e.get("excluded") == [{"symbol": "A", "reason": "ineligible"}] for e in r["state"]["events"])


def test_cash_rescale_is_proportional_not_symbol_priority():
    kwargs = args(initial_cash=1, rules=permissions(lot_step=1, quote_step=".3"))
    r = model.simulate_shared_next_open(frames(2, price=".06"), decisions({"A": ".5", "B": ".5"}), **kwargs)
    assert r["state"]["units"] == {"A": 5, "B": 5}
    assert r["state"]["cash"] == F(".4")
    for trade in r["state"]["trades"]:
        assert trade["cash_after"] >= 0


def test_tolerance_cannot_fund_one_quote_quantum():
    r = model.simulate_shared_next_open(frames(2, price=".001"), decisions({"A": 1}),
        **args(initial_cash=".009", rules=permissions(lot_step=1, quote_step=".01")))
    assert r["state"]["trades"] == [] and r["state"]["cash"] == F(".009")


def test_permutation_invariance_and_no_input_mutation():
    data, rules = frames(), permissions()
    saved = deepcopy((data, rules))
    a = model.simulate_shared_next_open(data, decisions({"B": ".5", "A": ".5"}, {"B": 1}), **args(rules=rules))
    b = model.simulate_shared_next_open(data, decisions({"A": ".5", "B": ".5"}, {"B": 1}),
        **args(symbols=("B", "A"), rules=dict(reversed(list(rules.items())))))
    assert a == b and (data, rules) == saved


def test_split_carries_cash_basis_pending_and_opening_gap_exactly():
    data = frames(4, price=10)
    for row in data[2:]:
        row["open"] = row["close"] = {"A": 20, "B": 20}
    callback = decisions({"A": 1}, {})
    full = model.simulate_shared_next_open(data, callback, **args())
    left = model.simulate_shared_next_open(data[:2], callback, **args())
    assert left["state"]["pending"]["execution_ms"] == 20
    right = model.simulate_shared_next_open(data[2:], callback, state=left["state"], **args())
    assert right["state"] == full["state"]
    assert right["phase_start_nav"] == left["marked_nav"] == 1000
    assert left["phase_profit"] == 0 and right["phase_profit"] == 1000
    assert len(right["state"]["trades"]) == 2
    assert left["phase_profit"] + right["phase_profit"] == full["net_profit"]


def test_missing_open_expires_only_that_order_without_later_retry():
    data = frames(3)
    del data[1]["open"]["A"]
    r = model.simulate_shared_next_open(data, decisions({"A": ".5", "B": ".5"}), **args())
    assert r["status"] == "COMPLETE" and r["state"]["units"] == {"A": 0, "B": 5}
    assert r["state"]["cash"] == 500
    assert r["state"]["events"][0]["excluded"] == [{"symbol": "A", "reason": "missing_execution_open"}]


@pytest.mark.parametrize("future_mark", [False, True])
def test_no_stale_or_future_mark_can_value_a_held_asset(future_mark):
    data = frames(3)
    del data[2]["open"]["A"]
    mark = {"ts_ms": 20 if future_mark else 10, "known_at_ms": 21 if future_mark else 10, "price": 100}
    r = model.simulate_shared_next_open(data, decisions({"A": 1}), **args(), valuation_marks={"A": [mark]})
    assert r["status"] == "INCOMPLETE" and r["marked_nav"] is None and r["net_profit"] is None
    assert r["state"]["units"]["A"] == 10 and r["state"]["cash"] == 0


def test_fresh_valuation_is_not_an_executable_price():
    data = frames(3)
    del data[2]["open"]["A"]
    marks = {"A": [{"ts_ms": 20, "known_at_ms": 20, "price": 100}]}
    r = model.simulate_shared_next_open(data, decisions({"A": 1}, {"B": 1}), **args(), valuation_marks=marks)
    assert r["status"] == "COMPLETE" and r["state"]["units"] == {"A": 10, "B": 0}
    assert len(r["state"]["trades"]) == 1


def test_missing_close_retains_legitimate_open_fill_but_unknown_performance():
    data = frames(2)
    del data[1]["close"]["A"]
    r = model.simulate_shared_next_open(data, decisions({"A": 1}), **args())
    assert r["status"] == "INCOMPLETE" and r["state"]["units"]["A"] == 10
    assert len(r["state"]["trades"]) == 1 and r["phase_profit"] is None
    with pytest.raises(ValueError, match="complete_state"):
        model.simulate_shared_next_open(frames(1)[0:1], decisions(None), **args(), state=r["state"])


@pytest.mark.parametrize("defect", ["missing", "future", "expired", "precision", "quote", "ambiguous"])
def test_missing_or_unusable_dated_evidence_is_incomplete(defect):
    rules = permissions()
    if defect == "missing":
        del rules["A"]
    elif defect == "future":
        rules["A"][0]["known_at_ms"] = 11
    elif defect == "expired":
        rules["A"][0]["valid_until_ms"] = 10
    elif defect == "precision":
        del rules["A"][0]["lot_step"]
    elif defect == "quote":
        rules["A"][0]["quote"] = "EUR"
    else:
        rules["A"].append(deepcopy(rules["A"][0]))
    r = model.simulate_shared_next_open(frames(2), decisions({"A": 1}), **args(rules=rules))
    assert r["status"] == "INCOMPLETE" and r["state"]["trades"] == []
    assert r["state"]["cash"] == 1000


def test_known_ineligible_order_is_excluded_not_a_fictitious_loss():
    r = model.simulate_shared_next_open(frames(2), decisions({"A": 1}), **args(rules=permissions(eligible=False)))
    assert r["status"] == "COMPLETE" and r["state"]["cash"] == 1000 and r["state"]["trades"] == []


def test_atomic_settlement_failure_does_not_commit_half_a_rebalance(monkeypatch):
    original = model.settle
    def broken(state, fill, *args, **kwargs):
        original(state, fill, *args, **kwargs)
        if fill["symbol"] == "B":
            raise model.Incomplete("injected_reconciliation_failure")
    monkeypatch.setattr(model, "settle", broken)
    r = model.simulate_shared_next_open(frames(3), decisions({"A": 1}, {"B": 1}), **args())
    assert r["status"] == "INCOMPLETE"
    assert r["state"]["units"] == {"A": 10, "B": 0} and r["state"]["cash"] == 0
    assert len(r["state"]["trades"]) == 1


def test_terminal_liquidation_is_separate_and_costs_do_not_pollute_carry():
    data = frames(3)
    callback = decisions({"A": 1})
    primary = model.simulate_shared_next_open(data, callback, **args(fee_bps=50))
    secondary = model.simulate_shared_next_open(data, callback, **args(fee_bps=50), terminal_liquidation=True)
    assert secondary["state"] == primary["state"] and secondary["marked_nav"] == primary["marked_nav"]
    terminal = secondary["terminal_liquidation"]
    assert terminal["marked_nav"] < primary["marked_nav"]
    assert all(t["terminal"] for t in terminal["trades"])
    assert "NOT_NEXT_OPEN" in terminal["qualification"]


def test_future_prices_do_not_change_prior_decisions_or_nav():
    baseline, changed = frames(5), frames(5)
    for row in changed[3:]:
        row["open"] = {"A": 7, "B": 50}
        row["close"] = {"A": 8, "B": 70}
    seen = [[], []]
    def callback(index):
        def target(context):
            seen[index].append(deepcopy(context))
            return {"A": ".5", "B": ".5"}
        return target
    a = model.simulate_shared_next_open(baseline, callback(0), **args())
    b = model.simulate_shared_next_open(changed, callback(1), **args())
    assert seen[0][:3] == seen[1][:3]
    assert a["equity"][:2] == b["equity"][:2]


def test_terminal_never_promotes_valuation_only_mark_to_execution():
    data = frames(3, price=10)
    del data[-1]["close"]["A"]
    marks = {"A": [{"ts_ms": 30, "known_at_ms": 30, "price": 12}]}
    r = model.simulate_shared_next_open(data, decisions({"A": 1}),
        **args(), valuation_marks=marks, terminal_liquidation=True)
    assert r["status"] == "COMPLETE" and r["marked_nav"] == 1200
    assert r["state"]["units"]["A"] == 100
    terminal = r["terminal_liquidation"]
    assert terminal["trades"] == [] and terminal["cash"] == 0
    assert terminal["units"]["A"] == 100 and terminal["marked_nav"] == 1200
    assert terminal["profit_basis"] == "marked_residual_holdings"
    assert terminal["excluded"] == [{"symbol": "A", "reason": "missing_execution_open"}]


@pytest.mark.parametrize("change", ["identity", "mix"])
def test_changed_comparison_declaration_is_refused_before_any_arm(change, monkeypatch):
    comparison = dict(btc_symbol="A", eth_symbol="B", mix_weights={"A": ".25", "B": ".25"})
    left = model.simulate_shared_comparison(frames(2), decisions(None), **comparison, **args())
    states = {k: v["state"] for k, v in left.items()}
    if change == "identity":
        comparison.update(btc_symbol="B", eth_symbol="A")
    else:
        comparison["mix_weights"] = {"A": ".75"}

    def forbidden(*a, **kw):
        pytest.fail("comparison mismatch simulated an arm")

    monkeypatch.setattr(model, "simulate_shared_next_open", forbidden)
    with pytest.raises(ValueError, match="comparison_contract_changed"):
        model.simulate_shared_comparison(frames(3)[2:], decisions(None),
            states=states, **comparison, **args())


def test_callback_mutation_cannot_change_inputs_or_wallet():
    data = frames(3)
    original = deepcopy(data)
    def target(context):
        context["history"][-1]["close"]["A"] = 999
        context["units"]["A"] = 999
        return {"A": 1} if context["decision_index"] == 0 else None
    r = model.simulate_shared_next_open(data, target, **args())
    assert data == original and r["state"]["units"]["A"] == 10
    assert r["state"]["history"][-1]["close"]["A"] == 100


def test_twenty_five_synthetic_symbols_share_one_capital_pool():
    symbols = tuple("SYN-" + str(i) for i in range(25))
    r = model.simulate_shared_next_open(frames(2, symbols, ".1"), decisions(dict.fromkeys(symbols, F(1, 25))),
        **args(symbols=symbols, rules=permissions(symbols, lot_step=".0001", quote_step=".0001")))
    assert r["marked_nav"] == 1000 and r["state"]["cash"] == 0
    assert sum(r["state"]["units"].values()) == 10000 and len(r["state"]["trades"]) == 25


@pytest.mark.parametrize("field", ["cash", "basis"])
def test_resume_refuses_unrecorded_wallet_changes(field):
    left = model.simulate_shared_next_open(frames(2), decisions({"A": 1}), **args())
    s = deepcopy(left["state"])
    if field == "cash":
        s["cash"] += 1
        s["last_nav"] += 1
    else:
        s["basis"]["A"] += 1
    with pytest.raises(ValueError, match="ledger_mismatch"):
        model.simulate_shared_next_open(frames(3)[2:], decisions(None), **args(), state=s)


@pytest.mark.parametrize("field", ["last_nav", "pending", "last_ts", "profile"])
def test_resume_refuses_changed_boundary_or_contract(field):
    left = model.simulate_shared_next_open(frames(2), decisions({"A": 1}, {}), **args())
    s = deepcopy(left["state"])
    if field == "last_nav":
        s[field] += 1
    elif field == "pending":
        s[field]["execution_ms"] += 10
    elif field == "last_ts":
        s[field] += 10
    else:
        s[field]["fee"] += F(1, 100)
    with pytest.raises(ValueError):
        model.simulate_shared_next_open(frames(3)[2:], decisions(None), **args(), state=s)


def test_caller_history_is_not_silently_truncated():
    lengths = []

    def target(context):
        lengths.append(len(context["history"]))
        return None

    result = model.simulate_shared_next_open(frames(302), target, **args())
    assert result["status"] == "COMPLETE" and lengths == list(range(1, 303))


def test_minimums_are_explicit_execution_gross_not_fee_inclusive():
    r = model.simulate_shared_next_open(frames(2, price=10), decisions({"A": 1}),
        **args(initial_cash=10, fee_bps=100, rules=permissions(minimum_notional_gross=10)))
    assert r["state"]["trades"] == []
    assert r["state"]["events"][0]["excluded"][0]["reason"] == "below_minimum_or_lot_dust"


@pytest.mark.parametrize("field,value", [("initial_cash", 0), ("fee_bps", 10000),
    ("slippage_bps", -1), ("initial_cash", True), ("fee_bps", "garbage")])
def test_invalid_financial_parameters_are_rejected(field, value):
    with pytest.raises(ValueError):
        model.simulate_shared_next_open(frames(2), decisions({"A": 1}), **args(**{field: value}))


def test_controls_share_costs_dates_and_fixed_units_across_splits():
    data = frames(4)
    for row in data[2:]:
        row["open"]["A"] = row["close"]["A"] = 200
    comparison = dict(btc_symbol="A", eth_symbol="B", mix_weights={"A": ".25", "B": ".25"})
    full = model.simulate_shared_comparison(data, decisions({"B": 1}), **comparison, **args(fee_bps=50))
    left = model.simulate_shared_comparison(data[:2], decisions({"B": 1}), **comparison, **args(fee_bps=50))
    right = model.simulate_shared_comparison(data[2:], decisions({"B": 1}),
        states={k:v["state"] for k,v in left.items()}, **comparison, **args(fee_bps=50))
    for name, result in full.items():
        assert result["state"] == right[name]["state"]
        assert result["phase_start_nav"] == 1000 and result["state"]["profile"]["fee"] == F(50, 10000)
    assert full["cash"]["marked_nav"] == 1000 and full["cash"]["state"]["trades"] == []
    assert len(full["hold_btc"]["state"]["trades"]) == 1
    assert len(full["declared_btc_eth_cash_mix"]["state"]["trades"]) == 2


@pytest.mark.parametrize("target", [{"A": -1}, {"A": 2}, {"UNKNOWN": 1}, {"A": float("nan")}, {"A": True}])
def test_invalid_sizing_is_not_invented(target):
    with pytest.raises(ValueError):
        model.simulate_shared_next_open(frames(2), decisions(target), **args())
