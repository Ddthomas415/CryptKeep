import copy
import json
import sqlite3

import pytest

from scripts.research import run_coinbase_confirmation as runner
from services.backtest.next_open_research import run_frozen_segment


def contract():
    plan = {"experiment_id": "synthetic", "symbols": ["BTC/USDT"],
            "strategies": ["arm"], "controls": ["cash", "same_entry_notional_buy_and_hold"],
            "archive_start_utc": "1970-01-01T00:00:00Z",
            "evaluation_start_utc": "1970-01-01T02:00:00Z",
            "descriptive_checkpoint_utc": "1970-01-01T04:00:00Z",
            "evaluation_end_exclusive_utc": "1970-01-01T06:00:00Z",
            "warmup_bars": 2, "initial_cash_per_independent_arm": 1000,
            "entry_notional_quote": 100, "primary_taker_fee_bps_per_side": 50,
            "primary_slippage_bps_per_side": 5, "slippage_stress_bps_per_side": [10, 20]}
    return plan, {"strategies": {"arm": {"name": "synthetic"}}}, {"plan_sha256": "plan", "runner_sha256": "runner"}


def files(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "load_contract", lambda _: contract())
    path = tmp_path/"archive.sqlite"
    with sqlite3.connect(path) as con:
        con.execute("CREATE TABLE market_ohlcv(exchange,symbol,timeframe,ts_ms,o,h,l,cl,v)")
        con.executemany("INSERT INTO market_ohlcv VALUES('coinbase','BTC/USDT','1h',?,?,?,?,?,?)",
                        [[i*runner.HOUR,100+10*i,200,90,100+10*i,1] for i in range(6)])
    registration = tmp_path/"registration.json"
    registration.write_text(json.dumps(runner.register("plan", now_ms=runner.HOUR)))
    def freeze(phase, previous=None):
        result = runner.run("plan", path, phase=phase, mode="freeze", now_ms=6*runner.HOUR,
                            registration_path=registration, previous_manifest_path=previous)
        output = tmp_path/(phase+".json")
        output.write_text(json.dumps(result))
        return output
    warmup = freeze("warmup")
    checkpoint = freeze("checkpoint", warmup)
    final = freeze("final", checkpoint)
    return path, registration, warmup, checkpoint, final


def test_actual_contract_and_references_load():
    plan, _, _ = runner.load_contract(runner.ROOT/"research/coinbase_confirmation_v1/plan.json")
    assert plan["primary_taker_fee_bps_per_side"] == 50


def test_usd_contract_and_no_mixed_quote_basket(tmp_path):
    path = runner.ROOT/"research/coinbase_confirmation_usd_v1/plan.json"
    plan, _, _ = runner.load_contract(path)
    assert plan["quote_currency"] == "USD"
    assert all(symbol.endswith("/USD") for symbol in plan["symbols"])
    for symbols, quote in [(plan["symbols"][:-1], "USD"),
                           (["BTC/USDT"] + plan["symbols"][1:], "USD"),
                           (plan["symbols"], "USDT")]:
        invalid = dict(plan, symbols=symbols, quote_currency=quote)
        candidate = tmp_path/"invalid.json"
        candidate.write_text(json.dumps(invalid))
        with pytest.raises(ValueError, match="unsupported_market"):
            runner.load_contract(candidate)


def test_preregistration_deadline_and_identity(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "load_contract", lambda _: contract())
    with pytest.raises(ValueError, match="deadline"):
        runner.register("plan", now_ms=2*runner.HOUR)
    registration = tmp_path/"registration.json"
    record = runner.register("plan", now_ms=runner.HOUR)
    registration.write_text(json.dumps(record))
    plan, _, identity = contract()
    assert runner.check_registration(registration, plan, identity, 2*runner.HOUR)
    record["identity"]["runner_sha256"] = "changed"
    registration.write_text(json.dumps(record))
    with pytest.raises(ValueError, match="registration"):
        runner.check_registration(registration, plan, identity, 2*runner.HOUR)


def test_future_and_warmup_scoring_refused_before_read(monkeypatch):
    monkeypatch.setattr(runner, "load_contract", lambda _: contract())
    monkeypatch.setattr(runner, "read_rows", lambda *a, **k: pytest.fail("archive read"))
    with pytest.raises(ValueError, match="not_completed"):
        runner.run("plan", "archive", phase="final", mode="simulate", now_ms=runner.HOUR)
    with pytest.raises(ValueError, match="cannot_be_scored"):
        runner.run("plan", "archive", phase="warmup", mode="simulate", now_ms=3*runner.HOUR)


