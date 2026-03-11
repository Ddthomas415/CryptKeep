from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite


def _seed_live_intent_db(path: Path) -> None:
    con = sqlite3.connect(str(path))
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS live_trade_intents(
          intent_id TEXT PRIMARY KEY,
          status TEXT
        )
        """
    )
    rows = [
        ("i-1", "submitted"),
        ("i-2", "rejected"),
        ("i-3", "filled"),
        ("i-4", "submitted"),
    ]
    con.executemany("INSERT OR REPLACE INTO live_trade_intents(intent_id, status) VALUES(?,?)", rows)
    con.commit()
    con.close()


def _seed_ws_status_db(path: Path) -> None:
    con = sqlite3.connect(str(path))
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS ws_status_events(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          lag_ms REAL
        )
        """
    )
    con.executemany("INSERT INTO ws_status_events(lag_ms) VALUES(?)", [(80.0,), (120.0,), (300.0,)])
    con.commit()
    con.close()


def _seed_ws_latency_db(path: Path) -> None:
    con = sqlite3.connect(str(path))
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS market_ws_latency(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          category TEXT,
          name TEXT,
          value_ms REAL
        )
        """
    )
    con.executemany(
        "INSERT INTO market_ws_latency(category, name, value_ms) VALUES(?,?,?)",
        [
            ("execution", "submit_to_ack_ms", 110.0),
            ("execution", "submit_to_ack_ms", 250.0),
            ("execution", "submit_to_ack_ms", 190.0),
        ],
    )
    con.commit()
    con.close()


def _seed_market_data_db(path: Path, symbol: str) -> None:
    con = sqlite3.connect(str(path))
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS market_tickers(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          symbol TEXT,
          last REAL
        )
        """
    )
    for px in [100.0, 101.0, 99.5, 102.0, 101.5, 103.0]:
        con.execute("INSERT INTO market_tickers(symbol, last) VALUES(?,?)", (symbol, px))
    con.commit()
    con.close()


def _seed_paper_db(path: Path) -> None:
    con = sqlite3.connect(str(path))
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS paper_equity(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          equity_quote REAL
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS paper_positions(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          qty REAL,
          avg_price REAL
        )
        """
    )
    con.executemany("INSERT INTO paper_equity(equity_quote) VALUES(?)", [(10000.0,), (9500.0,)])
    con.executemany("INSERT INTO paper_positions(qty, avg_price) VALUES(?,?)", [(0.5, 20000.0), (1.0, 1500.0)])
    con.commit()
    con.close()


def _seed_system_status(path: Path) -> None:
    payload = {
        "ts": "2026-03-11T00:00:00+00:00",
        "venues": {
            "coinbase": {"ok": True, "last": 85000.0},
            "gateio": {"ok": False, "error": "rate_limited"},
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_snapshot_uses_seeded_inputs(tmp_path):
    from services.ops.telemetry_snapshot_builder import TelemetrySnapshotCfg, build_snapshot
    from services.risk.risk_daily import RiskDailyDB

    live_intent_db = tmp_path / "live_intent_queue.sqlite"
    ws_status_db = tmp_path / "ws_status.sqlite"
    ws_latency_db = tmp_path / "market_ws.sqlite"
    market_data_db = tmp_path / "market_data.sqlite"
    paper_db = tmp_path / "paper_trading.sqlite"
    exec_db = tmp_path / "execution.sqlite"
    system_status = tmp_path / "system_status.latest.json"

    _seed_live_intent_db(live_intent_db)
    _seed_ws_status_db(ws_status_db)
    _seed_ws_latency_db(ws_latency_db)
    _seed_market_data_db(market_data_db, "BTC/USD")
    _seed_paper_db(paper_db)
    _seed_system_status(system_status)

    rdb = RiskDailyDB(exec_db=str(exec_db))
    rdb.incr_trades(2)
    rdb.add_pnl(realized_pnl_usd=120.0, fee_usd=20.0)

    snap = build_snapshot(
        TelemetrySnapshotCfg(
            symbol="BTC/USD",
            system_status_path=str(system_status),
            live_intent_db_path=str(live_intent_db),
            ws_status_db_path=str(ws_status_db),
            ws_latency_db_path=str(ws_latency_db),
            market_data_db_path=str(market_data_db),
            paper_db_path=str(paper_db),
            exec_db_path=str(exec_db),
        )
    )

    assert snap.exchange_api_ok is True
    assert snap.order_reject_rate > 0.0
    assert snap.ws_lag_ms >= 120.0
    assert snap.venue_latency_ms >= 190.0
    assert snap.realized_volatility > 0.0
    assert snap.drawdown_pct > 0.0
    assert snap.pnl_usd == 100.0
    assert snap.exposure_usd > 0.0
    assert snap.leverage > 0.0


def test_publish_snapshot_writes_ops_store(tmp_path):
    from services.ops.telemetry_snapshot_builder import TelemetrySnapshotCfg, publish_snapshot

    ops_db = tmp_path / "ops.sqlite"
    system_status = tmp_path / "system_status.latest.json"
    _seed_system_status(system_status)

    out = publish_snapshot(
        TelemetrySnapshotCfg(
            ops_db_path=str(ops_db),
            system_status_path=str(system_status),
            symbol="BTC/USD",
        )
    )
    assert out.get("ok") is True
    assert int(out.get("raw_id") or 0) > 0

    store = OpsSignalStoreSQLite(path=str(ops_db))
    latest = store.latest_raw_signal()
    assert isinstance(latest, dict)
    assert latest.get("source") == "ops_signal_adapter"

