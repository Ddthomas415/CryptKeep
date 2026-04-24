from __future__ import annotations

import json, sqlite3, time
from typing import Any

from services.os.app_paths import data_dir

DB_PATH = data_dir() / "intents.sqlite"

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("""
    CREATE TABLE IF NOT EXISTS intents (
        intent_id TEXT PRIMARY KEY,
        created_ts REAL,
        updated_ts REAL,
        mode TEXT,
        venue TEXT,
        symbol TEXT,
        side TEXT,
        order_type TEXT,
        amount REAL,
        price REAL,
        status TEXT,
        client_oid TEXT,
        order_id TEXT,
        last_error TEXT,
        meta_json TEXT
    )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_intents_status_updated ON intents(status, updated_ts)")
    con.commit()
    return con

def now() -> float:
    return time.time()

def create_intent(*, intent_id: str, mode: str, venue: str, symbol: str, side: str, order_type: str,
                  amount: float, price: float | None = None, meta: dict | None = None) -> dict[str, Any]:
    con = _connect()
    ts = now()
    mjs = json.dumps(meta or {}, ensure_ascii=False)
    with con:
        con.execute(
            "INSERT OR REPLACE INTO intents (intent_id,created_ts,updated_ts,mode,venue,symbol,side,order_type,amount,price,status,client_oid,order_id,last_error,meta_json) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (intent_id, ts, ts, str(mode), str(venue), str(symbol), str(side), str(order_type),
             float(amount), float(price or 0.0), "READY", None, None, None, mjs)
        )
    return {"ok": True, "intent_id": intent_id, "db": str(DB_PATH)}

def get_intent(intent_id: str) -> dict[str, Any] | None:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT intent_id,created_ts,updated_ts,mode,venue,symbol,side,order_type,amount,price,status,client_oid,order_id,last_error,meta_json FROM intents WHERE intent_id=?", (intent_id,))
    row = cur.fetchone()
    if not row:
        return None
    keys = ["intent_id","created_ts","updated_ts","mode","venue","symbol","side","order_type","amount","price","status","client_oid","order_id","last_error","meta_json"]
    d = dict(zip(keys, row))
    try:
        d["meta"] = json.loads(d.get("meta_json") or "{}")
    except Exception:
        d["meta"] = {}
    return d

def list_intents(limit: int = 200) -> list[dict[str, Any]]:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT intent_id,created_ts,updated_ts,mode,venue,symbol,side,order_type,amount,price,status,client_oid,order_id,last_error,meta_json FROM intents ORDER BY updated_ts DESC LIMIT ?", (int(limit),))
    rows = cur.fetchall()
    out = []
    keys = ["intent_id","created_ts","updated_ts","mode","venue","symbol","side","order_type","amount","price","status","client_oid","order_id","last_error","meta_json"]
    for r in rows:
        d = dict(zip(keys, r))
        try:
            d["meta"] = json.loads(d.get("meta_json") or "{}")
        except Exception:
            d["meta"] = {}
        out.append(d)
    return out

def claim_next_ready(*, venue: str | None = None, mode: str | None = None) -> dict[str, Any] | None:
    con = _connect()
    cur = con.cursor()

    if venue and mode:
        cur.execute("SELECT intent_id FROM intents WHERE status='READY' AND venue=? AND mode=? ORDER BY created_ts ASC LIMIT 1", (str(venue), str(mode)))
    elif venue:
        cur.execute("SELECT intent_id FROM intents WHERE status='READY' AND venue=? ORDER BY created_ts ASC LIMIT 1", (str(venue),))
    elif mode:
        cur.execute("SELECT intent_id FROM intents WHERE status='READY' AND mode=? ORDER BY created_ts ASC LIMIT 1", (str(mode),))
    else:
        cur.execute("SELECT intent_id FROM intents WHERE status='READY' ORDER BY created_ts ASC LIMIT 1")

    row = cur.fetchone()
    if not row:
        return None

    intent_id = row[0]
    ts = now()
    with con:
        cur2 = con.execute(
            "UPDATE intents SET status='SENDING', updated_ts=? WHERE intent_id=? AND status='READY'",
            (ts, intent_id),
        )
        if int(cur2.rowcount or 0) != 1:
            return None
    return get_intent(intent_id)

def update_intent(*, intent_id: str, status: str | None = None, client_oid: str | None = None,
                  order_id: str | None = None, last_error: str | None = None) -> dict[str, Any]:
    con = _connect()
    ts = now()
    fields = []
    vals: list[Any] = []
    if status is not None:
        fields.append("status=?"); vals.append(str(status))
    if client_oid is not None:
        fields.append("client_oid=?"); vals.append(str(client_oid))
    if order_id is not None:
        fields.append("order_id=?"); vals.append(str(order_id))
    if last_error is not None:
        fields.append("last_error=?"); vals.append(str(last_error))
    fields.append("updated_ts=?"); vals.append(ts)
    vals.append(str(intent_id))
    with con:
        con.execute(f"UPDATE intents SET {', '.join(fields)} WHERE intent_id=?", tuple(vals))
    return {"ok": True, "intent_id": intent_id, "db": str(DB_PATH)}

def active_counts() -> dict[str, Any]:
    con = _connect()
    cur = con.cursor()
    cur.execute("SELECT status, COUNT(*) FROM intents GROUP BY status")
    rows = cur.fetchall()
    return {"ok": True, "counts": {r[0]: int(r[1]) for r in rows}, "db": str(DB_PATH)}