def test_missing_archive_is_incomplete_not_fetch(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "load_contract", lambda _: contract())
    result = runner.run("plan", tmp_path/"missing", now_ms=runner.HOUR)
    assert not result["all_markets_complete"] and not result["full_phase_completed"]
    assert result["requested_end_ms"] == runner.HOUR


def test_carry_costs_terminal_and_natural_cycle_counts(monkeypatch, tmp_path):
    archive, registration, _, checkpoint, final = files(tmp_path, monkeypatch)
    monkeypatch.setattr(runner, "run_frozen_segment", lambda rows, **kw: run_frozen_segment(
        rows, signal_fn=lambda **kwargs: {"ok": True, "action": "buy"}, **kw))
    before = archive.read_bytes()
    results = []
    for phase, manifest in [("checkpoint", checkpoint), ("final", final)]:
        results.append(runner.run("plan", archive, phase=phase, mode="simulate", now_ms=6*runner.HOUR,
                                  registration_path=registration, manifest_path=manifest))
    early = results[0]["markets"]["BTC/USDT"]["results"]["arm"]["5"]
    late = results[1]["markets"]["BTC/USDT"]["results"]["arm"]["5"]
    assert early["ending_position_qty"] > 0 and not early["terminal_liquidation"]
    assert late["equity"][:2] == early["equity"]
    assert late["phase_starting_equity_quote"] == early["terminal_equity_quote"]
    assert late["natural_closed_cycles"] == 0 and late["closed_cycles"] == 1
    assert late["ending_position_qty"] == 0 and late["terminal_equity_adjustment_quote"] < 0
    buy, sell = late["trades"]
    assert buy["price"] == pytest.approx(120*1.0005)
    assert buy["fee"] == pytest.approx(0.5)
    assert sell["price"] == pytest.approx(150*.9995)
    assert sell["fee"] == pytest.approx(sell["qty"]*sell["price"]*.005)
    assert archive.read_bytes() == before
    cash = results[1]["markets"]["BTC/USDT"]["results"]["cash"]["5"]
    assert cash["net_quote_profit"] == 0


def test_changed_prefix_and_missing_ancestry_refused(monkeypatch, tmp_path):
    archive, registration, warmup, checkpoint, final = files(tmp_path, monkeypatch)
    manifest = json.loads(final.read_text())
    del manifest["prefixes"]["BTC/USDT"]["warmup"]
    final.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="missing_previous"):
        runner.run("plan", archive, phase="final", mode="simulate", now_ms=6*runner.HOUR,
                   registration_path=registration, manifest_path=final)
    with sqlite3.connect(archive) as con:
        con.execute("UPDATE market_ohlcv SET cl=101 WHERE ts_ms=0")
    with pytest.raises(ValueError, match="prefix_changed"):
        runner.run("plan", archive, phase="checkpoint", mode="freeze", now_ms=6*runner.HOUR,
                   registration_path=registration, previous_manifest_path=warmup)


def test_final_source_candles_and_wrong_venue_cannot_substitute(monkeypatch, tmp_path):
    archive, registration, _, _, final = files(tmp_path, monkeypatch)
    with sqlite3.connect(archive) as con:
        con.execute("UPDATE market_ohlcv SET exchange='okx'")
    result = runner.run("plan", archive, phase="final", mode="simulate", now_ms=6*runner.HOUR,
                        registration_path=registration, manifest_path=final)
    assert not result["all_markets_complete"]
    assert "results" not in result["markets"]["BTC/USDT"]


def test_all_markets_validated_before_any_signal(monkeypatch, tmp_path):
    archive, registration, _, _, final = files(tmp_path, monkeypatch)
    plan, snapshot, identity = contract()
    plan["symbols"].append("ETH/USDT")
    monkeypatch.setattr(runner, "load_contract", lambda _: (plan, snapshot, identity))
    monkeypatch.setattr(runner, "run_frozen_segment", lambda *a, **k: pytest.fail("signal evaluated"))
    result = runner.run("plan", archive, phase="final", mode="simulate", now_ms=6*runner.HOUR,
                        registration_path=registration, manifest_path=final)
    assert not result["all_markets_complete"]
