from __future__ import annotations

import asyncio
import importlib
import json
import sqlite3
from pathlib import Path


def _reload_state_modules(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    return app_paths


def test_market_data_store_reads_sqlite_latest(tmp_path):
    from storage.market_store_sqlite import MarketStore
    from storage.market_data_store_sqlite import SQLiteMarketDataStore

    db = tmp_path / "market.sqlite"
    market = MarketStore(path=db)
    market.upsert_ticker(ts_ms=1000, exchange="coinbase", symbol="BTC/USD", bid=99.0, ask=101.0, last=100.0)
    market.upsert_ticker(ts_ms=2000, exchange="coinbase", symbol="BTC/USD", bid=109.0, ask=111.0, last=110.0)
    market.upsert_ticker(ts_ms=1500, exchange="coinbase", symbol="ETH/USD", bid=49.0, ask=51.0, last=50.0)

    rows = SQLiteMarketDataStore(path=db).get_latest_sync()
    assert len(rows) == 2
    by_symbol = {r["symbol"]: r for r in rows}
    assert by_symbol["BTC/USD"]["ts_ms"] == 2000
    assert by_symbol["BTC/USD"]["venue"] == "coinbase"
    assert by_symbol["ETH/USD"]["last"] == 50.0


def test_market_data_store_falls_back_to_snapshot(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import storage.market_data_store_sqlite as mds

    importlib.reload(mds)
    mds.SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ticks": [{"symbol": "BTC/USD", "venue": "coinbase", "last": 123.0}]}
    mds.SNAPSHOT_FILE.write_text(json.dumps(payload), encoding="utf-8")

    rows = mds.SQLiteMarketDataStore(path=tmp_path / "missing.sqlite").get_latest_sync()
    assert rows == payload["ticks"]


def test_run_price_feeds_run_once_and_main_loop(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import services.market_data.run_price_feeds as rpf

    importlib.reload(rpf)

    calls: dict[str, int] = {"build": 0, "fetch": 0, "run_once": 0}

    def _fake_build(symbols, include_symbols=True, extra_pairs=None):
        calls["build"] += 1
        return [f"{s}:PAIR" for s in symbols]

    async def _fake_fetch(venue, pairs):
        calls["fetch"] += 1
        return {"ok": True, "venue": venue, "pairs": pairs, "ticks": [{"symbol": "BTC/USD", "last": 100.0}]}

    monkeypatch.setattr(rpf, "build_required_pairs", _fake_build)
    monkeypatch.setattr(rpf, "fetch_tickers_once", _fake_fetch)

    cfg = tmp_path / "market_data.yaml"
    cfg.write_text("venue: coinbase\nsymbols: [BTC/USD]\ninterval_sec: 0.01\n", encoding="utf-8")
    out = asyncio.run(rpf.run_once(cfg))
    assert out["ok"] is True
    assert calls["build"] == 1
    assert calls["fetch"] == 1
    snap = json.loads(rpf.SNAPSHOT_FILE.read_text(encoding="utf-8"))
    assert snap["ticks"][0]["symbol"] == "BTC/USD"
    assert "ts" in snap

    async def _fake_run_once(path):
        calls["run_once"] += 1
        return {"ok": True}

    async def _fake_sleep(_sec):
        return None

    monkeypatch.setattr(rpf, "run_once", _fake_run_once)
    monkeypatch.setattr(rpf.asyncio, "sleep", _fake_sleep)
    asyncio.run(rpf.main_async(cfg, max_loops=3))
    assert calls["run_once"] == 3


def test_live_start_gate_blocks_on_high_latency(tmp_path):
    import services.diagnostics.live_start_gate as gate

    db = tmp_path / "ws.sqlite"
    con = sqlite3.connect(str(db))
    con.execute("CREATE TABLE market_ws_latency(ts_ms INTEGER NOT NULL, value_ms REAL)")
    con.execute("INSERT INTO market_ws_latency(ts_ms, value_ms) VALUES(?,?)", (999_999_999_999, 10_000.0))
    con.commit()
    con.close()

    out = gate.check_ws_gate(
        {"circuit_breaker": {"latency_db_path": str(db), "ws_warn_ms": 100.0, "ws_block_ms": 500.0, "ws_lookback_sec": 999999999}}
    )
    assert out.ok is False
    assert out.status == "BLOCK"
    assert "ws_latency_block" in out.reasons

