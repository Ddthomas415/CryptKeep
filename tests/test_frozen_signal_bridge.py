"""Synthetic bridge contracts; saved strategy JSON is metadata, not price data."""
import ast
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction as F
import math
from pathlib import Path
import socket
import statistics
import subprocess

import pytest

from services.backtest import frozen_signal_bridge as bridge
from services.backtest import shared_cash_research as ledger
from services.strategies.strategy_registry import compute_signal


H = bridge.HOUR
ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = (ROOT / "research/multisymbol_baseline_v1/strategies.snapshot.json").read_bytes()


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("synthetic bridge attempted external work")
    for name in ("socket", "create_connection", "getaddrinfo"):
        monkeypatch.setattr(socket, name, forbidden)
    for name in ("Popen", "run", "call", "check_output", "check_call"):
        monkeypatch.setattr(subprocess, name, forbidden)


def data(symbols=("A", "B"), count=305, start=0):
    panel = {s: [{"row": [start+i*H, 100., 102., 98., 100., 1000.],
                  "known_at_ms": start+(i+1)*H} for i in range(count)] for s in symbols}
    return panel


def rules(symbols=("A", "B")):
    return {s: [{"known_at_ms": 0, "valid_from_ms": 0, "valid_until_ms": 9_999_999_999_999,
        "venue": "SYNTHETIC", "quote": "USD", "eligible": True, "lot_step": ".000001",
        "quote_step": ".000001", "minimum_qty": 0, "minimum_notional_gross": 0}] for s in symbols}


def frames(panel, first=299, last=None):
    symbols = tuple(panel)
    last = len(panel[symbols[0]]) if last is None else last
    return [{"ts_ms": panel[symbols[0]][i]["row"][0],
             "open": {s: panel[s][i]["row"][1] for s in symbols},
             "close": {s: panel[s][i]["row"][4] for s in symbols}} for i in range(first, last)]


def runner(panel, *, family="ema_cross_default", permissions=None, recent_listings=None,
           incumbent=None, **updates):
    symbols = tuple(panel)
    permissions = rules(symbols) if permissions is None else permissions
    callback = bridge.FrozenSignalBridge(symbols=symbols, observations=panel,
        rules=permissions, venue="SYNTHETIC", quote="USD", snapshot_bytes=SNAPSHOT,
        family=None if incumbent else family, incumbent=incumbent, recent_listings=recent_listings)
    profile = dict(symbols=symbols, rules=permissions, venue="SYNTHETIC", quote="USD",
        interval_ms=H, initial_cash=1000, fee_bps=0, slippage_bps=0, target_contract_id="synthetic", **updates)
    return callback, profile


def context(units=None, cash=1000, marks=None):
    units = units or {"A": 0, "B": 0}
    marks = marks or dict.fromkeys(units, 100)
    return {"units": units, "cash": cash, "marked_nav": cash+sum(q*marks[s] for s,q in units.items())}


def test_simultaneous_entry_targets_use_fixed_25_denominator():
    assert bridge.event_targets(context(), {"A": "buy", "B": "buy"}, {}) == {"A": F(1,25), "B": F(1,25)}


def test_sell_proceeds_and_tiny_remaining_budget_are_shared():
    c = context({"A": F(999,100), "B": 0, "C": 0}, cash=1)
    t = bridge.event_targets(c, {"A": "hold", "B": "buy", "C": "buy"}, {"A": 100})
    assert t == {"A": F(999,1000), "B": F(1,2000), "C": F(1,2000)}
    t = bridge.event_targets(c, {"A": "sell", "B": "buy", "C": "buy"}, {"A": 100})
    assert t == {"A": 0, "B": F(1,25), "C": F(1,25)}


@pytest.mark.parametrize("actions", [{"A":"hold", "B":"hold"}, {"A":"buy", "B":"sell"},
                                      {"A":"hold", "B":"buy"}])
def test_no_event_or_zero_budget_means_no_rebalance(actions):
    assert bridge.event_targets(context({"A": 10, "B": 0}, cash=0), actions, {"A":100}) is None


