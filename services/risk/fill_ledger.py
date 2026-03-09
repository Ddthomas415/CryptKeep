from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FillLedgerDB:
    def __init__(self, exec_db: str):
        self.exec_db = str(exec_db)
        Path(self.exec_db).parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _conn(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.exec_db)
        con.row_factory = sqlite3.Row
        return con

    def _ensure(self) -> None:
        with self._conn() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS fill_ledger(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts TEXT NOT NULL,
                  symbol TEXT NOT NULL,
                  realized_pnl_usd REAL NOT NULL DEFAULT 0,
                  fee_usd REAL NOT NULL DEFAULT 0,
                  meta_json TEXT NOT NULL DEFAULT '{}'
                );
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_fill_ledger_ts ON fill_ledger(ts)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_fill_ledger_symbol ON fill_ledger(symbol)")

    def insert_fill(
        self,
        *,
        symbol: str,
        realized_pnl_usd: float = 0.0,
        fee_usd: float = 0.0,
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload = json.dumps(meta or {}, sort_keys=True)
        with self._conn() as con:
            cur = con.execute(
                "INSERT INTO fill_ledger(ts, symbol, realized_pnl_usd, fee_usd, meta_json) VALUES(?,?,?,?,?)",
                (_now(), str(symbol), float(realized_pnl_usd or 0.0), float(fee_usd or 0.0), payload),
            )
            row_id = int(cur.lastrowid)
        return {"ok": True, "id": row_id, "symbol": str(symbol)}

    def list_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._conn() as con:
            rows = con.execute(
                "SELECT id, ts, symbol, realized_pnl_usd, fee_usd, meta_json FROM fill_ledger ORDER BY id DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            try:
                meta = json.loads(row["meta_json"] or "{}")
            except Exception:
                meta = {}
            out.append(
                {
                    "id": int(row["id"]),
                    "ts": str(row["ts"]),
                    "symbol": str(row["symbol"]),
                    "realized_pnl_usd": float(row["realized_pnl_usd"] or 0.0),
                    "fee_usd": float(row["fee_usd"] or 0.0),
                    "meta": meta,
                }
            )
        return out
