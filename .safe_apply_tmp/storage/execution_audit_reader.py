from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

def _data_dir() -> Path:
    try:
        from services.os.app_paths import data_dir
        return data_dir()
    except Exception:
        p = Path(__file__).resolve().parents[1] / "data"
        p.mkdir(parents=True, exist_ok=True)
        return p

DB_PATH = _data_dir() / "execution_audit.sqlite"

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    return c

def db_exists() -> bool:
    return DB_PATH.exists()

def list_orders(
    *,
    limit: int = 200,
    venue: str | None = None,
    symbol: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    if not db_exists():
        return []
    limit = int(limit)
    if limit <= 0: limit = 200
    if limit > 2000: limit = 2000

    q = "SELECT * FROM orders WHERE 1=1"
    params: list[Any] = []

    if venue:
        q += " AND venue = ?"
        params.append(str(venue).strip().lower())
    if symbol:
        q += " AND symbol = ?"
        params.append(str(symbol).strip().upper())
    if status:
        q += " AND status = ?"
        params.append(str(status).strip())

    q += " ORDER BY ts_epoch DESC LIMIT ?"
    params.append(limit)

    c = _conn()
    try:
        rows = c.execute(q, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        c.close()

def list_fills(
    *,
    limit: int = 200,
    venue: str | None = None,
    symbol: str | None = None,
    exchange_order_id: str | None = None,
) -> list[dict[str, Any]]:
    if not db_exists():
        return []
    limit = int(limit)
    if limit <= 0: limit = 200
    if limit > 4000: limit = 4000

    q = "SELECT * FROM fills WHERE 1=1"
    params: list[Any] = []

    if venue:
        q += " AND venue = ?"
        params.append(str(venue).strip().lower())
    if symbol:
        q += " AND symbol = ?"
        params.append(str(symbol).strip().upper())
    if exchange_order_id:
        q += " AND exchange_order_id = ?"
        params.append(str(exchange_order_id).strip())

    q += " ORDER BY ts_epoch DESC LIMIT ?"
    params.append(limit)

    c = _conn()
    try:
        rows = c.execute(q, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        c.close()

def list_statuses() -> list[str]:
    if not db_exists():
        return []
    c = _conn()
    try:
        rows = c.execute("SELECT DISTINCT status FROM orders WHERE status IS NOT NULL ORDER BY status").fetchall()
        return [r["status"] for r in rows if r["status"]]
    finally:
        c.close()
