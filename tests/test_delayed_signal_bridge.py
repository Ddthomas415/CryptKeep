"""Fixed-delay contracts on invented hourly prices, not a market study."""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction as F
import math
from pathlib import Path
import socket
import subprocess

import pytest

from services.backtest import delayed_signal_bridge as delayed
from services.backtest import frozen_signal_bridge as frozen
from services.backtest import shared_cash_research as ledger


H = frozen.HOUR
ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = (ROOT / "research/multisymbol_baseline_v1/strategies.snapshot.json").read_bytes()


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("synthetic delay test attempted external work")
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, forbidden)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, forbidden)


def data(symbols=("A", "B"), count=307, start=0, latency=1):
    return {s: [{"row": [start+i*H, 100., 102., 98., 100., 1000.],
                 "known_at_ms": start+(i+1)*H+latency} for i in range(count)] for s in symbols}


def permissions(symbols=("A", "B")):
    return {s: [{"known_at_ms": 0, "valid_from_ms": 0, "valid_until_ms": 9_999_999_999_999,
        "venue": "SYNTHETIC", "quote": "USD", "eligible": True, "lot_step": ".000001",
        "quote_step": ".000001", "minimum_qty": 0, "minimum_notional_gross": 0}] for s in symbols}


def frames(panel, first=300, last=None):
    symbols = tuple(panel)
    last = len(panel[symbols[0]]) if last is None else last
    return [{"ts_ms": panel[symbols[0]][i]["row"][0],
             "open": {s: panel[s][i]["row"][1] for s in symbols},
             "close": {s: panel[s][i]["row"][4] for s in symbols}} for i in range(first, last)]


def runner(panel, rules=None, family="ema_cross_default", incumbent=None, **extra):
    symbols = tuple(panel)
    rules = permissions(symbols) if rules is None else rules
    callback = delayed.DelayedSignalBridge(symbols=symbols, observations=panel, rules=rules,
        venue="SYNTHETIC", quote="USD", snapshot_bytes=SNAPSHOT,
        family=None if incumbent else family, incumbent=incumbent, **extra)
    profile = dict(symbols=symbols, rules=rules, venue="SYNTHETIC", quote="USD", interval_ms=H,
        initial_cash=1000, fee_bps=0, slippage_bps=0, target_contract_id="synthetic-delay")
    return callback, profile


def scripted(monkeypatch, actions, seen=None):
    def signal(*, cfg, symbol, ohlcv):
        if seen is not None:
            seen.append((symbol, deepcopy(ohlcv)))
        return {"ok": True, "action": actions.get((ohlcv[-1][0], symbol), "hold")}
    monkeypatch.setattr(frozen, "compute_signal", signal)


