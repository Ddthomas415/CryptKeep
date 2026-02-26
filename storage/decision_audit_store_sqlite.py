from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = data_dir() / "decision_audit.sqlite"

SCHEMA = '''
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS decisions (
  decision_id TEXT PRIMARY KEY,
  first_seen_ts TEXT NOT NULL,
  last_seen_ts TEXT NOT NULL,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL,
  safety_ok INTEGER,
  safety_reason TEXT,
  meta_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_decisions_last_seen ON decisions(last_seen_ts);
CREATE INDEX IF NOT EXISTS idx_decisions_venue_symbol ON decisions(venue, symbol);
'''

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

class DecisionAuditStoreSQLite:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db = db_path
        self.db.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db, isolation_level=None, check_same_thread=False)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        return con

    def _init(self) -> None:
        con = self._connect()
        try:
            for stmt in SCHEMA.strip().split(";"):
                s = stmt.strip()
                if s:
                    con.execute(s)
        finally:
            con.close()

    def upsert_decision(
        self,
        decision_id: str,
        venue: str,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        meta: dict | None = None,
        safety_ok: bool | None = None,
        safety_reason: str | None = None,
        ts: str | None = None,
    ) -> None:
        ts = ts or _now()
        meta_json = None
        try:
            meta_json = json.dumps(meta or {}, sort_keys=True)
        except Exception:
            meta_json = None
        con = self._connect()
        try:
            con.execute(
                "INSERT OR IGNORE INTO decisions(decision_id, first_seen_ts, last_seen_ts, venue, symbol, side, qty, price, safety_ok, safety_reason, meta_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(decision_id),
                    str(ts),
                    str(ts),
                    str(venue),
                    str(symbol),
                    str(side),
                    float(qty),
                    float(price),
                    (1 if safety_ok else 0) if safety_ok is not None else None,
                    (str(safety_reason) if safety_reason is not None else None),
                    meta_json,
                ),
            )
            con.execute(
                "UPDATE decisions SET last_seen_ts=?, safety_ok=COALESCE(?, safety_ok), safety_reason=COALESCE(?, safety_reason), meta_json=COALESCE(?, meta_json) "
                "WHERE decision_id=?",
                (
                    str(ts),
                    (1 if safety_ok else 0) if safety_ok is not None else None,
                    (str(safety_reason) if safety_reason is not None else None),
                    meta_json,
                    str(decision_id),
                ),
            )
        finally:
            con.close()

    def last_decisions(self, limit: int = 200, venue: str | None = None, symbol: str | None = None) -> List[dict]:
        con = self._connect()
        try:
            q = "SELECT decision_id, first_seen_ts, last_seen_ts, venue, symbol, side, qty, price, safety_ok, safety_reason, meta_json FROM decisions"
            args = []
            wh = []
            if venue:
                wh.append("venue=?"); args.append(str(venue))
            if symbol:
                wh.append("symbol=?"); args.append(str(symbol))
            if wh:
                q += " WHERE " + " AND ".join(wh)
            q += " ORDER BY last_seen_ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            out = []
            for r in rows:
                meta = None
                try:
                    meta = json.loads(r[10]) if r[10] else None
                except Exception:
                    meta = None
                out.append({
                    "decision_id": r[0],
                    "first_seen_ts": r[1],
                    "last_seen_ts": r[2],
                    "venue": r[3],
                    "symbol": r[4],
                    "side": r[5],
                    "qty": float(r[6]),
                    "price": float(r[7]),
                    "safety_ok": (bool(r[8]) if r[8] is not None else None),
                    "safety_reason": r[9],
                    "meta": meta,
                })
            return out
        finally:
            con.close()