def test_exhausted_account_does_not_divide_by_zero():
    assert bridge.event_targets(context(cash=0), {"A":"buy", "B":"sell"}, {}) is None
    callback, _ = runner({"A":[], "B":[]})
    c = {**context(cash=0), "history":[{"ts_ms":300*H,"open":{},"close":{}}], "close_ms":301*H}
    assert callback(c) is None
    assert set(callback.trace[-1]["readiness"].values()) == {"exhausted_account"}


@pytest.mark.parametrize("fault", ["action", "marks", "nav"])
def test_unknown_signal_or_valuation_is_incomplete(fault):
    c = context({"A": 1, "B": 0}, cash=900)
    actions, marks = {"A":"hold", "B":"buy"}, {"A":100}
    if fault == "action": actions["A"] = "unknown"
    if fault == "marks": marks = {}
    if fault == "nav": c["marked_nav"] += 1
    with pytest.raises(ledger.Incomplete):
        bridge.event_targets(c, actions, marks)


def test_real_frozen_families_receive_identical_300_completed_rows():
    panel = data(count=301)
    for family in sorted(bridge.FAMILIES):
        callback, profile = runner(panel, family=family)
        result = bridge.simulate_bridge(frames(panel), callback, **profile)
        assert result["status"] == "COMPLETE"
        for decision in callback.trace:
            i = decision["signal_bar_ts_ms"] // H
            expected = compute_signal(cfg=deepcopy(callback.config), symbol="A",
                ohlcv=[r["row"] for r in panel["A"][i-299:i+1]])
            assert decision["actions"]["A"] == expected["action"]


def test_gapped_or_late_available_input_stops_before_any_trade():
    for fault in ("gap", "late"):
        panel = data()
        if fault == "gap": del panel["A"][100]
        else: panel["A"][100]["known_at_ms"] = 400*H
        callback, profile = runner(panel)
        r = bridge.simulate_bridge(frames(data()), callback, **profile)
        assert r["status"] == "INCOMPLETE" and r["state"] is None
        assert "ohlcv" in r["reason"]


def test_documented_listing_is_not_a_gap_or_an_executable_signal():
    full = data()
    short = deepcopy(full)
    short["A"] = short["A"][290:]
    listing = {"A": {"first_bar_ms": 290*H, "known_at_ms": 290*H}}
    callback, profile = runner(short, recent_listings=listing)
    r = bridge.simulate_bridge(frames(full), callback, **profile)
    assert r["status"] == "COMPLETE"
    assert callback.trace[0]["readiness"]["A"] == "documented_recent_listing"
    assert callback.trace[0]["actions"]["A"] == "hold"
    del short["A"][2]
    callback, profile = runner(short, recent_listings=listing)
    assert bridge.simulate_bridge(frames(full), callback, **profile)["status"] == "INCOMPLETE"


def test_known_ineligible_without_candles_is_distinct_from_unknown_rules():
    panel = data()
    panel["A"] = []
    permissions = rules()
    permissions["A"][0]["eligible"] = False
    callback, profile = runner(panel, permissions=permissions)
    r = bridge.simulate_bridge(frames(data()), callback, **profile)
    assert r["status"] == "COMPLETE" and callback.trace[0]["readiness"]["A"] == "known_ineligible"
    del permissions["A"]
    callback, profile = runner(panel, permissions=permissions)
    assert bridge.simulate_bridge(frames(data()), callback, **profile)["status"] == "INCOMPLETE"


