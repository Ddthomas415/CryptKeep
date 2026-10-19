from datetime import datetime, timezone
import hashlib
import json
import sqlite3

import pytest

from scripts.research import run_multisymbol_baseline as runner
from services.backtest.next_open_research import run_frozen_segment
from services.backtest.research_prefix_freeze import build_manifest


def timestamp(hour):
    return datetime.fromtimestamp(hour*3600, timezone.utc).isoformat()


def tiny_contract():
    plan = {"experiment_id":"synthetic", "venue":"okx", "symbols":["BTC/USDT"],
            "strategies":["ema_cross_default"], "controls":["cash","same_entry_notional_buy_and_hold"],
            "archive_start_utc":timestamp(0), "evaluation_start_utc":timestamp(1),
            "discovery_end_exclusive_utc":timestamp(3), "validation_end_exclusive_utc":timestamp(5),
            "evaluation_end_exclusive_utc":timestamp(7), "warmup_bars":1,
            "initial_cash_per_independent_arm":1000, "entry_notional_quote":100,
            "fee_bps_per_side_scenarios":[0], "slippage_bps_per_side":0,
            "split_account_policy":"carry_cash_and_positions_forward"}
    snapshot = {"plan_sha256":"synthetic", "strategies":{"ema_cross_default":{"name":"ema_cross"}}}
    return plan, snapshot, "synthetic-snapshot"


def archive(tmp_path, rows=None):
    path = tmp_path/"archive.sqlite"
    rows = rows if rows is not None else [[i*runner.HOUR,100.,200.,90.,100. if i<3 else 150. if i<5 else 200.,1.] for i in range(7)]
    with sqlite3.connect(path) as con:
        con.execute("CREATE TABLE market_ohlcv(exchange TEXT,symbol TEXT,timeframe TEXT,ts_ms INTEGER,o REAL,h REAL,l REAL,cl REAL,v REAL)")
        con.executemany("INSERT INTO market_ohlcv VALUES('okx','BTC/USDT','1h',?,?,?,?,?,?)", rows)
    return path


def test_registered_snapshot_matches_current_selected_sources():
    plan, snapshot, digest = runner.load_contract()
    assert len(snapshot["strategies"]) == 3
    assert plan["split_account_policy"] == "carry_cash_and_positions_forward"
    assert len(digest) == 64


def test_source_drift_refused(monkeypatch, tmp_path):
    contract = tmp_path/"contract"
    contract.mkdir()
    (contract/"plan.json").write_text('{"strategies":["arm"]}')
    snapshot = {"strategies":{"arm":{}}, "plan_sha256":hashlib.sha256((contract/"plan.json").read_bytes()).hexdigest(),
                "selected_source_sha256":{"source.py":"a"*64}}
    (contract/"strategies.snapshot.json").write_text(json.dumps(snapshot))
    (tmp_path/"source.py").write_text("changed")
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "CONTRACT", contract)
    with pytest.raises(ValueError, match="source_changed"):
        runner.load_contract()
    snapshot["plan_sha256"] = "b"*64
    (contract/"strategies.snapshot.json").write_text(json.dumps(snapshot))
    with pytest.raises(ValueError, match="plan_changed"):
        runner.load_contract()


def test_read_only_exact_market_and_dates(tmp_path):
    path = archive(tmp_path)
    before = path.read_bytes()
    rows = runner.read_rows(path, venue="okx", symbol="BTC/USDT", start_ms=0, end_ms=3*runner.HOUR)
    assert len(rows) == 3 and rows[-1][0] == 2*runner.HOUR
    assert path.read_bytes() == before
    with pytest.raises(ValueError, match="archive_incomplete"):
        runner.read_rows(path, venue="coinbase", symbol="BTC/USDT", start_ms=0, end_ms=3*runner.HOUR)
    with pytest.raises(ValueError, match="archive_incomplete"):
        runner.read_rows(path, venue="okx", symbol="ETH/USDT", start_ms=0, end_ms=3*runner.HOUR)


def test_preflight_does_not_evaluate_signals(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "load_contract", tiny_contract)
    monkeypatch.setattr(runner, "run_frozen_segment", lambda *a, **kw: pytest.fail("preflight ran signals"))
    report = runner.run_phase(archive(tmp_path), phase="discovery")
    assert report["all_markets_complete"]
    assert report["markets"]["BTC/USDT"]["bars"] == 3
    assert "results" not in report["markets"]["BTC/USDT"]


