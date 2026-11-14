"""Invented prices/fills only; not a market experiment or execution validation."""
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import importlib.util
from pathlib import Path
import socket
import subprocess

import pytest

from services.backtest import dual_exit_bridge as dual
from services.backtest import frozen_signal_bridge as frozen
from services.backtest import shared_cash_research as ledger
from tests.test_delayed_signal_bridge import data, frames, permissions, SNAPSHOT, scripted


H = frozen.HOUR
ROOT = Path(__file__).resolve().parents[1]
SOURCE_MANIFEST_SHA = hashlib.sha256(b"synthetic caller-declared source manifest fixture").hexdigest()


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("synthetic dual-exit test attempted external work")
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, forbidden)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, forbidden)


def bridge_for(panel, model="R-H1D", configuration="ema_cross_default", rules=None, marks=None):
    rules = permissions(tuple(panel)) if rules is None else rules
    bridge = dual.DualExitBridge(configuration=configuration, exit_model=model,
        source_manifest_sha256=SOURCE_MANIFEST_SHA,
        symbols=tuple(panel), observations=panel, rules=rules, venue="SYNTHETIC", quote="USD", snapshot_bytes=SNAPSHOT,
        valuation_marks=marks)
    profile = dict(symbols=tuple(panel), venue="SYNTHETIC", quote="USD", rules=rules,
        interval_ms=H, initial_cash=1000, fee_bps=50, slippage_bps=25, target_contract_id="synthetic-dual",
        valuation_marks=marks or {})
    return bridge, profile


def fill(ts, side="buy", qty=1, price=100, symbol="A"):
    return {"ts_ms": ts * H, "side": side, "qty": F(qty), "execution_price": F(price),
            "symbol": symbol, "terminal": False}


def panel_prices(closes):
    observations = {"A": [{"row": [i * H, p, p + 1, p - 1, p, 10], "known_at_ms": (i + 1) * H}
                           for i, p in enumerate(closes)]}
    return frozen.HourlyPanel(observations)


@pytest.mark.parametrize("configuration", list(dual.CONFIGURATIONS))
@pytest.mark.parametrize("model", dual.EXIT_MODELS)
def test_all_twelve_policies_are_explicit_and_snapshot_unchanged(configuration, model):
    bridge, _ = bridge_for(data(), model, configuration)
    recipe = dual.policy_recipe(configuration, model, source_manifest_sha256=SOURCE_MANIFEST_SHA)
    assert bridge.recipe == recipe
    assert recipe["snapshot_sha256"] == hashlib.sha256(SNAPSHOT).hexdigest()
    if configuration.endswith("exit_unblocked"):
        assert bridge.config["strategy"]["filters_apply_to_sell"] is False
    else:
        assert "filters_apply_to_sell" not in bridge.config["strategy"]
    assert frozen.FAMILIES == {"breakout_default", "ema_cross_default", "mean_reversion_default"}


@pytest.mark.parametrize("configuration,model", [(False, "S"), ([], "S"), ("ema_cross_default", []), ("bad", "S"), ("ema_cross_default", "path")])
def test_malformed_or_unadopted_recipes_rejected(configuration, model):
    with pytest.raises(ValueError, match="unknown_dual_exit_policy"):
        dual.policy_recipe(configuration, model)


def test_legacy_profile_context_and_output_equal_preserved_source():
    path = ROOT / "docs/review_artifacts/ed002_dual_exit_adapter_20261114/before/shared_cash_research.py"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "3625c91f7d9af17daa685f6c118d175387d5d132dc6209aafb2d50c5271333cc"
    spec = importlib.util.spec_from_file_location("ledger_before_dual", path)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    panel = data(("A",), count=5)
    seen = []
    def target(c):
        seen.append(deepcopy(c))
        return {"A": F(1, 25)} if c["decision_index"] == 0 else None
    args = dict(symbols=("A",), venue="SYNTHETIC", quote="USD", interval_ms=H, initial_cash=1000,
                fee_bps=50, slippage_bps=25, rules=permissions(("A",)), target_contract_id="legacy")
    prior = old.simulate_shared_next_open(frames(panel, first=0), target, **args)
    old_seen, seen[:] = deepcopy(seen), []
    current = ledger.simulate_shared_next_open(frames(panel, first=0), target, **args)
    assert prior == current and seen == old_seen
    assert all("model_trades" not in c for c in seen)
    assert "decision_trade_context" not in current["state"]["profile"]