def scripted(monkeypatch, actions):
    def signal(*, cfg, symbol, ohlcv):
        return {"ok": True, "action": actions.get((ohlcv[-1][0]//H, symbol), "hold")}
    monkeypatch.setattr(bridge, "compute_signal", signal)


def test_incidental_gap_resizing_and_no_all_hold_orders(monkeypatch):
    panel = data(count=303)
    for r in panel["A"][301:]:
        r["row"][1:5] = [200., 202., 198., 200.]
    scripted(monkeypatch, {(299,"A"):"buy", (300,"B"):"buy"})
    callback, profile = runner(panel)
    r = bridge.simulate_bridge(frames(panel), callback, **profile)
    assert r["status"] == "COMPLETE"
    assert all(t["ts_ms"] in (300*H,301*H) for t in r["bridge_trades"])
    incidental = [t for t in r["bridge_trades"] if t["incidental_rebalance"]]
    assert len(incidental) == 1 and incidental[0]["symbol"] == "A" and incidental[0]["raw_action"] == "hold"
    assert r["incidental_turnover_quote"] > 0


def test_missing_entry_open_is_not_latched(monkeypatch):
    panel = data(count=303)
    scripted(monkeypatch, {(299,"A"):"buy"})
    f = frames(panel)
    del f[1]["open"]["A"]
    callback, profile = runner(panel)
    r = bridge.simulate_bridge(f, callback, **profile)
    assert r["status"] == "INCOMPLETE"  # cannot compute the next signal from a mismatched frame
    assert r["state"]["trades"] == [] and r["state"]["units"]["A"] == 0


def test_minimum_refusal_is_not_latched(monkeypatch):
    panel = data(count=303)
    scripted(monkeypatch, {(299,"A"):"buy"})
    permissions = rules()
    permissions["A"][0]["minimum_notional_gross"] = 50
    callback, profile = runner(panel, permissions=permissions)
    r = bridge.simulate_bridge(frames(panel), callback, **profile)
    assert r["status"] == "COMPLETE" and r["state"]["trades"] == []
    assert callback.trace[1]["targets"] is None


def test_full_split_equality_and_changed_past_refusal(monkeypatch):
    panel = data()
    scripted(monkeypatch, {(299,"A"):"buy", (302,"A"):"sell"})
    callback, profile = runner(panel)
    full = bridge.simulate_bridge(frames(panel), callback, **profile)
    callback, profile = runner(panel)
    left = bridge.simulate_bridge(frames(panel, last=302), callback, **profile)
    callback, profile = runner(panel)
    right = bridge.simulate_bridge(frames(panel, first=302), callback, state=left["state"], **profile)
    assert full["state"] == right["state"] and full["bridge_trades"] == right["bridge_trades"]
    changed = deepcopy(panel)
    changed["A"][100]["row"][5] += 1
    callback, profile = runner(changed)
    with pytest.raises(ValueError, match="historical_inputs"):
        bridge.simulate_bridge(frames(changed, first=302), callback, state=left["state"], **profile)


def test_future_perturbation_and_input_mutation_do_not_change_prefix(monkeypatch):
    original = data()
    changed = deepcopy(original)
    for s in changed:
        for r in changed[s][303:]:
            r["row"][1:5] = [200., 202., 198., 200.]
            r["row"][5] = 99999.
    scripted(monkeypatch, {(299,"A"):"buy"})
    a, profile = runner(original)
    b, _ = runner(changed)
    original["A"][0]["row"][5] = -1
    left = bridge.simulate_bridge(frames(data(), last=303), a, **profile)
    right = bridge.simulate_bridge(frames(changed, last=303), b, **profile)
    assert left["state"] == right["state"]


def test_universe25_has_one_shared_wallet(monkeypatch):
    symbols = tuple("SYN-"+str(i) for i in range(25))
    panel = data(symbols, count=301)
    scripted(monkeypatch, {(299,s):"buy" for s in symbols})
    callback, profile = runner(panel)
    r = bridge.simulate_bridge(frames(panel), callback, **profile)
    assert r["status"] == "COMPLETE" and r["state"]["cash"] == 0
    assert len(r["state"]["trades"]) == 25 and r["marked_nav"] == 1000


def test_frozen_configuration_and_snapshot_cannot_be_silently_replaced():
    panel = data()
    callback, profile = runner(panel)
    callback.config["strategy"]["ema_fast"] = 1
    with pytest.raises(ValueError, match="config_changed"):
        bridge.simulate_bridge(frames(panel), callback, **profile)
    with pytest.raises(ValueError, match="snapshot_mismatch"):
        bridge.FrozenSignalBridge(symbols=("A",), observations=panel, rules=rules(),
            venue="SYNTHETIC", quote="USD", snapshot_bytes=b"{}", family="ema_cross_default")


@pytest.mark.parametrize("family", sorted(bridge.FAMILIES))
def test_actual_frozen_family_future_prices_and_volume_do_not_change_prefix(family):
    panel = data()
    changed = deepcopy(panel)
    for symbol in changed:
        for r in changed[symbol][303:]:
            r["row"][1:5] = [1000.,1002.,998.,1000.]
            r["row"][5] = 1.
    a, profile = runner(panel, family=family)
    b, _ = runner(changed, family=family)
    assert bridge.simulate_bridge(frames(panel,last=303),a,**profile)["state"] == \
        bridge.simulate_bridge(frames(changed,last=303),b,**profile)["state"]


def test_changed_family_refuses_carry_but_future_rule_addition_is_allowed(monkeypatch):
    panel = data()
    scripted(monkeypatch, {(299,"A"):"buy"})
    callback, profile = runner(panel)
    left = bridge.simulate_bridge(frames(panel,last=302), callback, **profile)
    callback, profile = runner(panel, family="mean_reversion_default")
    with pytest.raises(ValueError, match="historical_inputs"):
        bridge.simulate_bridge(frames(panel,first=302), callback, state=left["state"], **profile)
    updated = rules()
    updated["A"].append({**updated["A"][0], "known_at_ms":303*H,"valid_from_ms":303*H,"lot_step":".001"})
    callback, profile = runner(panel, permissions=updated)
    r = bridge.simulate_bridge(frames(panel,first=302), callback, state=left["state"], **profile)
    assert r["status"] == "COMPLETE"
    assert r["state"]["trades"][:1] == left["state"]["trades"]


def test_signal_cannot_mutate_copied_panel_or_configuration(monkeypatch):
    panel = data()
    callback, profile = runner(panel)
    original = deepcopy(callback.panel.rows)
    def mutating(*, cfg, symbol, ohlcv):
        cfg["strategy"]["ema_fast"] = 1
        ohlcv[-1][5] = -99
        return {"ok": True,"action":"hold"}
    monkeypatch.setattr(bridge,"compute_signal",mutating)
    assert bridge.simulate_bridge(frames(panel),callback,**profile)["status"] == "COMPLETE"
    assert callback.panel.rows == original and callback.config["strategy"]["ema_fast"] == 12


@pytest.mark.parametrize("result", [{"ok":False,"action":"hold"}, {"ok":True,"action":"unknown"},
    {"ok":True,"action":"buy","ind":{"bad":float("inf")}}, ZeroDivisionError()])
def test_invalid_signal_or_arithmetic_failure_is_incomplete_not_hold(monkeypatch,result):
    def invalid(**kwargs):
        if isinstance(result,Exception):
            raise result
        return result
    monkeypatch.setattr(bridge,"compute_signal",invalid)
    callback,profile = runner(data())
    report = bridge.simulate_bridge(frames(data()),callback,**profile)
    assert report["status"] == "INCOMPLETE" and report["state"] is None
    assert "signal" in report["reason"] and callback.trace == []


def test_external_work_guard_is_not_swallowed_as_signal_failure(monkeypatch):
    def forbidden(**kwargs):
        raise AssertionError("guarded synthetic failure")
    monkeypatch.setattr(bridge,"compute_signal",forbidden)
    callback,profile = runner(data())
    with pytest.raises(AssertionError,match="guarded synthetic failure"):
        bridge.simulate_bridge(frames(data()),callback,**profile)


def test_frame_and_valuation_contracts_must_match():
    panel = data()
    callback,profile = runner(panel)
    f = frames(panel)
    f[0]["close"]["A"] = 99.
    assert bridge.simulate_bridge(f,callback,**profile)["status"] == "INCOMPLETE"
    with pytest.raises(ValueError,match="valuation_metadata"):
        bridge.simulate_bridge(frames(panel),callback,valuation_marks={"A":[]},**profile)


def test_incumbent_rejects_zero_volatility_and_missing_daily_hour():
    a = int(datetime(2026,1,5,tzinfo=timezone.utc).timestamp()*1000)
    panel = data(count=61*24+1,start=a-61*bridge.DAY)
    for symbol in panel:
        for i,r in enumerate(panel[symbol]):
            price = float(2**(i//24+1))
            r["row"][1:5] = [price,price,price,price]
    f = frames(panel,first=61*24-1)
    c = {**context(),"history":[f[0]],"close_ms":a}
    callback,_ = runner(panel,incumbent=("A","B"))
    with pytest.raises(ledger.Incomplete,match="volatility"):
        callback(c)
    del panel["A"][100]
    callback,_ = runner(panel,incumbent=("A","B"))
    with pytest.raises(ledger.Incomplete,match="ohlcv"):
        callback(c)


def test_incumbent_sunday_utc_timing_and_frozen_target_parity():
    a = int(datetime(2026,1,5,tzinfo=timezone.utc).timestamp()*1000)
    panel = data(count=61*24+2, start=a-61*bridge.DAY)
    for s in panel:
        for i, record in enumerate(panel[s]):
            p = 100 + i*.01 + math.sin(i/24)
            record["row"][1:5] = [p, p+2, p-2, p]
    callback, profile = runner(panel, incumbent=("A","B"))
    f = frames(panel, first=61*24-1)
    c = {**context(), "history": [f[0]], "close_ms": a}
    target = callback(c)
    daily = [panel["A"][i]["row"][4] for i in range(23,61*24,24)]
    dr = [0.] + [daily[i]/daily[i-1]-1 for i in range(1,len(daily))]
    vol = statistics.pstdev(dr[-30:])*math.sqrt(365)
    source = ast.parse((ROOT/"docs/research/btc_eth_stress_test_20261009/stress_btc_eth.py").read_text())
    function = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == "target")
    ns = {"P": {s:daily for s in ("A","B")}, "VOL": {s:[vol]*61 for s in ("A","B")}}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "frozen_target_only", "exec"), ns)
    expected = ns["target"]("rule",60,28,.5,("A","B"))
    assert target == {s:ledger.number(w) for s,w in expected.items()}
    assert callback({**c, "history":[f[1]], "close_ms":a+H}) is None
    assert callback.trace[0]["held_without_sell"] == []


@pytest.mark.parametrize("fault", ["open", "close", "missing_panel_hour"])
def test_incumbent_checks_non_rebalance_execution_and_marking_frames(fault):
    a = int(datetime(2026,1,5,tzinfo=timezone.utc).timestamp()*1000)
    panel = data(count=61*24+3,start=a-61*bridge.DAY)
    for symbol in panel:
        for i,r in enumerate(panel[symbol]):
            p = 100+i*.01+math.sin(i/24)
            r["row"][1:5] = [p,p+2,p-2,p]
    f = frames(panel,first=61*24-1)
    callback,profile = runner(panel,incumbent=("A","B"))
    baseline = bridge.simulate_bridge(f,callback,**profile)
    assert baseline["status"] == "COMPLETE"
    assert any(t["symbol"] == "A" and t["ts_ms"] == a for t in baseline["state"]["trades"])
    if fault == "missing_panel_hour":
        del panel["A"][61*24]
    else:
        f[1][fault]["A"] = 1. if fault == "open" else 1000.
    callback,profile = runner(panel,incumbent=("A","B"))
    invalid = bridge.simulate_bridge(f,callback,**profile)
    assert invalid["status"] == "INCOMPLETE"
    assert invalid["net_profit"] is None and invalid["marked_nav"] is None
    assert invalid["state"]["valid"] is False
    assert invalid["reason"].startswith(("signal_execution_frame_mismatch:","missing_or_unavailable_ohlcv:"))
