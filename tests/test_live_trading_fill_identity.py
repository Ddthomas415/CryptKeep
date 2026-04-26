import sqlite3

import storage.live_trading_sqlite as mod


def _fill(**overrides):
    row = {
        "trade_id": "trade-1",
        "ts": "2026-04-26T00:00:00Z",
        "venue": "coinbase",
        "symbol": "BTC/USD",
        "side": "buy",
        "qty": 1.0,
        "price": 100.0,
        "fee": None,
        "fee_currency": None,
        "client_order_id": "cid-1",
        "exchange_order_id": "ex-1",
    }
    row.update(overrides)
    return row


def test_live_fills_keep_same_trade_id_when_venue_or_symbol_differs(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_trading.sqlite")
    db = mod.LiveTradingSQLite()

    db.insert_fill(_fill())
    db.insert_fill(_fill(
        ts="2026-04-26T00:01:00Z",
        venue="kraken",
        symbol="ETH/USD",
        side="sell",
        qty=2.0,
        price=200.0,
        client_order_id="cid-2",
        exchange_order_id="ex-2",
    ))

    fills = db.list_fills(limit=10)
    assert len(fills) == 2
    assert {f["venue"] for f in fills} == {"coinbase", "kraken"}
    assert {f["trade_id"] for f in fills} == {"trade-1"}


def test_live_fills_ignore_exact_same_venue_symbol_trade_id_duplicate(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "DB_PATH", tmp_path / "live_trading.sqlite")
    db = mod.LiveTradingSQLite()

    db.insert_fill(_fill())
    db.insert_fill(_fill(ts="2026-04-26T00:01:00Z", qty=9.0))

    fills = db.list_fills(limit=10)
    assert len(fills) == 1
    assert fills[0]["qty"] == 1.0


def test_live_fills_migrate_legacy_trade_id_primary_key_table(tmp_path, monkeypatch):
    db_path = tmp_path / "live_trading.sqlite"
    monkeypatch.setattr(mod, "DB_PATH", db_path)

    con = sqlite3.connect(db_path)
    con.execute(
        """
        CREATE TABLE live_fills (
          trade_id TEXT PRIMARY KEY,
          ts TEXT NOT NULL,
          venue TEXT NOT NULL,
          symbol TEXT NOT NULL,
          side TEXT NOT NULL,
          qty REAL NOT NULL,
          price REAL NOT NULL,
          fee REAL,
          fee_currency TEXT,
          client_order_id TEXT,
          exchange_order_id TEXT
        )
        """
    )
    con.execute(
        "INSERT INTO live_fills(trade_id, ts, venue, symbol, side, qty, price, fee, fee_currency, client_order_id, exchange_order_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        ("legacy-trade", "2026-04-26T00:00:00Z", "coinbase", "BTC/USD", "buy", 1.0, 100.0, None, None, "cid-1", "ex-1"),
    )
    con.commit()
    con.close()

    db = mod.LiveTradingSQLite()
    fills = db.list_fills(limit=10)

    assert len(fills) == 1
    assert fills[0]["trade_id"] == "legacy-trade"
    assert fills[0]["venue"] == "coinbase"

    db.insert_fill(_fill(
        trade_id="legacy-trade",
        ts="2026-04-26T00:01:00Z",
        venue="kraken",
        symbol="ETH/USD",
        client_order_id="cid-2",
        exchange_order_id="ex-2",
    ))

    fills = db.list_fills(limit=10)
    assert len(fills) == 2
    assert {f["venue"] for f in fills} == {"coinbase", "kraken"}

    db.insert_fill(_fill(
        trade_id="legacy-trade",
        ts="2026-04-26T00:01:00Z",
        venue="kraken",
        symbol="ETH/USD",
        client_order_id="cid-2",
        exchange_order_id="ex-2",
    ))

    fills = db.list_fills(limit=10)
    assert len(fills) == 2
    assert {f["venue"] for f in fills} == {"coinbase", "kraken"}