def test_incomplete_symbol_remains_reported(monkeypatch, tmp_path):
    plan, snapshot, digest = tiny_contract()
    plan["symbols"].append("ETH/USDT")
    monkeypatch.setattr(runner, "load_contract", lambda:(plan,snapshot,digest))
    report = runner.run_phase(archive(tmp_path))
    assert not report["all_markets_complete"]
    assert report["markets"]["ETH/USDT"]["status"] == "INCOMPLETE"


def test_continuous_cash_and_position_across_splits(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "load_contract", tiny_contract)
    def actual_core(rows, **kwargs):
        return run_frozen_segment(rows, signal_fn=lambda **kw:{"ok":True,"action":"buy"}, **kwargs)
    monkeypatch.setattr(runner, "run_frozen_segment", actual_core)
    path = archive(tmp_path)
    plan, snapshot, digest = tiny_contract()
    manifest = build_manifest(plan=plan, plan_sha256=snapshot["plan_sha256"], snapshot_sha256=digest,
        read_prefix=lambda symbol,end:runner.read_rows(path, venue="okx", symbol=symbol,
                                                      start_ms=0,end_ms=runner.utc_ms(end)))
    manifest_path = tmp_path/"manifest.json"
    manifest_path.write_text(json.dumps(manifest))
    discovery = runner.run_phase(path, phase="discovery", simulate=True, manifest_path=manifest_path)
    validation = runner.run_phase(path, phase="validation", simulate=True, manifest_path=manifest_path)
    final = runner.run_phase(path, phase="final", simulate=True, manifest_path=manifest_path)
    def result(report):
        return report["markets"]["BTC/USDT"]["results"]["ema_cross_default"]["0"]
    assert not result(discovery)["terminal_liquidation"]
    assert result(discovery)["ending_position_qty"] == 1.
    assert result(validation)["phase_starting_equity_quote"] == 1000.
    assert result(validation)["phase_net_quote_profit"] == 50.
    assert result(validation)["final_cash_quote"] == 900.
    assert result(final)["phase_starting_equity_quote"] == 1050.
    assert result(final)["phase_net_quote_profit"] == 50.
    assert result(final)["terminal_liquidation"]
    assert result(final)["ending_position_qty"] == 0.
    assert len([t for t in result(final)["trades"] if t["side"]=="buy"]) == 1


def test_missing_or_changed_prefix_blocks_simulation(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, "load_contract", tiny_contract)
    path = archive(tmp_path)
    with pytest.raises(ValueError, match="manifest_required"):
        runner.run_phase(path, simulate=True)
    plan, snapshot, digest = tiny_contract()
    manifest = build_manifest(plan=plan, plan_sha256=snapshot["plan_sha256"], snapshot_sha256=digest,
        read_prefix=lambda symbol,end:runner.read_rows(path,venue="okx",symbol=symbol,start_ms=0,end_ms=runner.utc_ms(end)))
    target = tmp_path/"manifest.json"
    target.write_text(json.dumps(manifest))
    with sqlite3.connect(path) as con:
        con.execute("UPDATE market_ohlcv SET v=2 WHERE ts_ms=0")
    monkeypatch.setattr(runner,"run_frozen_segment",lambda *a,**kw:pytest.fail("changed prefix ran signals"))
    report = runner.run_phase(path, simulate=True, manifest_path=target)
    assert report["markets"]["BTC/USDT"]["reason"] == "dataset_prefix_changed_after_freeze"


def test_inconsistent_prefixes_cannot_be_frozen():
    plan, snapshot, digest = tiny_contract()
    def changing(symbol,end):
        count = runner.utc_ms(end)//runner.HOUR
        rows = [[i*runner.HOUR,100.,200.,90.,100.,1.] for i in range(count)]
        if count > 3:
            rows[0][-1] = 2.
        return rows
    with pytest.raises(ValueError, match="changed_during_freeze"):
        build_manifest(plan=plan, plan_sha256=snapshot["plan_sha256"],
                       snapshot_sha256=digest,read_prefix=changing)