def test_opt_in_evidence_is_copied_and_profile_bound():
    panel = data(("A",), count=4)
    def target(c):
        assert "model_trades" in c
        c["model_trades"].append({"fake": True})
        c["model_events"].append({"fake": True})
        return None
    args = dict(symbols=("A",), venue="SYNTHETIC", quote="USD", interval_ms=H, initial_cash=1000,
                fee_bps=0, slippage_bps=0, rules=permissions(("A",)), target_contract_id="context")
    out = ledger.simulate_shared_with_trade_context(frames(panel, first=0), target, **args)
    assert out["state"]["trades"] == [] and out["state"]["events"] == []
    assert out["state"]["profile"]["decision_trade_context"] is True
    with pytest.raises(ValueError, match="same_contract"):
        ledger.simulate_shared_next_open([{"ts_ms": 4 * H, "open": {"A": 100}, "close": {"A": 100}}],
                                        target, state=out["state"], **args)


def test_reference_age_and_peak_use_actual_fills_and_strictly_later_closes():
    panel = panel_prices([500, 110, 200, 105, 100])
    trades = [fill(1), fill(3), fill(3, "sell", F(1, 2))]
    state = dual.derive_positions(trades, {"A": F(3, 2)}, panel, 3 * H, price_peaks=True)["A"]
    assert state == {"original_entry_fill_ts": H, "last_reference_fill_ts": 3 * H,
                     "reference": F(100), "peak": F(110), "qty": F(3, 2)}
    assert dual.stack_exit(state, 500, 3 * H, "ema_cross") is None
    assert dual.stack_exit(state, 105, 4 * H, "ema_cross") == "trailing_stop"


def test_added_buy_weighted_reference_does_not_include_fees_or_reset_age_peak():
    state = dual.derive_positions([fill(1), fill(3, qty=2, price=130)], {"A": 3},
                                 panel_prices([500, 110, 200, 130]), 3 * H, price_peaks=True)["A"]
    assert state["reference"] == 120 and state["original_entry_fill_ts"] == H
    assert state["last_reference_fill_ts"] == 3 * H and state["peak"] == 110


def test_flat_reset_and_bad_fill_evidence():
    panel = panel_prices([100] * 6)
    trades = [fill(1), fill(2, "sell"), fill(4, price=90)]
    state = dual.derive_positions(trades, {"A": 1}, panel, 4 * H, price_peaks=True)["A"]
    assert state["reference"] == 90 and state["peak"] == 90
    assert state["original_entry_fill_ts"] == state["last_reference_fill_ts"] == 4 * H
    for bad in ([fill(5)], [fill(2), fill(1)], [fill(1, "sell")], [{**fill(1), "qty": True}]):
        with pytest.raises(ledger.Incomplete):
            dual.derive_positions(bad, {"A": 1}, panel, 4 * H, price_peaks=True)


@pytest.mark.parametrize("mark,peak,age,reason", [(96, 100, 1, "stop_loss"), (100, 110, 1, "trailing_stop"),
    (106, 106, 1, "take_profit"), (100, 100, 60, "time_stop"), (100, 100, 59, None)])
def test_stack_priority_and_decision_time(mark, peak, age, reason):
    pos = {"reference": F(100), "peak": F(peak), "qty": F(1),
           "original_entry_fill_ts": H, "last_reference_fill_ts": H}
    assert dual.stack_exit(pos, mark, (age + 1) * H, "ema_cross") == reason


