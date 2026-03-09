from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from typing import Any

from services.os.app_paths import data_dir

DB_PATH = data_dir() / "position_state.sqlite"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS position_state(
          venue TEXT NOT NULL,
          symbol TEXT NOT NULL,
          base TEXT NOT NULL,
          quote TEXT NOT NULL,
          qty REAL NOT NULL,
          status TEXT NOT NULL,
          note TEXT NOT NULL,
          raw_json TEXT NOT NULL,
          updated_ts TEXT NOT NULL,
          PRIMARY KEY(venue, symbol)
        )
        """
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_position_state_updated ON position_state(updated_ts)")
    return con


class PositionStateSQLite:
    def __init__(self) -> None:
        _connect().close()

    def upsert(
        self,
        *,
        venue: str,
        symbol: str,
        base: str,
        quote: str,
        qty: float,
        status: str,
        note: str = "",
        raw: dict[str, Any] | None = None,
    ) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO position_state(venue, symbol, base, quote, qty, status, note, raw_json, updated_ts) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    str(venue),
                    str(symbol),
                    str(base),
                    str(quote),
                    float(qty or 0.0),
                    str(status),
                    str(note or ""),
                    json.dumps(raw or {}, sort_keys=True),
                    _now(),
                ),
            )
        finally:
            con.close()

    def get(self, *, venue: str, symbol: str) -> dict[str, Any] | None:
        con = _connect()
        try:
            row = con.execute(
                "SELECT venue, symbol, base, quote, qty, status, note, raw_json, updated_ts FROM position_state WHERE venue=? AND symbol=?",
                (str(venue), str(symbol)),
            ).fetchone()
            if not row:
                return None
            return {
                "venue": row[0],
                "symbol": row[1],
                "base": row[2],
                "quote": row[3],
                "qty": row[4],
                "status": row[5],
                "note": row[6],
                "raw": json.loads(row[7] or "{}"),
                "updated_ts": row[8],
            }
        finally:
            con.close()
