from __future__ import annotations
import sqlite3
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "meta_decisions.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS meta_decisions (
  decision_id TEXT PRIMARY KEY,
  ts TEXT NOT NULL,
  symbol TEXT NOT NULL,
  venue TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  action TEXT NOT NULL,
  score REAL NOT NULL,
  confidence REAL NOT NULL,
  internal_action TEXT,
  internal_score REAL,
  external_action TEXT,
  external_score REAL,
  details_json TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_md_ts ON meta_decisions(ts);
CREATE INDEX IF NOT EXISTS idx_md_symbol_ts ON meta_decisions(symbol, ts);
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

class MetaDecisionsSQLite:
    def __init__(self) -> None:
        _connect().close()

    def insert(self, row: Dict[str, Any]) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO meta_decisions(decision_id, ts, symbol, venue, timeframe, action, score, confidence, internal_action, internal_score, external_action, external_score, details_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(row["decision_id"]),
                    str(row.get("ts") or _now()),
                    str(row["symbol"]),
                    str(row["venue"]),
                    str(row["timeframe"]),
                    str(row["action"]),
                    float(row.get("score") or 0.0),
                    float(row.get("confidence") or 0.0),
                    row.get("internal_action"),
                    row.get("internal_score"),
                    row.get("external_action"),
                    row.get("external_score"),
                    json.dumps(row.get("details") or {}, ensure_ascii=False),
                ),
            )
        finally:
            con.close()

    def list(self, limit: int = 500, symbol: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = ("SELECT decision_id, ts, symbol, venue, timeframe, action, score, confidence, internal_action, internal_score, external_action, external_score, details_json "
                 "FROM meta_decisions")
            args = []
            if symbol:
                q += " WHERE symbol=?"
                args.append(str(symbol))
            q += " ORDER BY ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [
                {
                    "decision_id": r[0], "ts": r[1], "symbol": r[2], "venue": r[3], "timeframe": r[4],
                    "action": r[5], "score": r[6], "confidence": r[7],
                    "internal_action": r[8], "internal_score": r[9],
                    "external_action": r[10], "external_score": r[11],
                    "details": json.loads(r[12] or "{}"),
                }
                for r in rows
            ]
        finally:
            con.close()
