"""Synthetic post-ledger economics; no market study or statistical qualification."""
from copy import deepcopy
from fractions import Fraction as F
from pathlib import Path
import socket
import subprocess

import pytest

from services.backtest import delayed_research_comparison as comparison
from services.backtest import descriptive_report as report
from services.backtest import frozen_signal_bridge as frozen


H, D = report.HOUR, report.DAY
SYMBOLS = tuple("TEST%02d" % i for i in range(25))
A, B = 312 * H, 360 * H


def forbid(*args, **kwargs):
    raise AssertionError("descriptive report attempted external work")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, forbid)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, forbid)


@pytest.fixture(scope="module")
def journals():
    def price(i, s):
        if s != SYMBOLS[0] or i < 320:
            return 100
        return 120 if i < 328 else 80 if i < 342 else 110

    def signal(*, cfg, symbol, ohlcv):
        close = ohlcv[-1][0] + H
        family = cfg["strategy"]["name"]
        schedule = ({A: "buy", A+12*H: "sell", A+24*H: "buy"}
                    if family == "breakout_donchian" else
                    {A+12*H: "buy", A+24*H: "sell"} if family == "ema_cross" else {})
        action = schedule.get(close, "hold") if symbol == SYMBOLS[0] else "hold"
        if family == "breakout_donchian" and symbol == SYMBOLS[1] and close == A+6*H:
            action = "buy"
        return {"ok": True, "action": action}

    observations = {s: [{"row": [i*H, price(i, s), price(i, s)+2, price(i, s)-2, price(i, s), 1000],
                         "known_at_ms": (i+1)*H+1} for i in range(360)] for s in SYMBOLS}
    frames = [{"ts_ms": i*H, "open": {s: price(i, s) for s in SYMBOLS},
               "close": {s: price(i, s) for s in SYMBOLS}} for i in range(312, 360)]
    rules = {s: [{"known_at_ms": 0, "valid_from_ms": 0, "valid_until_ms": 1000*H,
        "venue": "coinbase", "quote": "USD", "eligible": True, "lot_step": ".000001",
        "quote_step": ".01", "minimum_qty": 0, "minimum_notional_gross": 0}] for s in SYMBOLS}
    snapshot = (Path(__file__).resolve().parents[1] /
                "research/multisymbol_baseline_v1/strategies.snapshot.json").read_bytes()
    profile = dict(symbols=SYMBOLS, observations=observations, rules=rules, venue="coinbase", quote="USD",
        snapshot_bytes=snapshot, btc_symbol=SYMBOLS[0], eth_symbol=SYMBOLS[1],
        mix_weights={SYMBOLS[0]: F(1,4), SYMBOLS[1]: F(1,4)}, evaluation_start_ms=A,
        evaluation_end_ms=B, initial_cash=1000, slippage_bps=25, target_contract_id="synthetic-report")
    whole, split = {}, {}
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(frozen, "compute_signal", signal)
        for name in ("socket", "create_connection", "getaddrinfo"):
            patch.setattr(socket, name, forbid)
        for name in ("Popen", "run", "call", "check_output", "check_call"):
            patch.setattr(subprocess, name, forbid)
        for label, fee in (("primary", 50), ("stress", 90)):
            whole[label] = [comparison.simulate_delayed_comparison(frames, fee_bps=fee, **profile)]
            first = comparison.simulate_delayed_comparison(frames[:24], fee_bps=fee, **profile)
            second = comparison.simulate_delayed_comparison(frames[24:], states=first["states"], fee_bps=fee, **profile)
            split[label] = [first, second]
    assert all(c[0]["economic_result_usable"] for c in whole.values())
    return whole, split


def build(journals):
    return report.build_descriptive_report(journals, symbols=SYMBOLS, monthly_overhead=20)


def test_completed_reports_keep_gains_losses_cash_and_all_14_alternatives(journals):
    result = build(journals[0])
    assert result["status"] == "COMPLETE", result
    assert result["statistics_calculated"] is False and result["experiment_pass"] is None
    assert result["trial_accounting"] == {"families": 3, "symbol_family_considerations": 75,
        "symbol_family_cost_considerations": 150, "alternative_trajectories": 14,
        "independent_sample_size": None}
    assert "total_profit" not in result
    for case in result["cases"].values():
        arms = case["arms"]
        assert set(arms) == set(comparison.ARM_NAMES)
        assert arms["breakout_default"]["periods"]["whole"]["net_profit_usd"] > 0
        assert arms["ema_cross_default"]["periods"]["whole"]["net_profit_usd"] < 0
        assert arms["cash"]["periods"]["whole"]["net_profit_usd"] == 0
        assert arms["cash"]["periods"]["whole"]["net_after_overhead_usd"] < 0


