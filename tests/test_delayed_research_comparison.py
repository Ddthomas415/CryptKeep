"""Synthetic comparison completeness, not strategy or market evidence."""
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import socket
import subprocess

import pytest

from services.backtest import delayed_research_comparison as comparison
from services.backtest import frozen_signal_bridge as frozen


H = frozen.HOUR
SNAPSHOT = (Path(__file__).resolve().parents[1] /
            "research/multisymbol_baseline_v1/strategies.snapshot.json").read_bytes()


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("synthetic comparison attempted external work")
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, forbidden)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, forbidden)
    monkeypatch.setattr(frozen, "compute_signal", lambda **kwargs: {"ok": True, "action": "hold"})


def setup(symbols=("A", "B")):
    panel = {s: [{"row": [i*H, 100., 102., 98., 100., 1000.], "known_at_ms": (i+1)*H+1}
                 for i in range(307)] for s in symbols}
    rules = {s: [{"known_at_ms": 0, "valid_from_ms": 0, "valid_until_ms": 9999999999999,
        "venue": "SYNTHETIC", "quote": "USD", "eligible": True, "lot_step": ".000001",
        "quote_step": ".000001", "minimum_qty": 0, "minimum_notional_gross": 0}] for s in symbols}
    f = [{"ts_ms": i*H, "open": dict.fromkeys(symbols, 100.), "close": dict.fromkeys(symbols, 100.)}
         for i in range(300, 307)]
    profile = dict(symbols=symbols, observations=panel, rules=rules, venue="SYNTHETIC", quote="USD",
        snapshot_bytes=SNAPSHOT, btc_symbol=symbols[0], eth_symbol=symbols[1],
        mix_weights={symbols[0]: F(1,4), symbols[1]: F(1,4)}, evaluation_start_ms=300*H,
        evaluation_end_ms=307*H, initial_cash=1000, fee_bps=0, slippage_bps=0,
        target_contract_id="synthetic-seven-arm")
    return f, profile


def test_seven_accounts_common_clock_initial_cash_hour_and_no_sum():
    f, profile = setup()
    result = comparison.simulate_delayed_comparison(f, **profile)
    assert result["status"] == "COMPLETE" and result["economic_result_usable"]
    assert set(result["arms"]) == set(comparison.ARM_NAMES) and len(result["arms"]) == 7
    assert result["net_profit_by_arm"] == dict.fromkeys(comparison.ARM_NAMES, 0)
    assert "total_profit" not in result
    for arm in result["arms"].values():
        assert len(arm["equity"]) == 7
        assert arm["equity"][0]["close_ms"] == 301*H
        assert arm["equity"][0]["cash"] == 1000 and not any(arm["equity"][0]["units"].values())
        assert arm["equity"][-1]["close_ms"] == 307*H
    for name in ("hold_btc", "declared_btc_eth_cash_mix"):
        assert result["arms"][name]["state"]["trades"][0]["ts_ms"] == 301*H
        assert result["arms"][name]["benchmark_entry"]["status"] == "ACCEPTED"


@pytest.mark.parametrize("fault", ["missing_open", "ineligible", "minimum", "lot_dust"])
def test_failed_benchmark_entry_is_incomplete_not_cash_hold(fault):
    f, profile = setup()
    if fault == "missing_open":
        del f[1]["open"]["A"]
    elif fault == "ineligible":
        profile["rules"]["A"][0]["eligible"] = False
    elif fault == "minimum":
        profile["rules"]["A"][0]["minimum_notional_gross"] = 1001
    else:
        profile["rules"]["A"][0]["lot_step"] = 100
    result = comparison.simulate_delayed_comparison(f, **profile)
    failed = result["arms"]["hold_btc"]
    assert result["status"] == "INCOMPLETE" and result["period_complete"]
    assert failed["ledger_status"] == "COMPLETE" and failed["status"] == "INCOMPLETE"
    assert failed["marked_nav"] is None and failed["net_profit"] is None
    assert failed["benchmark_entry"]["missing_symbols"] == ["A"]
    assert failed["state"]["cash"] == 1000  # Preserved diagnostic ledger, not benchmark success.
    assert not result["economic_result_usable"] and all(v is None for v in result["net_profit_by_arm"].values())


