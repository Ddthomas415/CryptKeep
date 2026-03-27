from __future__ import annotations

import sqlite3

from services.analytics.paper_loss_replay import build_loss_replay


def test_build_loss_replay_filters_strategy_and_symbol(tmp_path) -> None:
    db = tmp_path / "trade_journal.sqlite"
    con = sqlite3.connect(str(db))
    try:
        con.execute(
            """
            CREATE TABLE journal_fills (
              fill_id TEXT PRIMARY KEY,
              journal_ts TEXT NOT NULL,
              intent_id TEXT,
              source TEXT,
              strategy_id TEXT,
              client_order_id TEXT,
              order_id TEXT NOT NULL,
              fill_ts TEXT NOT NULL,
              venue TEXT NOT NULL,
              symbol TEXT NOT NULL,
              side TEXT NOT NULL,
              qty REAL NOT NULL,
              price REAL NOT NULL,
              fee REAL NOT NULL,
              fee_currency TEXT NOT NULL,
              cash_quote REAL,
              pos_qty REAL,
              pos_avg_price REAL,
              realized_pnl_total REAL
            )
            """
        )
        con.executemany(
            "INSERT INTO journal_fills(fill_id, journal_ts, strategy_id, order_id, fill_ts, venue, symbol, side, qty, price, fee, fee_currency) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            [
                ("f1", "2026-03-19T12:00:00Z", "mean_reversion_rsi", "o1", "2026-03-19T12:00:00Z", "paper", "ETH/USD", "buy", 1.0, 100.0, 0.5, "USD"),
                ("f2", "2026-03-19T12:02:00Z", "mean_reversion_rsi", "o2", "2026-03-19T12:02:00Z", "paper", "ETH/USD", "sell", 1.0, 99.0, 0.5, "USD"),
                ("f3", "2026-03-19T12:04:00Z", "mean_reversion_rsi", "o3", "2026-03-19T12:04:00Z", "paper", "BTC/USD", "buy", 1.0, 100.0, 0.5, "USD"),
                ("f4", "2026-03-19T12:06:00Z", "mean_reversion_rsi", "o4", "2026-03-19T12:06:00Z", "paper", "BTC/USD", "sell", 1.0, 101.0, 0.5, "USD"),
                ("f5", "2026-03-19T12:08:00Z", "ema_cross", "o5", "2026-03-19T12:08:00Z", "paper", "ETH/USD", "buy", 1.0, 100.0, 0.5, "USD"),
                ("f6", "2026-03-19T12:09:00Z", "ema_cross", "o6", "2026-03-19T12:09:00Z", "paper", "ETH/USD", "sell", 1.0, 98.0, 0.5, "USD"),
            ],
        )
        con.commit()
    finally:
        con.close()

    out = build_loss_replay(
        strategy_id="mean_reversion_rsi",
        symbol="ETH/USD",
        journal_path=str(db),
        limit=5,
    )

    assert out["ok"] is True
    assert out["strategy_id"] == "mean_reversion_rsi"
    assert out["symbol_filter"] == "ETH/USD"
    assert out["fills_count"] == 2
    assert out["closed_trade_count"] == 1
    assert out["losing_trade_count"] == 1
    assert out["symbols"] == ["ETH/USD"]
    assert len(out["loss_replays"]) == 1
    row = out["loss_replays"][0]
    assert row["symbol"] == "ETH/USD"
    assert row["duration_sec"] == 120.0
    assert row["gross_pnl"] == -1.0
    assert row["fees"] == 1.0
    assert row["net_pnl"] == -2.0

