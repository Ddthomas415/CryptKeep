"""Offline multi-market packaging proof; no historical strategy results."""
import json
import sqlite3

import pytest

from scripts.research import run_multisymbol_baseline as runner
from services.backtest.research_prefix_freeze import build_manifest
from tests.test_multisymbol_archive_runner import archive, tiny_contract


def two_market_contract():
    plan, snapshot, digest = tiny_contract()
    plan["symbols"] = ["BTC/USDT", "ETH/USDT"]
    plan["strategies"] = []
    snapshot["strategies"] = {}
    return plan, snapshot, digest


def test_two_market_frozen_archive_and_carry_forward(monkeypatch, tmp_path):
    """Every symbol has its own cash account, as the existing contract specifies."""
    path = archive(tmp_path)
    with sqlite3.connect(path) as con:
        con.execute(
            "INSERT INTO market_ohlcv "
            "SELECT exchange,'ETH/USDT',timeframe,ts_ms,o*2,h*2,l*2,cl*2,v "
            "FROM market_ohlcv WHERE symbol='BTC/USDT'"
        )
    before = path.read_bytes()
    monkeypatch.setattr(runner, "load_contract", two_market_contract)
    plan, snapshot, digest = two_market_contract()
    manifest = build_manifest(
        plan=plan, plan_sha256=snapshot["plan_sha256"], snapshot_sha256=digest,
        read_prefix=lambda symbol, end: runner.read_rows(
            path, venue="okx", symbol=symbol, start_ms=0,
            end_ms=runner.utc_ms(end),
        ),
    )
    manifest_path = tmp_path / "prefixes.json"
    manifest_path.write_text(json.dumps(manifest))
    preflight = runner.run_phase(path)
    assert preflight["all_markets_complete"]
    assert set(preflight["markets"]) == set(plan["symbols"])
    assert all("results" not in row for row in preflight["markets"].values())

    for phase, starting, change in (
        ("discovery", 1000.0, 0.0),
        ("validation", 1000.0, 50.0),
        ("final", 1050.0, 50.0),
    ):
        result = runner.run_phase(
            path, phase=phase, simulate=True, manifest_path=manifest_path,
        )
        assert result["all_markets_complete"], result["markets"]
        for symbol in plan["symbols"]:
            held = result["markets"][symbol]["results"][
                "same_entry_notional_buy_and_hold"
            ]["0"]
            assert held["phase_starting_equity_quote"] == pytest.approx(starting)
            assert held["phase_net_quote_profit"] == pytest.approx(change)
            assert held["terminal_liquidation"] == (phase == "final")
            assert len([t for t in held["trades"] if t["side"] == "buy"]) == 1
    assert path.read_bytes() == before

    with sqlite3.connect(path) as con:
        con.execute("DELETE FROM market_ohlcv WHERE symbol='ETH/USDT' AND ts_ms=0")
    incomplete = runner.run_phase(path)
    assert not incomplete["all_markets_complete"]
    assert incomplete["markets"]["ETH/USDT"]["status"] == "INCOMPLETE"
    assert incomplete["markets"]["BTC/USDT"]["status"] == "ARCHIVE_VERIFIED"