def test_time_exit_can_sell_recent_addition_but_does_not_use_execution_clock():
    pos = {"reference": F(100), "peak": F(200), "qty": F(2),
           "original_entry_fill_ts": H, "last_reference_fill_ts": 61 * H}
    assert dual.stack_exit(pos, 80, 61 * H, "ema_cross") == "time_stop"
    pos["last_reference_fill_ts"] = 60 * H
    assert dual.stack_exit(pos, 80, 60 * H, "ema_cross") is None


def test_missing_late_peak_or_unrepresentable_reference_is_incomplete():
    panel = panel_prices([100] * 4)
    panel.rows["A"][1]["known_at_ms"] = 4 * H
    with pytest.raises(ledger.Incomplete, match="peak_history"):
        dual.derive_positions([fill(1)], {"A": 1}, panel, 3 * H, price_peaks=True)
    pos = {"reference": F(10**500), "peak": F(10**500), "qty": F(1),
           "original_entry_fill_ts": H, "last_reference_fill_ts": H}
    with pytest.raises(ledger.Incomplete, match="numeric_range"):
        dual.stack_exit(pos, 100, 2 * H, "ema_cross")


@pytest.mark.parametrize("model", dual.EXIT_MODELS)
def test_actual_fill_reference_and_full_split_carry(monkeypatch, model):
    panel = data(count=311)
    scripted(monkeypatch, {(299 * H, "A"): "buy", (304 * H, "A"): "sell"})
    callback, profile = bridge_for(panel, model)
    full = dual.simulate_dual_exit_bridge(frames(panel), callback, **profile)
    callback, _ = bridge_for(panel, model)
    left = dual.simulate_dual_exit_bridge(frames(panel)[:3], callback, **profile)
    state = left["state"]["dual_exit"]["positions"]["A"]
    assert state["reference"] == left["state"]["trades"][0]["execution_price"] == F(401, 4)
    callback, _ = bridge_for(panel, model)
    right = dual.simulate_dual_exit_bridge(frames(panel)[3:], callback, state=left["state"], **profile)
    assert full["status"] == right["status"] == "COMPLETE"
    assert full["state"] == right["state"]
    assert full["equity"] == left["equity"] + right["equity"]
    assert full["study_ready"] is False and full["event_policy_implemented"] is False


def test_delayed_gap_fill_not_trigger_level_or_three_percent_cap(monkeypatch):
    panel = data(count=307)
    panel["A"][301]["row"][1:5] = [100., 101., 94., 95.]
    for i in (302, 303):
        panel["A"][i]["row"][1:5] = [70., 71., 69., 70.]
    scripted(monkeypatch, {(299 * H, "A"): "buy"})
    callback, profile = bridge_for(panel)
    out = dual.simulate_dual_exit_bridge(frames(panel), callback, **profile)
    assert out["status"] == "COMPLETE"
    buy, sell = out["bridge_trades"][:2]
    assert sell["ts_ms"] == 303 * H and sell["raw_price"] == 70
    assert sell["exit_rule"] == "stop_loss" and sell["strategy_action"] == "hold"
    assert sell["execution_price"] / buy["execution_price"] < F(3, 4)


def test_held_restriction_and_missing_context_cannot_be_complete(monkeypatch):
    panel = data()
    rules = permissions()
    rules["A"].append({**rules["A"][0], "known_at_ms": 301 * H, "valid_from_ms": 302 * H, "eligible": False})
    scripted(monkeypatch, {(299 * H, "A"): "buy"})
    callback, profile = bridge_for(panel, rules=rules)
    out = dual.simulate_dual_exit_bridge(frames(panel), callback, **profile)
    assert out["status"] == "INCOMPLETE" and out["net_profit"] is None
    assert "held_exit_permission" in out["reason"]
    callback, profile = bridge_for(panel)
    out = frozen.simulate_bridge(frames(panel), callback, **profile)
    assert out["status"] == "INCOMPLETE" and out["state"] is None
    assert "fill_context" in out["reason"]