@pytest.mark.parametrize("latency", [1, H//2, H])
def test_receipt_allowance_preserves_original_timestamps_and_one_hour_fill(monkeypatch, latency):
    panel = data(latency=latency)
    original = deepcopy(panel)
    seen = []
    scripted(monkeypatch, {(299*H, "A"): "buy"}, seen)
    callback, profile = runner(panel)
    result = delayed.simulate_delayed_bridge(frames(panel), callback, **profile)
    assert result["status"] == "COMPLETE" and panel == original
    trade = result["bridge_trades"][0]
    assert trade["ts_ms"] == 301*H
    assert trade["strategy_signal_bar_ts_ms"] == 299*H
    assert trade["receipt_cutoff_ms"] == 301*H
    assert callback.trace[0]["signal_close_ms"] == 300*H
    assert len(seen[0][1]) == 300 and seen[0][1][-1][0] == 299*H
    assert callback.panel.rows == original and callback.panel.cutoff is None


def test_receipt_after_cutoff_is_incomplete_not_silently_retimestamped(monkeypatch):
    panel = data()
    panel["A"][299]["known_at_ms"] = 301*H+1
    scripted(monkeypatch, {(299*H, "A"): "buy"})
    callback, profile = runner(panel)
    result = delayed.simulate_delayed_bridge(frames(panel), callback, **profile)
    assert result["status"] == "INCOMPLETE" and result["state"] is None
    assert "unavailable_ohlcv" in result["reason"] and callback.panel.cutoff is None


def test_availability_extension_defaults_preserve_immediate_guard():
    panel = data()
    p = frozen.HourlyPanel(panel)
    with pytest.raises(ledger.Incomplete):
        p.window("A", 300*H, 300)
    assert len(p.window("A", 300*H, 300, available_by_ms=301*H)) == 300
    with pytest.raises(ValueError, match="precedes"):
        p.window("A", 300*H, 300, available_by_ms=300*H-1)


def test_fill_uses_later_open_not_signal_close_or_immediate_open(monkeypatch):
    panel = data()
    panel["A"][300]["row"][1:5] = [150., 152., 148., 150.]
    panel["A"][301]["row"][1:5] = [200., 202., 198., 200.]
    scripted(monkeypatch, {(299*H, "A"): "buy"})
    callback, profile = runner(panel)
    result = delayed.simulate_delayed_bridge(frames(panel), callback, **profile)
    trade = result["bridge_trades"][0]
    assert trade["raw_price"] == 200 and trade["ts_ms"] == 301*H
    assert not any(t["ts_ms"] == 300*H for t in result["bridge_trades"])


def test_intervening_bar_does_not_leak_into_signal_or_signal_close_allocation(monkeypatch):
    panel = data()
    seen = []
    scripted(monkeypatch, {(299*H, "A"): "buy", (300*H, "B"): "buy"}, seen)
    callback, profile = runner(panel)
    f = frames(panel)
    c = {"history": [f[0]], "close_ms": 301*H, "units": {"A": 1, "B": 0},
         "cash": 900, "marked_nav": 999999, "basis": {"A": 100, "B": 0}}
    # Current-frame valuation is not a signal feature or target-size input.
    panel["A"][300]["row"][1:5] = [200., 202., 198., 200.]
    callback, _ = runner(panel)
    c["history"] = [frames(panel)[0]]
    assert callback(c) is None  # BUY while held is ignored; no later B signal yet.
    assert seen[0][1][-1][0] == 299*H
    c["close_ms"], c["history"] = 302*H, [frames(panel)[1]]
    target = callback(c)
    assert target == {"A": F(2, 11), "B": F(1, 25)}


def test_execution_permission_can_cancel_delayed_entry(monkeypatch):
    panel = data()
    rules = permissions()
    rules["A"].append({**rules["A"][0], "known_at_ms": 300*H+1,
        "valid_from_ms": 301*H, "eligible": False})
    scripted(monkeypatch, {(299*H, "A"): "buy"})
    callback, profile = runner(panel, rules)
    result = delayed.simulate_delayed_bridge(frames(panel), callback, **profile)
    assert result["status"] == "COMPLETE" and not result["state"]["trades"]
    assert result["state"]["events"][0]["excluded"][0]["reason"] == "ineligible"


def test_signal_permission_is_not_backdated_from_arrival(monkeypatch):
    panel = data()
    rules = permissions()
    rules["A"][0]["known_at_ms"] = 300*H+1
    scripted(monkeypatch, {(299*H, "A"): "buy"})
    callback, profile = runner(panel, rules)
    result = delayed.simulate_delayed_bridge(frames(panel), callback, **profile)
    assert result["status"] == "INCOMPLETE" and result["state"] is None


@pytest.mark.parametrize("fault", ["signal_gap", "outcome_gap", "outcome_price"])
def test_gaps_and_conflicting_outcome_prices_are_incomplete(monkeypatch, fault):
    panel = data()
    f = frames(panel)
    if fault == "signal_gap":
        del panel["A"][100]
    elif fault == "outcome_gap":
        del panel["A"][300]
    else:
        f[0]["close"]["A"] = 200
    scripted(monkeypatch, {})
    callback, profile = runner(panel)
    result = delayed.simulate_delayed_bridge(f, callback, **profile)
    assert result["status"] == "INCOMPLETE" and result["state"] is None


def test_all25_one_wallet_no_hold_rebalance_or_latched_retry(monkeypatch):
    symbols = tuple("SYN-"+str(i) for i in range(25))
    panel = data(symbols)
    scripted(monkeypatch, {(299*H, s): "buy" for s in symbols})
    callback, profile = runner(panel)
    result = delayed.simulate_delayed_bridge(frames(panel), callback, **profile)
    assert result["status"] == "COMPLETE" and len(result["bridge_trades"]) == 25
    assert result["marked_nav"] == 1000 and result["state"]["cash"] == 0
    assert {t["ts_ms"] for t in result["bridge_trades"]} == {301*H}


def test_controls_and_candidate_share_initial_fill_and_endpoint(monkeypatch):
    panel = data()
    scripted(monkeypatch, {(299*H, "A"): "buy"})
    callback, profile = runner(panel)
    result = ledger.simulate_shared_comparison(frames(panel), callback, btc_symbol="A", eth_symbol="B",
        mix_weights={"A": F(1,4), "B": F(1,4)}, **profile)
    for name in ("candidate", "hold_btc", "declared_btc_eth_cash_mix"):
        assert result[name]["state"]["trades"][0]["ts_ms"] == 301*H
        assert result[name]["equity"][-1]["close_ms"] == 307*H
    assert result["cash"]["marked_nav"] == 1000


def test_full_split_carry_and_historical_receipt_binding(monkeypatch):
    panel = data()
    scripted(monkeypatch, {(299*H, "A"): "buy", (302*H, "A"): "sell"})
    a, profile = runner(panel)
    full = delayed.simulate_delayed_bridge(frames(panel), a, **profile)
    a, profile = runner(panel)
    left = delayed.simulate_delayed_bridge(frames(panel, last=303), a, **profile)
    a, profile = runner(panel)
    right = delayed.simulate_delayed_bridge(frames(panel, first=303), a, state=left["state"], **profile)
    assert right["state"] == full["state"] and right["bridge_trades"] == full["bridge_trades"]
    changed = deepcopy(panel)
    changed["A"][299]["known_at_ms"] += 1
    a, profile = runner(changed)
    with pytest.raises(ValueError, match="historical_inputs"):
        delayed.simulate_delayed_bridge(frames(changed, first=303), a, state=left["state"], **profile)


@pytest.mark.parametrize("family", sorted(frozen.FAMILIES))
def test_real_frozen_families_ignore_future_prices_and_volume(family):
    panel = data()
    changed = deepcopy(panel)
    for symbol in changed:
        for r in changed[symbol][304:]:
            r["row"][1:5] = [500., 502., 498., 500.]
            r["row"][5] = 3.
    a, profile = runner(panel, family=family)
    b, _ = runner(changed, family=family)
    assert delayed.simulate_delayed_bridge(frames(panel, last=304), a, **profile)["state"] == \
        delayed.simulate_delayed_bridge(frames(changed, last=304), b, **profile)["state"]


def test_incumbent_stays_on_sunday_signal_with_monday_one_hour_fill():
    monday = int(datetime(2026, 1, 5, tzinfo=timezone.utc).timestamp()*1000)
    panel = data(count=61*24+4, start=monday-61*frozen.DAY)
    for records in panel.values():
        for i, r in enumerate(records):
            p = 100+i*.01+math.sin(i/24)
            r["row"][1:5] = [p, p+2, p-2, p]
    callback, profile = runner(panel, incumbent=("A", "B"))
    result = delayed.simulate_delayed_bridge(frames(panel, first=61*24), callback, **profile)
    assert result["status"] == "COMPLETE"
    assert {t["ts_ms"] for t in result["bridge_trades"]} == {monday+H}
    assert callback.trace[0]["signal_close_ms"] == monday
    assert all(t["strategy_signal_bar_ts_ms"] == monday-H for t in result["bridge_trades"])
    assert callback.trace[1]["targets"] is None


def test_explicit_delay_profile_cannot_resume_immediate_account(monkeypatch):
    panel = data(latency=0)
    scripted(monkeypatch, {(299*H, "A"): "buy"})
    callback, profile = runner(panel)
    direct = frozen.FrozenSignalBridge(symbols=tuple(panel), observations=panel, rules=profile["rules"],
        venue="SYNTHETIC", quote="USD", snapshot_bytes=SNAPSHOT, family="ema_cross_default")
    old = frozen.simulate_bridge(frames(panel, last=303), direct, **profile)
    with pytest.raises(ValueError, match="historical_inputs"):
        delayed.simulate_delayed_bridge(frames(panel, first=303), callback, state=old["state"], **profile)
    with pytest.raises(ValueError, match="explicit_delayed"):
        delayed.simulate_delayed_bridge(frames(panel), direct, **profile)


def test_known_ineligible_asset_does_not_require_candles(monkeypatch):
    complete = data()
    panel = deepcopy(complete)
    panel["A"] = []
    rules = permissions()
    rules["A"][0]["eligible"] = False
    scripted(monkeypatch, {})
    callback, profile = runner(panel, rules)
    result = delayed.simulate_delayed_bridge(frames(complete), callback, **profile)
    assert result["status"] == "COMPLETE"
    assert callback.trace[0]["readiness"]["A"] == "known_ineligible"


def test_exhausted_account_has_no_signal_or_data_requirement():
    callback, _ = runner({"A": [], "B": []})
    c = {"history": [{"ts_ms": 300*H, "open": {}, "close": {}}],
         "close_ms": 301*H, "units": {"A": 0, "B": 0}, "cash": 0, "marked_nav": 0}
    assert callback(c) is None
    assert set(callback.trace[-1]["readiness"].values()) == {"exhausted_account"}


def test_missing_execution_open_expires_without_latching_entry(monkeypatch):
    panel = data()
    f = frames(panel)
    del f[1]["open"]["A"]
    scripted(monkeypatch, {(299*H, "A"): "buy"})
    callback, profile = runner(panel)
    result = delayed.simulate_delayed_bridge(f, callback, **profile)
    assert result["status"] == "COMPLETE" and not result["state"]["trades"]
    assert result["state"]["events"][0]["excluded"][0]["reason"] == "missing_execution_open"


def test_fees_and_lot_affordability_remain_in_the_shared_ledger(monkeypatch):
    panel = data(tuple("SYN-"+str(i) for i in range(25)))
    scripted(monkeypatch, {(299*H, s): "buy" for s in panel})
    callback, profile = runner(panel)
    profile.update(fee_bps=50, slippage_bps=25)
    result = delayed.simulate_delayed_bridge(frames(panel), callback, **profile)
    assert result["status"] == "COMPLETE" and result["state"]["cash"] >= 0
    assert result["fees_quote"] > 0 and result["slippage_quote"] > 0
    assert result["net_profit"] < 0


def test_terminal_pending_signal_is_not_executed_beyond_endpoint(monkeypatch):
    panel = data()
    scripted(monkeypatch, {(305*H, "A"): "buy"})
    callback, profile = runner(panel)
    result = delayed.simulate_delayed_bridge(frames(panel), callback, **profile)
    assert result["status"] == "COMPLETE" and not result["state"]["trades"]
    assert result["state"]["pending"]["execution_ms"] == 307*H


def test_incumbent_does_not_acquire_unrelated_universe_signal_requirements():
    monday = int(datetime(2026, 1, 5, tzinfo=timezone.utc).timestamp()*1000)
    panel = data(count=61*24+3, start=monday-61*frozen.DAY)
    for records in panel.values():
        for i, r in enumerate(records):
            p = 100+i*.01+math.sin(i/24)
            r["row"][1:5] = [p, p+2, p-2, p]
    f = frames(panel, first=61*24)
    panel["UNRELATED"] = []
    callback, profile = runner(panel, rules=permissions(("A", "B")), incumbent=("A", "B"))
    assert delayed.simulate_delayed_bridge(f, callback, **profile)["status"] == "COMPLETE"


def test_unreceived_outcome_price_cannot_be_rewritten_across_resume(monkeypatch):
    panel = data()
    panel["A"][302]["known_at_ms"] = 500*H
    scripted(monkeypatch, {})
    callback, profile = runner(panel)
    left = delayed.simulate_delayed_bridge(frames(panel, last=303), callback, **profile)
    assert left["status"] == "COMPLETE"  # This bar was marking-only, not a signal input yet.
    changed = deepcopy(panel)
    changed["A"][302]["row"][1:5] = [200., 202., 198., 200.]
    callback, profile = runner(changed)
    with pytest.raises(ValueError, match="historical_inputs"):
        delayed.simulate_delayed_bridge(frames(changed, first=303), callback, state=left["state"], **profile)


def test_delayed_sell_annotation_and_incidental_turnover_remain_traceable(monkeypatch):
    panel = data()
    scripted(monkeypatch, {(299*H, "A"): "buy", (301*H, "A"): "sell"})
    callback, profile = runner(panel)
    result = delayed.simulate_delayed_bridge(frames(panel), callback, **profile)
    buys, sells = result["bridge_trades"]
    assert buys["raw_action"] == "buy" and sells["raw_action"] == "sell"
    assert sells["ts_ms"] == sells["strategy_signal_bar_ts_ms"] + 2*H
    assert sells["incidental_rebalance"] is False and result["incidental_turnover_quote"] == 0
