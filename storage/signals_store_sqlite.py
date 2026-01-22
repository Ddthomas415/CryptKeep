from __future__ import annotations
import asyncio
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
import orjson

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS trader_signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  platform TEXT NOT NULL,
  trader_id TEXT NOT NULL,
  venue TEXT,
  symbol_norm TEXT NOT NULL,
  side TEXT NOT NULL,
  confidence REAL,
  qty REAL,
  price REAL,
  horizon_min INTEGER,
  raw BLOB,
  UNIQUE(platform, trader_id, ts, symbol_norm, side)
);
CREATE INDEX IF NOT EXISTS idx_ts ON trader_signals(ts);
CREATE INDEX IF NOT EXISTS idx_symbol ON trader_signals(symbol_norm);
"""

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class SignalsStoreSQLite:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _init(self) -> None:
        conn = self._connect()
        try:
            for stmt in SCHEMA.strip().split(";"):
                s = stmt.strip()
                if s:
                    conn.execute(s)
        finally:
            conn.close()

    async def upsert_signal(self, payload: Dict[str, Any]) -> bool:
        return await asyncio.to_thread(self._upsert_sync, payload)

    def _upsert_sync(self, payload: Dict[str, Any]) -> bool:
        conn = self._connect()
        try:
            ts = str(payload.get("ts") or utc_now().isoformat())
            platform = str(payload.get("platform") or "unknown")
            trader_id = str(payload.get("trader_id") or "unknown")
            venue = str(payload.get("venue") or "")
            symbol = str(payload.get("symbol_norm") or payload.get("symbol") or "").upper().replace("/", "-")
            side = str(payload.get("side") or "").lower()
            if side not in ("buy","sell"):
                return False
            confidence = payload.get("confidence")
            qty = payload.get("qty")
            price = payload.get("price")
            horizon = payload.get("horizon_min")
            conn.execute(
                "INSERT OR IGNORE INTO trader_signals(ts, platform, trader_id, venue, symbol_norm, side, confidence, qty, price, horizon_min, raw) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    ts, platform, trader_id, venue, symbol, side,
                    float(confidence) if confidence is not None else None,
                    float(qty) if qty is not None else None,
                    float(price) if price is not None else None,
                    int(horizon) if horizon is not None else None,
                    orjson.dumps(payload),
                ),
            )
            return True
        except Exception:
            return False
        finally:
            conn.close()
