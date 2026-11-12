"""Bounded independent source-only candle guard probes."""
import difflib
import hashlib
import json
from datetime import timedelta
from pathlib import Path
import subprocess

import pytest

from tests.test_hourly_candle_quality import market, write


ARTIFACT = Path(__file__).resolve().parents[1]
ROOT = ARTIFACT.parents[2]


def test_nine_file_seal():
    for name, digest in {
        "stage.diff": "f6069d5edcdb67c37e9eabe16f2e6ef0b3d7bfb4503ec86704d67b6c4eecf07c",
        "hashes.json": "82270272b22a9f7b66ee6d19d527fbf8046b894ae4ba58e6ec5b5f0a9fab8a83",
    }.items():
        assert hashlib.sha256((ARTIFACT / name).read_bytes()).hexdigest() == digest
    manifest = json.loads((ARTIFACT / "hashes.json").read_text())
    existing = ("services/execution/paper_engine.py", "services/execution/strategy_runner.py",
                "services/strategies/signal_input_capture.py", "services/market_data/local_data_reader.py",
                "storage/paper_trading_sqlite.py")
    head = ("tests/test_ohlcv_snapshot_provenance.py",)
    new = ("services/market_data/hourly_candle_quality.py", "tests/test_hourly_candle_quality.py",
           "tests/test_paper_candle_fill_boundary.py")
    assert set(manifest["before"]) == set(manifest["current"]) == set(existing + head + new)
    chunks = []
    for name in existing + head + new:
        old = ((ARTIFACT / "before" / name).read_bytes() if name in existing else
               subprocess.check_output(["/usr/bin/git", "show", "HEAD:" + name], cwd=ROOT)
               if name in head else b"")
        current = (ROOT / name).read_bytes()
        assert hashlib.sha256(old).hexdigest() == manifest["before"][name]
        assert hashlib.sha256(current).hexdigest() == manifest["current"][name]
        chunks.extend(difflib.unified_diff(old.decode().splitlines(keepends=True),
            current.decode().splitlines(keepends=True), fromfile="before/" + name, tofile="after/" + name))
    assert "".join(chunks).encode() == (ARTIFACT / "stage.diff").read_bytes()


def test_new_diagnostic_write_crossing_ttl_must_not_fill(market, monkeypatch):
    write(market)
    created = market.now[0]
    result = market.eng.submit_order(client_order_id="review-delayed-diagnostic", venue="coinbase",
        symbol="ADA/USD", side="buy", order_type="market", qty=1)
    assert result["ok"]
    market.now[0] = created + timedelta(seconds=119)
    original = market.eng.db._set_state_conn
    diagnostic_calls = []

    def delayed_write(con, key, value):
        if key.startswith("paper_candle_check:"):
            diagnostic_calls.append(key)
            market.now[0] = created + timedelta(seconds=121)
        return original(con, key, value)

    monkeypatch.setattr(market.eng.db, "_set_state_conn", delayed_write)
    evaluated = market.eng.evaluate_open_orders()
    canonical = market.eng.db.get_order_by_client_id("review-delayed-diagnostic")
    observed = {"now": market.clock(), "result": evaluated, "order": canonical,
                "fills": market.eng.db.list_fills(), "cash": market.eng.cash_quote()}
    assert diagnostic_calls
    assert evaluated["filled"] == 0, observed
    assert canonical["status"] == "expired", observed
    assert market.eng.db.list_fills() == [] and market.eng.cash_quote() == 1000


@pytest.mark.parametrize("binding", ["runner_alias", "module_constant"])
def test_new_assessor_bindings_are_in_loaded_identity(monkeypatch, binding):
    from services.execution import strategy_runner
    from services.market_data import hourly_candle_quality
    from services.strategies import signal_input_capture
    before = signal_input_capture._runner_code_identity()
    if binding == "runner_alias":
        monkeypatch.setattr(strategy_runner, "assess_hourly_candles", lambda *a, **kw: {"ok": True})
    else:
        monkeypatch.setattr(hourly_candle_quality, "HOUR_MS", 1)
    assert signal_input_capture._runner_code_identity() != before


def test_colliding_filename_cannot_substitute_symbol_identity(market):
    from services.market_data.hourly_candle_quality import check_cached_hourly_candles
    from services.market_data.local_data_reader import write_local_ohlcv_snapshot
    path = write(market)
    rows = json.loads(path.read_text())["candles"]
    collision = write_local_ohlcv_snapshot("coinbase", "ADA_USD", rows, timeframe="1h", source="public_ohlcv")
    assert collision == path
    result = check_cached_hourly_candles("coinbase", "ADA/USD", clock=market.clock, data_root=market.root)
    assert result["ok"] is False and result["reason"] == "cache_identity_or_source_unverified"