def test_each_mix_component_must_enter_not_just_one_positive_fill():
    f, profile = setup()
    profile["rules"]["B"][0]["minimum_qty"] = 100
    result = comparison.simulate_delayed_comparison(f, **profile)
    assert result["arms"]["hold_btc"]["status"] == "COMPLETE"
    mix = result["arms"]["declared_btc_eth_cash_mix"]
    assert mix["benchmark_entry"]["entered_symbols"] == ["A"]
    assert mix["benchmark_entry"]["missing_symbols"] == ["B"] and mix["status"] == "INCOMPLETE"


def test_fixed_units_control_has_no_rebalance_when_prices_change():
    f, profile = setup()
    for index in range(302, 307):
        profile["observations"]["A"][index]["row"][1:5] = [200., 202., 198., 200.]
        f[index-300]["open"]["A"] = f[index-300]["close"]["A"] = 200.
    result = comparison.simulate_delayed_comparison(f, **profile)
    mix = result["arms"]["declared_btc_eth_cash_mix"]
    assert result["status"] == "COMPLETE" and len(mix["state"]["trades"]) == 2
    assert mix["state"]["units"] == {"A": F(5,2), "B": F(5,2)}
    assert mix["marked_nav"] == 1250


def test_fee_cases_are_explicit_and_not_rebased_or_combined():
    f, profile = setup()
    profile.update(fee_bps=50, slippage_bps=25)
    result = comparison.simulate_delayed_comparison(f, **profile)
    hold = result["arms"]["hold_btc"]
    assert result["status"] == "COMPLETE" and hold["phase_start_nav"] == 1000
    assert hold["net_profit"] < 0 and hold["fees_quote"] > 0 and hold["slippage_quote"] > 0
    assert result["arms"]["cash"]["net_profit"] == 0
    assert hold["net_profit"] == hold["marked_nav"] - 1000


def test_full_split_all_seven_wallets_and_equity_match():
    f, profile = setup()
    full = comparison.simulate_delayed_comparison(f, **profile)
    left = comparison.simulate_delayed_comparison(f[:3], **profile)
    assert left["status"] == "INCOMPLETE" and not left["period_complete"]
    assert all(v is None for v in left["net_profit_by_arm"].values())
    right = comparison.simulate_delayed_comparison(f[3:], states=left["states"], **profile)
    assert right["status"] == "COMPLETE" and right["states"] == full["states"]
    for name in comparison.ARM_NAMES:
        assert left["arms"][name]["equity"] + right["arms"][name]["equity"] == full["arms"][name]["equity"]
        assert right["arms"][name]["bridge_trades"] == full["arms"][name]["bridge_trades"]


@pytest.mark.parametrize("fault", ["missing_arm", "changed_mix", "changed_end", "changed_fee", "offset_clock"])
def test_carry_refuses_changed_contract_or_missing_state(fault):
    f, profile = setup()
    left = comparison.simulate_delayed_comparison(f[:3], **profile)
    states = deepcopy(left["states"])
    if fault == "missing_arm":
        states.pop("cash")
    elif fault == "changed_mix":
        profile["mix_weights"] = {"A": F(1,3), "B": F(1,3)}
    elif fault == "changed_end":
        profile["evaluation_end_ms"] += H
    elif fault == "changed_fee":
        profile["fee_bps"] = 50
    else:
        states["cash"]["last_ts"] -= H
    with pytest.raises(ValueError):
        comparison.simulate_delayed_comparison(f[3:], states=states, **profile)


def test_failed_entry_cannot_be_restarted_as_successful_carry():
    f, profile = setup()
    del f[1]["open"]["A"]
    left = comparison.simulate_delayed_comparison(f[:3], **profile)
    with pytest.raises(ValueError, match="carry_contract_or_entry"):
        comparison.simulate_delayed_comparison(f[3:], states=left["states"], **profile)


