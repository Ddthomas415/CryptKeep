from __future__ import annotations

import json, sqlite3, time
from typing import Any

from services.os.app_paths import data_dir

DB_PATH = data_dir() / "journal.sqlite"

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("""
    CREATE TABLE IF NOT EXISTS order_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts REAL,
        intent_id TEXT,
        venue TEXT,
        symbol TEXT,
        event TEXT,
        status TEXT,
        client_oid TEXT,
        order_id TEXT,
        payload_json TEXT
    )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_order_events_intent ON order_events(intent_id, ts)")
    con.commit()
    return con

def log_event(*, intent_id: str, venue: str, symbol: str, event: str, status: str,
              client_oid: str | None = None, order_id: str | None = None, payload: dict | None = None) -> dict[str, Any]:
    con = _connect()
    ts = time.time()
    pj = json.dumps(payload or {}, ensure_ascii=False)
    with con:
        con.execute(
            "INSERT INTO order_events (ts,intent_id,venue,symbol,event,status,client_oid,order_id,payload_json) VALUES (?,?,?,?,?,?,?,?,?)",
            (ts, str(intent_id), str(venue), str(symbol), str(event), str(status),
             (str(client_oid) if client_oid else None), (str(order_id) if order_id else None), pj)
        )
    return {"ok": True, "db": str(DB_PATH), "ts": ts}

def last_events(limit: int = 200) -> dict[str, Any]:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT ts,intent_id,venue,symbol,event,status,client_oid,order_id,payload_json FROM order_events ORDER BY ts DESC LIMIT ?", (int(limit),))
    rows = cur.fetchall()
    out = []
    for r in rows:
        try:
            payload = json.loads(r[8] or "{}")
        except Exception:
            payload = {}
        out.append({
            "ts": r[0], "intent_id": r[1], "venue": r[2], "symbol": r[3],
            "event": r[4], "status": r[5], "client_oid": r[6], "order_id": r[7], "payload": payload
        })
    return {"ok": True, "rows": out, "db": str(DB_PATH)}
