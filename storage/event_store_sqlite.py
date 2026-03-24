from __future__ import annotations
import asyncio
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Optional
try:
    import orjson
except ModuleNotFoundError:
    import json

    class _OrjsonCompat:
        @staticmethod
        def dumps(obj):
            return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

        @staticmethod
        def loads(data):
            if isinstance(data, (bytes, bytearray)):
                data = data.decode("utf-8")
            return json.loads(data)

    orjson = _OrjsonCompat()
from core.event_factory import event_from_dict
from core.event_key import compute_event_key
from core.events import EventBase
from core.symbols import normalize_symbol

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  symbol_norm TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_key TEXT,
  payload BLOB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_symbol ON events(symbol);
CREATE INDEX IF NOT EXISTS idx_events_symbol_norm ON events(symbol_norm);
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_event_key ON events(event_key) WHERE event_key IS NOT NULL;
CREATE TABLE IF NOT EXISTS health (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  service TEXT NOT NULL,
  status TEXT NOT NULL,
  detail BLOB
);
CREATE INDEX IF NOT EXISTS idx_health_service_ts ON health(service, ts);
"""

@dataclass
class SQLiteEventStore:
    path: Path

    def __post_init__(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_or_upgrade_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, isolation_level=None, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        return conn

    def _table_columns(self, conn: sqlite3.Connection, table: str) -> set[str]:
        cur = conn.execute(f"PRAGMA table_info({table})")
        return {row[1] for row in cur.fetchall()}

    def _init_or_upgrade_db(self) -> None:
        conn = self._connect()
        try:
            for stmt in SCHEMA_SQL.strip().split(";"):
                s = stmt.strip()
                if s:
                    conn.execute(s)
            cols = self._table_columns(conn, "events")
            if "symbol_norm" not in cols:
                conn.execute("ALTER TABLE events ADD COLUMN symbol_norm TEXT")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_events_symbol_norm ON events(symbol_norm)")
            if "event_key" not in cols:
                conn.execute("ALTER TABLE events ADD COLUMN event_key TEXT")
                conn.execute(
                    "CREATE UNIQUE INDEX IF NOT EXISTS idx_events_event_key ON events(event_key) WHERE event_key IS NOT NULL"
                )
            self._backfill_recent(conn, limit=20000)
        finally:
            conn.close()

    def _backfill_recent(self, conn: sqlite3.Connection, limit: int = 20000) -> None:
        cur = conn.execute(
            "SELECT id, venue, symbol FROM events WHERE symbol_norm IS NULL OR symbol_norm = '' ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        for rid, venue, symbol in cur.fetchall():
            symn = normalize_symbol(str(venue), str(symbol))
            conn.execute("UPDATE events SET symbol_norm = ? WHERE id = ?", (symn, rid))
        cur = conn.execute(
            "SELECT id, payload FROM events WHERE event_key IS NULL ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        for rid, payload in cur.fetchall():
            try:
                d = orjson.loads(payload)
                e = event_from_dict(d)
                ek = compute_event_key(e)
                if ek:
                    conn.execute("UPDATE events SET event_key = ? WHERE id = ?", (ek, rid))
            except Exception:
                continue

    async def append(self, e: EventBase) -> None:
        await asyncio.to_thread(self._append_sync, e)

    def _append_sync(self, e: EventBase) -> None:
        conn = self._connect()
        try:
            payload = orjson.dumps(e.model_dump())
            symn = normalize_symbol(e.venue, e.symbol)
            ek = compute_event_key(e)
            conn.execute(
                "INSERT OR IGNORE INTO events(ts, venue, symbol, symbol_norm, event_type, event_key, payload) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (e.ts.isoformat(), e.venue, e.symbol, symn, e.event_type, ek, payload),
            )
        finally:
            conn.close()

    async def heartbeat(self, ts_iso: str, service: str, status: str, detail: Optional[Dict[str, Any]] = None) -> None:
        await asyncio.to_thread(self._heartbeat_sync, ts_iso, service, status, detail)

    def _heartbeat_sync(self, ts_iso: str, service: str, status: str, detail: Optional[Dict[str, Any]]) -> None:
        conn = self._connect()
        try:
            blob = orjson.dumps(detail or {})
            conn.execute(
                "INSERT INTO health(ts, service, status, detail) VALUES (?, ?, ?, ?)",
                (ts_iso, service, status, blob),
            )
        finally:
            conn.close()

    async def tail(self, after_id: int = 0, poll_sec: float = 0.25) -> AsyncIterator[EventBase]:
        last = after_id
        while True:
            rows = await asyncio.to_thread(self._fetch_batch, last)
            if not rows:
                await asyncio.sleep(poll_sec)
                continue
            for rid, payload in rows:
                last = rid
                d = orjson.loads(payload)
                yield event_from_dict(d)

    def _fetch_batch(self, after_id: int, limit: int = 500):
        conn = self._connect()
        try:
            cur = conn.execute(
                "SELECT id, payload FROM events WHERE id > ? ORDER BY id ASC LIMIT ?",
                (after_id, limit),
            )
            return cur.fetchall()
        finally:
            conn.close()
