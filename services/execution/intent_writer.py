from __future__ import annotations

import json
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from storage.intent_queue_sqlite import IntentQueueSQLite


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class IntentWriterCfg:
    exec_db: str
    cfg_path: str = "config/trading.yaml"


class IntentWriter:
    def __init__(self, cfg: IntentWriterCfg):
        self.cfg = cfg
        self.exec_db = str(cfg.exec_db)
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
                CREATE TABLE IF NOT EXISTS pipeline_intents(
                  intent_id TEXT PRIMARY KEY,
                  created_ts TEXT NOT NULL,
                  exchange TEXT NOT NULL,
                  symbol TEXT NOT NULL,
                  mode TEXT NOT NULL,
                  side TEXT NOT NULL,
                  qty REAL NOT NULL,
                  order_type TEXT NOT NULL,
                  price REAL,
                  status TEXT NOT NULL,
                  meta_json TEXT NOT NULL DEFAULT '{}'
                );
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_pipeline_intents_created ON pipeline_intents(created_ts)")

    def create_intent(
        self,
        *,
        exchange: str,
        symbol: str,
        mode: str,
        side: str,
        qty: float,
        order_type: str,
        price: float | None,
        meta: dict[str, Any] | None = None,
        status: str = "pending",
        strategy_id: str | None = None,
        source: str = "pipeline",
        enqueue_execution: bool = True,
    ) -> str:
        intent_id = str(uuid.uuid4())
        ts = _now()
        with self._conn() as con:
            con.execute(
                "INSERT INTO pipeline_intents(intent_id, created_ts, exchange, symbol, mode, side, qty, order_type, price, status, meta_json) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (
                    intent_id,
                    ts,
                    str(exchange),
                    str(symbol),
                    str(mode),
                    str(side),
                    float(qty),
                    str(order_type),
                    None if price is None else float(price),
                    str(status),
                    json.dumps(meta or {}, sort_keys=True),
                ),
            )

        if enqueue_execution:
            try:
                IntentQueueSQLite().upsert_intent(
                    {
                        "intent_id": intent_id,
                        "created_ts": ts,
                        "ts": ts,
                        "source": str(source),
                        "strategy_id": strategy_id,
                        "venue": str(exchange),
                        "symbol": str(symbol),
                        "side": str(side),
                        "order_type": str(order_type),
                        "qty": float(qty),
                        "limit_price": (None if price is None else float(price)),
                        "status": "queued",
                        "last_error": None,
                        "client_order_id": None,
                        "linked_order_id": None,
                    }
                )
            except Exception:
                # Keep pipeline intent creation durable even if queue mirror fails.
                pass

        return intent_id

    def get_intent(self, intent_id: str) -> dict[str, Any] | None:
        with self._conn() as con:
            row = con.execute(
                "SELECT intent_id, created_ts, exchange, symbol, mode, side, qty, order_type, price, status, meta_json "
                "FROM pipeline_intents WHERE intent_id=?",
                (str(intent_id),),
            ).fetchone()
        if not row:
            return None
        try:
            meta = json.loads(row["meta_json"] or "{}")
        except Exception:
            meta = {}
        return {
            "intent_id": str(row["intent_id"]),
            "created_ts": str(row["created_ts"]),
            "exchange": str(row["exchange"]),
            "symbol": str(row["symbol"]),
            "mode": str(row["mode"]),
            "side": str(row["side"]),
            "qty": float(row["qty"]),
            "order_type": str(row["order_type"]),
            "price": row["price"],
            "status": str(row["status"]),
            "meta": meta,
        }

    def list_intents(self, *, limit: int = 200, status: str | None = None) -> list[dict[str, Any]]:
        q = (
            "SELECT intent_id, created_ts, exchange, symbol, mode, side, qty, order_type, price, status, meta_json "
            "FROM pipeline_intents"
        )
        args: list[Any] = []
        if status:
            q += " WHERE status=?"
            args.append(str(status))
        q += " ORDER BY created_ts DESC LIMIT ?"
        args.append(int(limit))
        with self._conn() as con:
            rows = con.execute(q, tuple(args)).fetchall()
        out: list[dict[str, Any]] = []
        for row in rows:
            try:
                meta = json.loads(row["meta_json"] or "{}")
            except Exception:
                meta = {}
            out.append(
                {
                    "intent_id": str(row["intent_id"]),
                    "created_ts": str(row["created_ts"]),
                    "exchange": str(row["exchange"]),
                    "symbol": str(row["symbol"]),
                    "mode": str(row["mode"]),
                    "side": str(row["side"]),
                    "qty": float(row["qty"]),
                    "order_type": str(row["order_type"]),
                    "price": row["price"],
                    "status": str(row["status"]),
                    "meta": meta,
                }
            )
        return out

    def mark_status(self, intent_id: str, *, status: str, last_error: str | None = None) -> None:
        with self._conn() as con:
            con.execute(
                "UPDATE pipeline_intents SET status=? WHERE intent_id=?",
                (str(status), str(intent_id)),
            )
        try:
            IntentQueueSQLite().update_status(str(intent_id), str(status), last_error=last_error)
        except Exception:
            pass