def test_resume_rejects_edited_peak_policy_and_missing_state(monkeypatch):
    panel = data(count=309)
    scripted(monkeypatch, {(299 * H, "A"): "buy"})
    callback, profile = bridge_for(panel)
    left = dual.simulate_dual_exit_bridge(frames(panel)[:3], callback, **profile)
    for corrupt in ("peak", "missing", "policy"):
        state = deepcopy(left["state"])
        if corrupt == "peak":
            state["dual_exit"]["positions"]["A"]["peak"] = 999
        elif corrupt == "missing":
            state.pop("dual_exit")
        else:
            state["dual_exit"]["recipe"]["exit_model"] = "S"
        callback, _ = bridge_for(panel)
        with pytest.raises(ValueError, match="resume_state"):
            dual.simulate_dual_exit_bridge(frames(panel)[3:], callback, state=state, **profile)


def test_all25_symbols_share_one_account(monkeypatch):
    panel = data(tuple(f"SYN-{i:02}" for i in range(25)), count=304)
    scripted(monkeypatch, {(299 * H, s): "buy" for s in panel})
    callback, profile = bridge_for(panel)
    out = dual.simulate_dual_exit_bridge(frames(panel), callback, **profile)
    assert out["status"] == "COMPLETE" and len(out["state"]["units"]) == 25
    assert len(out["state"]["trades"]) == 25 and out["state"]["cash"] >= 0
    assert out["marked_nav"] <= 1000


def test_resume_rejects_forged_execution_price_even_with_matching_derived_state(monkeypatch):
    panel = data(count=309)
    scripted(monkeypatch, {(299 * H, "A"): "buy"})
    callback, profile = bridge_for(panel)
    left = dual.simulate_dual_exit_bridge(frames(panel)[:3], callback, **profile)
    state = deepcopy(left["state"])
    state["trades"][0]["execution_price"] *= 2
    callback, _ = bridge_for(panel)
    state["dual_exit"]["positions"] = callback.positions(state["trades"], state["units"], state["last_ts"])
    with pytest.raises(ValueError, match="fill_ledger"):
        dual.simulate_dual_exit_bridge(frames(panel)[3:], callback, state=state, **profile)


def test_prescribed_held_exit_missing_execution_open_is_incomplete(monkeypatch):
    panel = data(count=307)
    panel["A"][301]["row"][1:5] = [100., 101., 94., 95.]
    for i in (302, 303):
        panel["A"][i]["row"][1:5] = [70., 71., 69., 70.]
    scripted(monkeypatch, {(299 * H, "A"): "buy"})
    marks = {"A": [{"ts_ms": 303 * H, "known_at_ms": 303 * H, "price": 70}]}
    callback, profile = bridge_for(panel, marks=marks)
    supplied = frames(panel)
    supplied[3]["open"].pop("A")
    out = dual.simulate_dual_exit_bridge(supplied, callback, **profile)
    assert out["status"] == "INCOMPLETE" and out["net_profit"] is None
    assert "required_held_exit" in out["reason"]
    assert out["state"]["units"]["A"] > 0


@pytest.mark.parametrize("configuration", list(dual.CONFIGURATIONS))
@pytest.mark.parametrize("model", dual.EXIT_MODELS)
def test_all_twelve_real_signal_paths_complete_on_invented_flat_data(configuration, model):
    panel = data(count=304)
    callback, profile = bridge_for(panel, model, configuration)
    out = dual.simulate_dual_exit_bridge(frames(panel), callback, **profile)
    assert out["status"] == "COMPLETE" and not out["state"]["trades"]
    assert out["marked_nav"] == 1000 and out["comparison_ready"] is False