def test_dollars_costs_overhead_and_symbol_contributions_reconcile(journals):
    original = deepcopy(journals[0])
    result = build(journals[0])
    assert journals[0] == original
    for label, case in result["cases"].items():
        for name, arm in case["arms"].items():
            source = journals[0][label][0]["arms"][name]
            whole = arm["periods"]["whole"]
            assert whole["net_profit_usd"] == source["net_profit"]
            assert whole["final_marked_nav"] == source["marked_nav"]
            assert whole["separate_overhead_usd"] == F(20*12*2, 365)
            assert whole["net_after_overhead_usd"] == source["net_profit"] - F(480, 365)
            assert len(arm["per_symbol"]) == len(arm["coverage"]) == 25
            assert sum(p["net_pnl_contribution"] for p in arm["per_symbol"]) == source["net_profit"]
            for bucket, field in (("fee", "fees_quote"), ("slippage", "slippage_quote"), ("rounding", "rounding_loss_quote")):
                assert sum(p[bucket] for p in arm["per_symbol"]) == source[field]
            assert sum(p["realized_pnl"] for p in arm["per_symbol"]) == source["realized_pnl_quote"]
            assert sum(p["unrealized_pnl"] for p in arm["per_symbol"]) == source["unrealized_pnl"]
            for control in report.CONTROLS:
                assert whole["profit_gap_usd_vs_controls"][control] == source["net_profit"] - journals[0][label][0]["arms"][control]["net_profit"]


def test_chunk_carry_and_halves_do_not_reset_or_double_charge(journals):
    whole, split = build(journals[0]), build(journals[1])
    assert split == whole
    for case in whole["cases"].values():
        for arm in case["arms"].values():
            total, first, second = [arm["periods"][p] for p in ("whole", "first_half", "second_half")]
            assert first["final_marked_nav"] == second["initial_marked_nav"]
            assert first["net_profit_usd"] + second["net_profit_usd"] == total["net_profit_usd"]
            assert first["separate_overhead_usd"] + second["separate_overhead_usd"] == total["separate_overhead_usd"]
            for bucket in report.BUCKETS:
                assert first["model_costs_usd"][bucket] + second["model_costs_usd"][bucket] == total["model_costs_usd"][bucket]
            for phase in (first, second):
                assert sum(phase["symbol_contribution_usd"].values()) == phase["net_profit_usd"]


def test_drawdown_and_unrecovered_duration_are_hourly_not_annualized():
    curve = [{"close_ms": i*H, "nav": F(v)} for i, v in enumerate((1000, 1200, 900, 1100))]
    assert report._risk(curve) == {"maximum_drawdown_fraction": F(1,4), "maximum_underwater_hours": 2}
    assert report._risk([{"close_ms": 0, "nav": F(1000)}, {"close_ms": H, "nav": F(0)}])["maximum_drawdown_fraction"] == 1
    recovered = [{"close_ms": i*H, "nav": F(v)} for i, v in enumerate((1000, 900, 1000))]
    assert report._risk(recovered)["maximum_underwater_hours"] == 2


def test_cycles_open_risk_incidental_turnover_and_exposure_are_disclosed(journals):
    result = build(journals[0])
    arm = result["cases"]["primary"]["arms"]["breakout_default"]
    assert arm["periods"]["whole"]["closed_position_cycles"] == 1
    assert arm["incidental_reference_turnover_usd"] > 0
    assert 0 < arm["time_in_market_fraction"] < 1
    assert 0 < arm["mean_hour_end_gross_exposure_fraction"] < 1
    assert any(p["units"] and p["unrealized_pnl"] for p in arm["per_symbol"])
    assert arm["terminal_liquidation_sensitivity"] is None


