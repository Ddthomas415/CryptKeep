from __future__ import annotations

import sqlite3
from pathlib import Path

from services.execution import idempotency_inspector as ii


def _build_idempotency_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    try:
        conn.execute(
            """
            CREATE TABLE idempotency (
                key TEXT,
                status TEXT,
                payload TEXT,
                updated_epoch INTEGER
            )
            """
        )
        conn.executemany(
            "INSERT INTO idempotency(key, status, payload, updated_epoch) VALUES(?, ?, ?, ?)",
            [
                ("coinbase|BTC/USD|a", "error", '{"msg":"boom-1"}', 100),
                ("binance|ETH/USDT|b", "ok", '{"msg":"ok"}', 200),
                ("coinbase|BTC/USD|c", "error", '{"msg":"boom-2"}', 300),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def test_list_recent_applies_status_filter_and_limit(monkeypatch, tmp_path):
    db = tmp_path / "idempotency.sqlite"
    _build_idempotency_db(db)
    monkeypatch.setattr(ii, "data_dir", lambda: tmp_path)

    out = ii.list_recent(limit=10, status="error")
    assert out.get("ok") is True
    rows = list(out.get("rows") or [])
    assert len(rows) == 2
    assert rows[0]["key"] == "coinbase|BTC/USD|c"
    assert rows[0]["venue"] == "coinbase"
    assert rows[0]["symbol"] == "BTC/USD"
    assert rows[0]["payload"] == {"msg": "boom-2"}
    assert all(r.get("status") == "error" for r in rows)

    out_limited = ii.list_recent(limit=1, status="error")
    rows_limited = list(out_limited.get("rows") or [])
    assert len(rows_limited) == 1
    assert rows_limited[0]["key"] == "coinbase|BTC/USD|c"


def test_filter_rows_by_venue_and_symbol():
    rows = [
        {"venue": "coinbase", "symbol": "BTC/USD", "key": "1"},
        {"venue": "coinbase", "symbol": "ETH/USD", "key": "2"},
        {"venue": "binance", "symbol": "BTC/USDT", "key": "3"},
    ]
    out = ii.filter_rows(rows, venue="coinbase", symbol="BTC/USD")
    assert [r["key"] for r in out] == ["1"]