def test_s_overlay_uses_real_final_action_not_raw_observer(monkeypatch):
    panel = data(count=305)
    for records in panel.values():
        for i, record in enumerate(records):
            p = 100 + i / 10
            record["row"][1:5] = [p, p + .2, p - .2, p]
    actual = frozen.compute_signal
    def enter_then_real(*, cfg, symbol, ohlcv):
        if ohlcv[-1][0] == 299 * H and symbol == "A":
            return {"ok": True, "action": "buy"}
        return actual(cfg=cfg, symbol=symbol, ohlcv=ohlcv)
    monkeypatch.setattr(frozen, "compute_signal", enter_then_real)
    outputs = {}
    for configuration in ("mean_reversion_default", "mean_reversion_exit_unblocked"):
        callback, profile = bridge_for(panel, "S", configuration)
        outputs[configuration] = dual.simulate_dual_exit_bridge(frames(panel), callback, **profile)
    default, variant = outputs.values()
    assert all(x["status"] == "COMPLETE" for x in outputs.values())
    assert default["state"]["units"]["A"] > 0
    assert variant["state"]["units"]["A"] == 0
    assert variant["bridge_trades"][1]["strategy_action"] == "sell"
    assert variant["bridge_trades"][1]["ts_ms"] == 302 * H


def test_real_incidental_addition_keeps_old_age_and_can_time_exit(monkeypatch):
    panel = data(count=365)
    for i in (361, 362):
        panel["A"][i]["row"][1:5] = [80., 81., 79., 80.]
    scripted(monkeypatch, {(299 * H, "A"): "buy", (359 * H, "B"): "buy"})
    callback, profile = bridge_for(panel)
    out = dual.simulate_dual_exit_bridge(frames(panel), callback, **profile)
    assert out["status"] == "COMPLETE"
    buys = [t for t in out["bridge_trades"] if t["symbol"] == "A" and t["side"] == "buy"]
    assert len(buys) == 2 and [t["ts_ms"] for t in buys] == [301 * H, 361 * H]
    sells = [t for t in out["bridge_trades"] if t["symbol"] == "A" and t["side"] == "sell"]
    assert sells[0]["ts_ms"] == 362 * H and sells[0]["exit_rule"] == "time_stop"
    note = next(t for t in out["state"]["signal_bridge"]["decisions"] if t["signal_close_ms"] == 361 * H)
    assert note["derived_positions"]["A"]["original_entry_fill_ts"] == 301 * H
    assert note["derived_positions"]["A"]["last_reference_fill_ts"] == 361 * H
    assert next(t for t in out["state"]["signal_bridge"]["decisions"] if t["signal_close_ms"] == 360 * H)["exit_rules"] == {}


def test_future_change_does_not_change_past_state_but_past_change_rejects_carry(monkeypatch):
    panel = data(count=309)
    scripted(monkeypatch, {(299 * H, "A"): "buy"})
    callback, profile = bridge_for(panel)
    left = dual.simulate_dual_exit_bridge(frames(panel)[:3], callback, **profile)
    future = deepcopy(panel)
    future["A"][305]["row"][1:5] = [150., 151., 149., 150.]
    callback, _ = bridge_for(future)
    other = dual.simulate_dual_exit_bridge(frames(future)[:3], callback, **profile)
    assert left["state"] == other["state"]
    past = deepcopy(panel)
    past["A"][301]["row"][4] = 100.5
    callback, _ = bridge_for(past)
    with pytest.raises((ValueError, ledger.Incomplete)):
        dual.simulate_dual_exit_bridge(frames(past)[3:], callback, state=left["state"], **profile)


def test_resume_rejects_alternate_frame_ledger_with_transplanted_input_binding(monkeypatch):
    panel = data(count=309)
    scripted(monkeypatch, {(299 * H, "A"): "buy"})
    callback, profile = bridge_for(panel)
    original = dual.simulate_dual_exit_bridge(frames(panel)[:3], callback, **profile)
    alternate = deepcopy(panel)
    for i in (301, 302):
        alternate["A"][i]["row"][1:5] = [200., 201., 199., 200.]
    callback, _ = bridge_for(alternate)
    fake = dual.simulate_dual_exit_bridge(frames(alternate)[:3], callback, **profile)
    fake["state"]["signal_bridge"]["binding"] = original["state"]["signal_bridge"]["binding"]
    callback, _ = bridge_for(panel)
    with pytest.raises(ValueError, match="fill_ledger"):
        dual.simulate_dual_exit_bridge(frames(panel)[3:], callback, state=fake["state"], **profile)


