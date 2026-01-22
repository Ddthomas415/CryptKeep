from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir

def _try_json(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, (dict, list)):
        return x
    if isinstance(x, (bytes, bytearray)):
        try:
            x = x.decode("utf-8", errors="replace")
        except Exception:
            return {"raw_bytes_len": len(x)}
    if isinstance(x, str):
        s = x.strip()
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                return json.loads(s)
            except Exception:
                return x
    return x

def _find_idempotency_db() -> Path | None:
    d = data_dir()
    if not d.exists():
        return None
    # Prefer obvious names
    cands = list(d.glob("*idempot*.*"))
    # include .db and .sqlite
    cands += list(d.glob("*.db")) + list(d.glob("*.sqlite")) + list(d.glob("*.sqlite3"))
    # Deduplicate
    seen = set()
    uniq = []
    for p in cands:
        if p.is_file():
            k = str(p.resolve())
            if k not in seen:
                seen.add(k)
                uniq.append(p)
    # Heuristic: pick newest file with "idempot" in name first
    idemps = [p for p in uniq if "idempot" in p.name.lower()]
    pool = idemps if idemps else uniq
    if not pool:
        return None
    pool.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return pool[0]

def _guess_table(conn: sqlite3.Connection) -> str | None:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    names = [r[0] for r in rows]
    # prefer tables containing idempot
    for n in names:
        if "idempot" in n.lower():
            return n
    # else fallback to first table
    return names[0] if names else None

def _cols(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r[1] for r in rows]  # name

def _pick(colnames: list[str], options: list[str]) -> str | None:
    low = {c.lower(): c for c in colnames}
    for o in options:
        if o.lower() in low:
            return low[o.lower()]
    # fuzzy: contains
    for c in colnames:
        cl = c.lower()
        for o in options:
            if o.lower() in cl:
                return c
    return None

def _parse_venue_symbol_from_key(key: str) -> dict:
    # best-effort: our idempotency keys often include venue/symbol somewhere
    k = str(key or "")
    out = {"venue": None, "symbol": None}
    # common pattern: venue|symbol|...
    if "|" in k:
        parts = k.split("|")
        if len(parts) >= 2:
            out["venue"] = parts[0].strip().lower() or None
            out["symbol"] = parts[1].strip().upper() or None
    return out

def list_recent(*, limit: int = 50, status: str | None = None) -> dict:
    db = _find_idempotency_db()
    if not db:
        return {"ok": False, "reason": "idempotency_db_not_found", "data_dir": str(data_dir())}

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    try:
        table = _guess_table(conn)
        if not table:
            return {"ok": False, "reason": "no_tables_in_db", "path": str(db)}

        cols = _cols(conn, table)

        c_key = _pick(cols, ["key", "idempotency_key", "idem_key"])
        c_status = _pick(cols, ["status", "state"])
        c_result = _pick(cols, ["result", "payload", "data", "json"])
        c_ts = _pick(cols, ["updated_epoch", "updated_at", "ts", "timestamp", "created_epoch", "created_at"])

        if not c_key:
            return {"ok": False, "reason": "no_key_column", "table": table, "cols": cols, "path": str(db)}

        where = ""
        params = []
        if status and c_status:
            where = f"WHERE {c_status} = ?"
            params.append(status)

        order = ""
        if c_ts:
            order = f"ORDER BY {c_ts} DESC"
        else:
            # fallback to rowid
            order = "ORDER BY rowid DESC"

        q = f"SELECT * FROM {table} {where} {order} LIMIT ?"
        params.append(int(limit))
        rows = conn.execute(q, params).fetchall()

        out = []
        for r in rows:
            rr = dict(r)
            key = rr.get(c_key)
            payload = rr.get(c_result) if c_result else None
            parsed = _try_json(payload)
            vs = _parse_venue_symbol_from_key(str(key))
            out.append({
                "key": key,
                "status": rr.get(c_status) if c_status else None,
                "ts": rr.get(c_ts) if c_ts else None,
                "venue": vs.get("venue"),
                "symbol": vs.get("symbol"),
                "payload": parsed,
                "raw": rr,
            })

        return {"ok": True, "path": str(db), "table": table, "rows": out, "cols": cols}
    finally:
        conn.close()

def filter_rows(rows: list[dict], venue: str | None, symbol: str | None) -> list[dict]:
    v = (venue or "").strip().lower()
    s = (symbol or "").strip().upper()
    out = []
    for r in rows or []:
        rv = (r.get("venue") or "").lower()
        rs = (r.get("symbol") or "").upper()
        if v and rv != v:
            continue
        if s and rs != s:
            continue
        out.append(r)
    return out
