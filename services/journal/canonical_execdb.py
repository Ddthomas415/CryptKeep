from __future__ import annotations

import datetime
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# CBP_CANONICAL_EXECDB_V1
#
# Minimal canonical journal backed by exec_db.
# Idempotent on (venue, fill_id) so replays are safe.

def _utc_iso() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"

@dataclass
class CanonicalJournal:
    exec_db: str

    def __post_init__(self) -> None:
        Path(self.exec_db).parent.mkdir(parents=True, exist_ok=True)

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.exec_db)
        c.row_factory = sqlite3.Row
        return c

    def ensure_schema(self) -> None:
        with self._conn() as c:
            c.execute("""
            CREATE TABLE IF NOT EXISTS canonical_fills(
              venue TEXT NOT NULL,
              fill_id TEXT NOT NULL,
              symbol TEXT NOT NULL,
              side TEXT NOT NULL,
              qty REAL NOT NULL,
              price REAL NOT NULL,
              ts TEXT NOT NULL,
              fee_usd REAL NOT NULL DEFAULT 0,
              realized_pnl_usd REAL,
              client_order_id TEXT,
              order_id TEXT,
              raw_json TEXT,
              created_at TEXT NOT NULL,
              PRIMARY KEY(venue, fill_id)
            );
            """)

    def record_fill(
        self,
        *,
        venue: str,
        fill_id: str,
        symbol: str,
        side: str,
        qty: float,
        price: float,
        ts: Any,
        fee_usd: float = 0.0,
        realized_pnl_usd: Optional[float] = None,
        client_order_id: str = "",
        order_id: str = "",
        raw: Any = None,
    ) -> None:
        self.ensure_schema()
        raw_json = None
        try:
            if raw is not None:
                raw_json = json.dumps(raw, ensure_ascii=False, default=str)[:200000]
        except Exception:
            raw_json = None

        with self._conn() as c:
            # INSERT OR IGNORE makes replays safe
            c.execute(
                """
                INSERT OR IGNORE INTO canonical_fills(
                  venue, fill_id, symbol, side, qty, price, ts,
                  fee_usd, realized_pnl_usd, client_order_id, order_id, raw_json, created_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    str(venue), str(fill_id), str(symbol), str(side),
                    float(qty), float(price), str(ts),
                    float(fee_usd), (None if realized_pnl_usd is None else float(realized_pnl_usd)),
                    str(client_order_id or ""), str(order_id or ""),
                    raw_json, _utc_iso(),
                ),
            )
    