@pytest.mark.parametrize("fault", ["wrong_start", "beyond_end", "one_frame", "one_mix_asset"])
def test_invalid_clock_or_control_contract_refuses_before_execution(fault):
    f, profile = setup()
    if fault == "wrong_start":
        profile["evaluation_start_ms"] -= H
    elif fault == "beyond_end":
        profile["evaluation_end_ms"] -= H
    elif fault == "one_frame":
        f = f[:1]
    else:
        profile["mix_weights"] = {"A": F(1,2)}
    with pytest.raises(ValueError):
        comparison.simulate_delayed_comparison(f, **profile)


def test_missing_signal_input_is_not_a_negative_economic_verdict():
    f, profile = setup()
    del profile["observations"]["A"][100]
    result = comparison.simulate_delayed_comparison(f, **profile)
    assert result["status"] == "INCOMPLETE"
    assert result["arms"]["ema_cross_default"]["state"] is None
    assert all(v is None for v in result["net_profit_by_arm"].values())


def test_all25_declared_symbols_share_each_family_wallet(monkeypatch):
    symbols = tuple("SYN-"+str(i) for i in range(25))
    f, profile = setup(symbols)
    def buy(*, cfg, symbol, ohlcv):
        return {"ok": True, "action": "buy" if ohlcv[-1][0] == 299*H else "hold"}
    monkeypatch.setattr(frozen, "compute_signal", buy)
    result = comparison.simulate_delayed_comparison(f, **profile)
    assert result["status"] == "COMPLETE"
    for name in frozen.FAMILIES:
        state = result["arms"][name]["state"]
        assert len(state["units"]) == 25 and sum(state["units"].values())*100 + state["cash"] == 1000
        assert len(state["trades"]) == 25
    assert not result["statistics_calculated"]


def test_missing_held_mark_is_incomplete_not_a_fabricated_exit():
    f, profile = setup()
    del f[2]["close"]["A"]
    result = comparison.simulate_delayed_comparison(f, **profile)
    hold = result["arms"]["hold_btc"]
    assert hold["status"] == "INCOMPLETE" and hold["reason"] == "unknown_held_valuation"
    assert hold["net_profit"] is None and not result["economic_result_usable"]
    assert hold["state"]["units"]["A"] > 0


def test_bad_control_outcome_price_invalidates_comparison():
    f, profile = setup()
    f[2]["close"]["A"] = 10000.
    result = comparison.simulate_delayed_comparison(f, **profile)
    assert result["arms"]["hold_btc"]["status"] == "INCOMPLETE"
    assert not result["economic_result_usable"]
    assert all(v is None for v in result["net_profit_by_arm"].values())


def test_copied_cash_entry_proof_cannot_hide_failed_benchmarks():
    f, profile = setup()
    profile["rules"]["A"][0]["eligible"] = False
    left = comparison.simulate_delayed_comparison(f[:3], **profile)
    states = deepcopy(left["states"])
    for name in ("hold_btc", "declared_btc_eth_cash_mix"):
        states[name]["comparison_entry"] = deepcopy(states["cash"]["comparison_entry"])
    with pytest.raises(ValueError, match="comparison_carry_contract_or_entry_invalid"):
        comparison.simulate_delayed_comparison(f[3:], states=states, **profile)


@pytest.mark.parametrize("field,value", [
    ("expected_symbols", []), ("entered_symbols", []),
    ("execution_ms", 302*H), ("missing_symbols", ["A"]),
])
def test_carry_reconciles_full_entry_record_before_any_arm_runs(monkeypatch, field, value):
    f, profile = setup()
    left = comparison.simulate_delayed_comparison(f[:3], **profile)
    states = deepcopy(left["states"])
    states["hold_btc"]["comparison_entry"][field] = value
    def forbidden(*args, **kwargs):
        raise AssertionError("simulation ran before carried entry evidence was checked")
    monkeypatch.setattr(comparison.delayed, "simulate_delayed_bridge", forbidden)
    with pytest.raises(ValueError, match="comparison_carry_contract_or_entry_invalid"):
        comparison.simulate_delayed_comparison(f[3:], states=states, **profile)