@pytest.mark.parametrize("fault", ["missing_hour", "duplicate_hour", "false_nav", "false_cash", "false_units",
    "missing_benchmark_entry", "false_fee_summary", "false_cost_trade", "missing_trace", "missing_mark",
    "incomplete_arm", "false_profile", "missing_arm", "changed_recipe", "changed_mix",
    "different_arm_prices", "different_case_binding"])
def test_corrupt_or_incomplete_case_never_becomes_a_headline_profit(journals, fault):
    broken = deepcopy(journals[0])
    case = broken["primary"][0]
    arm = case["arms"]["hold_btc"]
    if fault == "missing_hour":
        arm["equity"].pop(2)
    elif fault == "duplicate_hour":
        arm["equity"].insert(2, deepcopy(arm["equity"][1]))
    elif fault == "false_nav":
        arm["equity"][3]["nav"] += 1
    elif fault == "false_cash":
        arm["equity"][3]["cash"] += 1
    elif fault == "false_units":
        arm["equity"][3]["units"][SYMBOLS[0]] += 1
    elif fault == "missing_benchmark_entry":
        arm["benchmark_entry"]["entered_symbols"] = []
    elif fault == "false_fee_summary":
        arm["fees_quote"] = 0
    elif fault == "false_cost_trade":
        arm["state"]["trades"][0]["execution_price"] = 1
    elif fault == "missing_trace":
        arm["state"]["signal_bridge"]["decisions"] = []
    elif fault == "missing_mark":
        del arm["state"]["history"][2]["close"][SYMBOLS[0]]
    elif fault == "incomplete_arm":
        arm["status"] = "INCOMPLETE"
    elif fault == "false_profile":
        arm["state"]["profile"]["fee"] = 0
    elif fault == "missing_arm":
        del case["arms"]["cash"]
    elif fault == "changed_recipe":
        broken["stress"][0]["comparison_contract"]["evaluation_end_ms"] += 2*H
    elif fault == "changed_mix":
        case["comparison_contract"]["mix"][SYMBOLS[0]] = F(1,2)
    elif fault == "different_arm_prices":
        arm["state"]["history"][1]["close"][SYMBOLS[1]] = 101
    else:
        broken["stress"][0]["arms"]["cash"]["state"]["signal_bridge"]["binding"] = "changed"
    result = build(broken)
    assert result["status"] == "INCOMPLETE"
    assert result["net_profit_usd_by_alternative"] is None
    assert all(len(a["coverage"]) == 25 for c in result["cases"].values() for a in c["diagnostics"].values())


def test_partial_period_and_missing_chunk_are_not_complete_evidence(journals):
    partial = {label: [chunks[0]] for label, chunks in journals[1].items()}
    result = build(partial)
    assert result["status"] == "INCOMPLETE" and result["net_profit_usd_by_alternative"] is None
    tail_only = {label: [chunks[-1]] for label, chunks in journals[1].items()}
    assert build(tail_only)["status"] == "INCOMPLETE"


def test_required_historical_valuation_sidecar_is_not_invented_or_taken_from_future(journals):
    modified = deepcopy(journals[0])
    ts = A + 3*H
    for cases in modified.values():
        for arm in cases[0]["arms"].values():
            del arm["state"]["history"][2]["close"][SYMBOLS[0]]
    assert build(modified)["status"] == "INCOMPLETE"
    marks = {SYMBOLS[0]: [{"ts_ms": ts, "known_at_ms": ts, "price": 100}]}
    result = report.build_descriptive_report(modified, symbols=SYMBOLS,
        monthly_overhead=20, valuation_marks=marks)
    assert result == build(journals[0])
    marks[SYMBOLS[0]][0]["known_at_ms"] = ts + 1
    assert report.build_descriptive_report(modified, symbols=SYMBOLS,
        monthly_overhead=20, valuation_marks=marks)["status"] == "INCOMPLETE"


def test_25_scope_and_both_cost_cases_are_explicit(journals):
    with pytest.raises(ValueError):
        report.build_descriptive_report(journals[0], symbols=SYMBOLS[:2], monthly_overhead=20)
    with pytest.raises(ValueError):
        report.build_descriptive_report({"primary": journals[0]["primary"]}, symbols=SYMBOLS, monthly_overhead=20)
    with pytest.raises(ValueError):
        report.build_descriptive_report(journals[0], symbols=SYMBOLS, monthly_overhead=0)
