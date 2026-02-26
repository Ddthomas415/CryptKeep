from __future__ import annotations
import json, sqlite3, time
from dataclasses import dataclass
from typing import Any
from services.os.app_paths import data_dir

DB_PATH = data_dir() / "execution.sqlite"

def _now() -> float:
    return time.time()

def _ensure_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute(
            """
        CREATE TABLE IF NOT EXISTS order_intents (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          intent_id TEXT NOT NULL UNIQUE,
          ts_epoch REAL NOT NULL,
          updated_ts_epoch REAL NOT NULL,
          venue TEXT NOT NULL,
          symbol TEXT NOT NULL,
          side TEXT NOT NULL,
          timeframe TEXT,
          bar_ts_ms INTEGER,
          status TEXT NOT NULL,
          meta_json TEXT,
          last_error TEXT
        )
        """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_intents_status ON order_intents(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_intents_symbol ON order_intents(symbol)")
        conn.commit()
    finally:
        conn.close()

def _intent_id(*, venue: str, symbol: str, side: str, timeframe: str, bar_ts_ms: int) -> str:
    return f"{venue.strip().lower()}::{symbol.strip().upper()}::{side.strip().lower()}::{timeframe.strip()}::{int(bar_ts_ms)}"

@dataclass
class Intent:
    intent_id: str
    venue: str
    symbol: str
    side: str
    timeframe: str
    bar_ts_ms: int
    status: str
    ts_epoch: float
    updated_ts_epoch: float
    meta: dict[str, Any] | None = None
    last_error: str | None = None

class OrderIntentLedger:
    def __init__(self):
        _ensure_db()

    def create_if_new(self, *, venue: str, symbol: str, side: str, timeframe: str, bar_ts_ms: int, meta: dict[str, Any] | None = None) -> dict:
        _ensure_db()
        iid = _intent_id(venue=venue, symbol=symbol, side=side, timeframe=timeframe, bar_ts_ms=bar_ts_ms)
        now = _now()
        conn = sqlite3.connect(str(DB_PATH))
        try:
            try:
                conn.execute(
                    "INSERT INTO order_intents (intent_id, ts_epoch, updated_ts_epoch, venue, symbol, side, timeframe, bar_ts_ms, status, meta_json, last_error) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (iid, float(now), float(now), venue.strip().lower(), symbol.strip().upper(), side.strip().lower(), timeframe, int(bar_ts_ms), "NEW", json.dumps(meta or {}, ensure_ascii=False), None)
                )
                conn.commit()
                return {"ok": True, "created": True, "intent_id": iid, "status": "NEW"}
            except sqlite3.IntegrityError:
                row = conn.execute("SELECT intent_id, venue, symbol, side, timeframe, bar_ts_ms, status, ts_epoch, updated_ts_epoch, meta_json, last_error FROM order_intents WHERE intent_id=?", (iid,)).fetchone()
                if not row: return {"ok": False, "reason": "intent_missing_after_integrity_error", "intent_id": iid}
                meta_obj = {}
                try: meta_obj = json.loads(row[9]) if row[9] else {}
                except: meta_obj = {}
                return {"ok": True, "created": False, "intent_id": iid, "status": row[6], "intent":{"intent_id": row[0],"venue":row[1],"symbol":row[2],"side":row[3],"timeframe":row[4],"bar_ts_ms":row[5],"status":row[6],"ts_epoch":row[7],"updated_ts_epoch":row[8],"meta":meta_obj,"last_error":row[10]}}
        finally:
            conn.close()

    def reconcile_stale_new(self, *, max_age_sec: float = 600.0) -> dict:
        _ensure_db()
        cutoff = _now() - float(max_age_sec)
        conn = sqlite3.connect(str(DB_PATH))
        try:
            ids = [r[0] for r in conn.execute("SELECT intent_id FROM order_intents WHERE status='NEW' AND ts_epoch < ?", (float(cutoff),)).fetchall()]
            for iid in ids:
                conn.execute("UPDATE order_intents SET status='STALE', updated_ts_epoch=? WHERE intent_id=?", (float(_now()), iid))
            conn.commit()
            return {"ok": True, "staled": len(ids)}
        finally:
            conn.close()

    def list_recent(self, limit: int = 200) -> dict:
        _ensure_db()
        conn = sqlite3.connect(str(DB_PATH))
        try:
            rows = []
            for r in conn.execute("SELECT intent_id, venue, symbol, side, timeframe, bar_ts_ms, status, ts_epoch, updated_ts_epoch, meta_json, last_error FROM order_intents ORDER BY updated_ts_epoch DESC LIMIT ?", (int(limit),)).fetchall():
                meta_obj = {}
                try: meta_obj = json.loads(r[9]) if r[9] else {}
                except: meta_obj = {}
                rows.append({"intent_id": r[0], "venue": r[1], "symbol": r[2], "side": r[3], "timeframe": r[4], "bar_ts_ms": r[5], "status": r[6], "ts_epoch": r[7], "updated_ts_epoch": r[8], "meta": meta_obj, "last_error": r[10]})
            return {"ok": True, "path": str(DB_PATH), "rows": rows}
        finally:
            conn.close()
