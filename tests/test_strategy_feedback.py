from __future__ import annotations

import sqlite3

from services.analytics import strategy_feedback


def test_load_strategy_feedback_ledger_reports_missing_journal(tmp_path) -> None:
    out = strategy_feedback.load_strategy_feedback_ledger(journal_path=str(tmp_path / "missing.sqlite"), symbol="BTC/USD")

    assert out["ok"] is False
    assert out["status"] == "missing"
    assert out["fills_count"] == 0
    assert out["strategy_count"] == 0
    assert out["symbol_filter"] == "BTC/USD"


def test_load_strategy_feedback_ledger_summarizes_strategy_rows(tmp_path) -> None:
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
                ("f1", "2026-04-09T12:00:00Z", "ema_crossover_v1", "o1", "2026-04-09T12:00:00Z", "paper", "BTC/USD", "buy", 1.0, 100.0, 1.0, "USD"),
                ("f2", "2026-04-09T12:10:00Z", "ema_crossover_v1", "o2", "2026-04-09T12:10:00Z", "paper", "BTC/USD", "sell", 1.0, 110.0, 1.0, "USD"),
                ("f3", "2026-04-09T12:20:00Z", "mystery_strategy", "o3", "2026-04-09T12:20:00Z", "paper", "BTC/USD", "buy", 1.0, 100.0, 1.0, "USD"),
            ],
        )
        con.commit()
    finally:
        con.close()

    out = strategy_feedback.load_strategy_feedback_ledger(journal_path=str(db), symbol="BTC/USD")

    assert out["ok"] is True
    assert out["status"] == "available"
    assert out["fills_count"] == 2
    assert out["strategy_count"] == 1
    assert out["unmapped_strategy_ids"] == ["mystery_strategy"]
    row = out["rows"][0]
    assert row["strategy"] == "ema_cross"
    assert row["closed_trades"] == 1
    assert row["net_realized_pnl"] == 8.0
    assert row["expectancy_per_closed_trade"] == 8.0
    assert row["win_rate"] == 1.0


def test_build_strategy_feedback_weighting_handles_thin_boost_and_penalty() -> None:
    thin = strategy_feedback.build_strategy_feedback_weighting(
        {
            "closed_trades": 1,
            "expectancy_per_closed_trade": 2.0,
            "net_realized_pnl": 2.0,
            "recent_net_realized_pnl": 2.0,
            "win_rate": 1.0,
        }
    )
    boost = strategy_feedback.build_strategy_feedback_weighting(
        {
            "closed_trades": 20,
            "expectancy_per_closed_trade": 1.5,
            "net_realized_pnl": 30.0,
            "recent_net_realized_pnl": 4.0,
            "win_rate": 0.6,
        }
    )
    penalty = strategy_feedback.build_strategy_feedback_weighting(
        {
            "closed_trades": 20,
            "expectancy_per_closed_trade": -0.5,
            "net_realized_pnl": -10.0,
            "recent_net_realized_pnl": -1.0,
            "win_rate": 0.4,
        }
    )

    assert thin["status"] == "thin"
    assert thin["adjustment"] == 0.0
    assert boost["status"] == "boost"
    assert boost["adjustment"] > 0.0
    assert penalty["status"] == "penalty"
    assert penalty["adjustment"] < 0.0
