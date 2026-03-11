from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
DB_PATH = data_dir() / "trade_history.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS trade_history (
  trade_id TEXT PRIMARY KEY,
  ts TEXT NOT NULL,
  ts_ms INTEGER NOT NULL,
  venue TEXT NOT NULL,
  symbol TEXT NOT NULL,
  side TEXT NOT NULL,
  qty REAL NOT NULL,
  price REAL NOT NULL,
  fee REAL NOT NULL DEFAULT 0.0,
  fee_ccy TEXT,
  exchange_order_id TEXT,
  client_order_id TEXT,
  status TEXT,
  meta_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_th_ts_ms ON trade_history(ts_ms);
CREATE INDEX IF NOT EXISTS idx_th_venue_symbol_ts ON trade_history(venue, symbol, ts_ms);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path, isolation_level=None, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con


class TradeHistorySQLite:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DB_PATH
        _connect(self.path).close()

    def upsert_trade(self, row: Dict[str, Any]) -> Dict[str, Any]:
        trade_id = str(row.get("trade_id") or row.get("fill_id") or row.get("id") or "")
        if not trade_id:
            raise ValueError("trade_id is required")
        ts = str(row.get("ts") or _now_iso())
        ts_ms = int(row.get("ts_ms") or _now_ms())
        payload = (
            trade_id,
            ts,
            ts_ms,
            str(row.get("venue") or ""),
            str(row.get("symbol") or ""),
            str(row.get("side") or "").lower(),
            float(row.get("qty") or 0.0),
            float(row.get("price") or 0.0),
            float(row.get("fee") or 0.0),
            None if row.get("fee_ccy") is None else str(row.get("fee_ccy")),
            None if row.get("exchange_order_id") is None else str(row.get("exchange_order_id")),
            None if row.get("client_order_id") is None else str(row.get("client_order_id")),
            None if row.get("status") is None else str(row.get("status")),
            json.dumps(row.get("meta") or {}, default=str),
        )
        con = _connect(self.path)
        try:
            con.execute(
                "INSERT OR REPLACE INTO trade_history(trade_id, ts, ts_ms, venue, symbol, side, qty, price, fee, fee_ccy, exchange_order_id, client_order_id, status, meta_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                payload,
            )
        finally:
            con.close()
        return {"ok": True, "trade_id": trade_id}

    def recent(self, *, limit: int = 200, venue: str | None = None, symbol: str | None = None) -> List[Dict[str, Any]]:
        q = (
            "SELECT trade_id, ts, ts_ms, venue, symbol, side, qty, price, fee, fee_ccy, exchange_order_id, client_order_id, status, meta_json "
            "FROM trade_history"
        )
        args: list[Any] = []
        where: list[str] = []
        if venue:
            where.append("venue=?")
            args.append(str(venue))
        if symbol:
            where.append("symbol=?")
            args.append(str(symbol))
        if where:
            q += " WHERE " + " AND ".join(where)
        q += " ORDER BY ts_ms DESC LIMIT ?"
        args.append(int(limit))

        con = _connect(self.path)
        try:
            rows = con.execute(q, tuple(args)).fetchall()
            out: list[dict[str, Any]] = []
            for r in rows:
                meta = {}
                try:
                    meta = json.loads(r["meta_json"] or "{}")
                except Exception:
                    meta = {}
                out.append(
                    {
                        "trade_id": r["trade_id"],
                        "ts": r["ts"],
                        "ts_ms": int(r["ts_ms"]),
                        "venue": r["venue"],
                        "symbol": r["symbol"],
                        "side": r["side"],
                        "qty": float(r["qty"]),
                        "price": float(r["price"]),
                        "fee": float(r["fee"]),
                        "fee_ccy": r["fee_ccy"],
                        "exchange_order_id": r["exchange_order_id"],
                        "client_order_id": r["client_order_id"],
                        "status": r["status"],
                        "meta": meta,
                    }
                )
            return out
        finally:
            con.close()

    def for_order(self, order_id: str) -> List[Dict[str, Any]]:
        return self.recent(limit=2000, venue=None, symbol=None) if not order_id else self._for_order_exact(order_id)

    def _for_order_exact(self, order_id: str) -> List[Dict[str, Any]]:
        con = _connect(self.path)
        try:
            rows = con.execute(
                "SELECT trade_id, ts, ts_ms, venue, symbol, side, qty, price, fee, fee_ccy, exchange_order_id, client_order_id, status, meta_json "
                "FROM trade_history WHERE exchange_order_id=? OR client_order_id=? ORDER BY ts_ms ASC",
                (str(order_id), str(order_id)),
            ).fetchall()
            out: list[dict[str, Any]] = []
            for r in rows:
                try:
                    meta = json.loads(r["meta_json"] or "{}")
                except Exception:
                    meta = {}
                out.append(
                    {
                        "trade_id": r["trade_id"],
                        "ts": r["ts"],
                        "ts_ms": int(r["ts_ms"]),
                        "venue": r["venue"],
                        "symbol": r["symbol"],
                        "side": r["side"],
                        "qty": float(r["qty"]),
                        "price": float(r["price"]),
                        "fee": float(r["fee"]),
                        "fee_ccy": r["fee_ccy"],
                        "exchange_order_id": r["exchange_order_id"],
                        "client_order_id": r["client_order_id"],
                        "status": r["status"],
                        "meta": meta,
                    }
                )
            return out
        finally:
            con.close()
