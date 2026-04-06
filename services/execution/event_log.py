from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path

from services.os.app_paths import data_dir, ensure_dirs

_LOG = logging.getLogger(__name__)

_DB_PATH: Path | None = None


def _db_path() -> Path:
    global _DB_PATH
    if _DB_PATH is None:
        ensure_dirs()
        _DB_PATH = data_dir() / "lifecycle_events.sqlite"
    return _DB_PATH


def _conn() -> sqlite3.Connection:
    p = _db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(str(p), timeout=10)
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")
    c.execute("""
        CREATE TABLE IF NOT EXISTS lifecycle_events (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_ms     INTEGER NOT NULL,
            venue     TEXT NOT NULL,
            symbol    TEXT NOT NULL,
            event     TEXT NOT NULL,
            ref_id    TEXT,
            payload   TEXT NOT NULL DEFAULT '{}'
        )
    """)
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_le_venue_symbol "
        "ON lifecycle_events(venue, symbol, ts_ms)"
    )
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_le_event "
        "ON lifecycle_events(event, ts_ms)"
    )
    c.commit()
    return c


def log_event(
    venue: str,
    symbol: str,
    event: str,
    *,
    ref_id: str | None = None,
    payload: dict | None = None,
) -> str:
    key = f"{venue}/{symbol}:{event}:{ref_id}"
    try:
        ts_ms = int(time.time() * 1000)
        payload_json = json.dumps(payload or {}, default=str)[:65536]
        with _conn() as c:
            c.execute(
                "INSERT INTO lifecycle_events(ts_ms, venue, symbol, event, ref_id, payload) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (ts_ms, str(venue), str(symbol), str(event), ref_id, payload_json),
            )
    except Exception:
        _LOG.exception("event_log.log_event failed key=%s", key)
    return key
