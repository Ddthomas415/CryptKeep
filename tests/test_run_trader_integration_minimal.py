from __future__ import annotations

import asyncio
import json
import sqlite3
import time
from pathlib import Path

import yaml

from services.trading_runner import run_trader
from storage.market_store_sqlite import MarketStore


def test_runner_minimal_integration_paper_loop_db_write(monkeypatch, tmp_path):
    journal_db = tmp_path / "paper_journal.sqlite"
    market_db = tmp_path / "market_data.sqlite"
    state_file = tmp_path / "runner_state.json"
    kill_file = tmp_path / "KILL_SWITCH.flag"
    cfg_path = tmp_path / "trading.yaml"

    # Seed market data so aggregation returns a tradable price.
    market = MarketStore(market_db)
    market.upsert_ticker(
        ts_ms=int(time.time() * 1000),
        exchange="binance",
        symbol="BTC/USDT",
        bid=100.0,
        ask=101.0,
        last=100.5,
    )

    cfg = {
        "mode": "paper",
        "run_id": "it_run",
        "paths": {
            "journal_db": str(journal_db),
            "market_db": str(market_db),
            "state_file": str(state_file),
            "kill_switch_file": str(kill_file),
        },
        "market_data": {
            "auto_start_feeds": False,
        },
        "aggregation": {
            "mode": "median",
            "stale_seconds": 0,
        },
        "symbols": ["BTC/USDT"],
        "strategy": {
            "type": "ema_crossover",
            "ema": {
                "fast": 12,
                "slow": 26,
                "min_history": 1,
                "trade_qty": 0.1,
            },
        },
        "risk": {
            "max_trades_per_day": 5,
            "max_position_notional": 10_000.0,
            "max_drawdown_frac": 0.5,
            "min_cash": 0.0,
        },
        "runner": {
            "tick_interval_sec": 0.05,
        },
    }
    cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")

    # Deterministic one-way signal so the first loop places one BUY.
    monkeypatch.setattr(run_trader, "compute_signal", lambda _st: 1)

    async def _scenario() -> int:
        task = asyncio.create_task(run_trader.runner(cfg_path))
        await asyncio.sleep(0.30)
        kill_file.write_text("1\n", encoding="utf-8")
        return await asyncio.wait_for(task, timeout=5.0)

    rc = asyncio.run(_scenario())
    assert rc == 0
    assert journal_db.exists()
    assert state_file.exists()

    con = sqlite3.connect(str(journal_db))
    try:
        fills_count = int(con.execute("SELECT COUNT(*) FROM fills").fetchone()[0])
        pos_count = int(con.execute("SELECT COUNT(*) FROM positions").fetchone()[0])
    finally:
        con.close()

    assert fills_count >= 1
    assert pos_count >= 1

    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert int(state.get("trades_today") or 0) >= 1
