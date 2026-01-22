from __future__ import annotations
import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "signal_inbox.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS signal_inbox (
  signal_id TEXT PRIMARY KEY,
  ts TEXT NOT NULL,
  received_ts TEXT NOT NULL,
  source TEXT NOT NULL,
  author TEXT NOT NULL,
  venue_hint TEXT,
  symbol TEXT NOT NULL,
  action TEXT NOT NULL,
  confidence REAL NOT NULL,
  notes TEXT,
  raw_json TEXT NOT NULL,
  status TEXT NOT NULL,
  updated_ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_si_ts ON signal_inbox(ts);
CREATE INDEX IF NOT EXISTS idx_si_symbol_ts ON signal_inbox(symbol, ts);
CREATE INDEX IF NOT EXISTS idx_si_status ON signal_inbox(status);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con

class SignalInboxSQLite:
    def __init__(self) -> None:
        _connect().close()

    def upsert_signal(self, sig: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO signal_inbox(signal_id, ts, received_ts, source, author, venue_hint, symbol, action, confidence, notes, raw_json, status, updated_ts) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(sig["signal_id"]),
                    str(sig["ts"]),
                    str(sig.get("received_ts") or _now()),
                    str(sig.get("source") or "unknown"),
                    str(sig.get("author") or "unknown"),
                    sig.get("venue_hint"),
                    str(sig["symbol"]),
                    str(sig["action"]),
                    float(sig.get("confidence") or 0.5),
                    sig.get("notes"),
                    json.dumps(sig.get("raw") or {}, ensure_ascii=False),
                    str(sig.get("status") or "new"),
                    _now(),
                ),
            )
        finally:
            con.close()

    def list_signals(self, limit: int = 500, status: str | None = None, symbol: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = ("SELECT signal_id, ts, received_ts, source, author, venue_hint, symbol, action, confidence, notes, raw_json, status, updated_ts "
                 "FROM signal_inbox")
            args = []
            wh = []
            if status:
                wh.append("status=?"); args.append(str(status))
            if symbol:
                wh.append("symbol=?"); args.append(str(symbol))
            if wh:
                q += " WHERE " + " AND ".join(wh)
            q += " ORDER BY ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [
                {
                    "signal_id": r[0], "ts": r[1], "received_ts": r[2], "source": r[3], "author": r[4],
                    "venue_hint": r[5], "symbol": r[6], "action": r[7], "confidence": r[8],
                    "notes": r[9], "raw": json.loads(r[10] or "{}"),
                    "status": r[11], "updated_ts": r[12],
                }
                for r in rows
            ]
        finally:
            con.close()

    def set_status(self, signal_id: str, status: str) -> None:
        con = _connect()
        try:
            con.execute("UPDATE signal_inbox SET status=?, updated_ts=? WHERE signal_id=?", (str(status), _now(), str(signal_id)))
        finally:
            con.close()