@pytest.mark.parametrize("corruption", ["injected", "altered", "deleted"])
def test_pending_target_must_be_derived_from_policy_not_two_serialized_copies(monkeypatch, corruption):
    panel = data(count=309)
    actions = {(299 * H, "A"): "buy"}
    if corruption != "injected":
        actions[(300 * H, "B")] = "buy"
    scripted(monkeypatch, actions)
    callback, profile = bridge_for(panel)
    left = dual.simulate_dual_exit_bridge(frames(panel)[:2], callback, **profile)
    state = deepcopy(left["state"])
    target = None if corruption == "deleted" else {"A": F(1, 2), "B": F(0)}
    state["signal_bridge"]["decisions"][-1]["targets"] = target
    state["pending"] = None if target is None else {"weights": target, "signal_ms": state["last_ts"],
                                                     "execution_ms": state["last_ts"] + H}
    callback, _ = bridge_for(panel)
    with pytest.raises(ValueError, match="policy_history"):
        dual.simulate_dual_exit_bridge(frames(panel)[2:], callback, state=state, **profile)


def test_consistent_altered_executed_target_is_not_accepted_as_strategy_decision(monkeypatch):
    panel = data(count=309)
    scripted(monkeypatch, {(299 * H, "A"): "buy"})
    callback, profile = bridge_for(panel)
    left = dual.simulate_dual_exit_bridge(frames(panel)[:3], callback, **profile)
    state = deepcopy(left["state"])
    scratch = deepcopy(state)
    scratch.update(cash=F(1000), units={"A": F(0), "B": F(0)}, basis={"A": F(0), "B": F(0)},
                   fee=F(0), slippage=F(0), rounding=F(0), realized=F(0), trades=[], events=[])
    event = state["events"][0]
    target = {"A": F(1, 2), "B": F(0)}
    frame = next(f for f in state["history"] if f["ts_ms"] == event["ts_ms"])
    marks = ledger.marks_at(frame["open"], {}, tuple(panel), event["ts_ms"])
    pre = deepcopy(scratch["units"])
    scratch = ledger.batch(scratch, target, frame["open"], marks, callback.rules,
                           ts=event["ts_ms"], source_ts=event["signal_bar_ts_ms"], interval=H)
    scratch["events"][-1].update(target_weights=target, pre_batch_units=pre)
    for key in ("cash", "units", "basis", "fee", "slippage", "rounding", "realized", "trades", "events"):
        state[key] = scratch[key]
    state["last_nav"] = ledger.nav(state, state["last_marks"])
    state["signal_bridge"]["decisions"][0]["targets"] = target
    state["dual_exit"]["positions"] = callback.positions(state["trades"], state["units"], state["last_ts"])
    dual.validate_fill_ledger(state, callback)  # Financial validity is not policy provenance.
    callback, _ = bridge_for(panel)
    with pytest.raises(ValueError, match="policy_history"):
        dual.simulate_dual_exit_bridge(frames(panel)[3:], callback, state=state, **profile)


@pytest.mark.parametrize("value", [None, True, "bad", "F" * 64, 0])
def test_source_manifest_binding_required(value):
    with pytest.raises(ValueError, match="source_manifest"):
        dual.policy_recipe("ema_cross_default", "S", source_manifest_sha256=value)


def test_different_declared_source_manifest_refuses_carry(monkeypatch):
    panel = data(count=309)
    scripted(monkeypatch, {(299 * H, "A"): "buy"})
    callback, profile = bridge_for(panel)
    left = dual.simulate_dual_exit_bridge(frames(panel)[:3], callback, **profile)
    callback = dual.DualExitBridge(configuration="ema_cross_default", exit_model="R-H1D",
        source_manifest_sha256="a" * 64, symbols=tuple(panel), observations=panel, rules=permissions(),
        venue="SYNTHETIC", quote="USD", snapshot_bytes=SNAPSHOT)
    with pytest.raises(ValueError, match="resume_state"):
        dual.simulate_dual_exit_bridge(frames(panel)[3:], callback, state=left["state"], **profile)
