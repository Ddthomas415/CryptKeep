from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StrategyStateStore:
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
                CREATE TABLE IF NOT EXISTS strategy_state(
                  strategy_id TEXT NOT NULL,
                  exchange TEXT NOT NULL,
                  symbol TEXT NOT NULL,
                  timeframe TEXT NOT NULL,
                  last_bar_ts_ms INTEGER,
                  last_signal TEXT,
                  last_intent_id TEXT,
                  meta_json TEXT,
                  updated_ts TEXT NOT NULL,
                  PRIMARY KEY(strategy_id, exchange, symbol, timeframe)
                );
                """
            )

    def get(self, *, strategy_id: str, exchange: str, symbol: str, timeframe: str) -> dict[str, Any] | None:
        with self._conn() as con:
            row = con.execute(
                "SELECT strategy_id, exchange, symbol, timeframe, last_bar_ts_ms, last_signal, last_intent_id, meta_json, updated_ts "
                "FROM strategy_state WHERE strategy_id=? AND exchange=? AND symbol=? AND timeframe=?",
                (str(strategy_id), str(exchange), str(symbol), str(timeframe)),
            ).fetchone()
        if not row:
            return None
        return {
            "strategy_id": row["strategy_id"],
            "exchange": row["exchange"],
            "symbol": row["symbol"],
            "timeframe": row["timeframe"],
            "last_bar_ts_ms": row["last_bar_ts_ms"],
            "last_signal": row["last_signal"],
            "last_intent_id": row["last_intent_id"],
            "meta_json": row["meta_json"],
            "updated_ts": row["updated_ts"],
        }

    def upsert(
        self,
        *,
        strategy_id: str,
        exchange: str,
        symbol: str,
        timeframe: str,
        last_bar_ts_ms: int | None,
        last_signal: str | None,
        last_intent_id: str | None,
        meta_json: str | None,
    ) -> None:
        with self._conn() as con:
            con.execute(
                "INSERT OR REPLACE INTO strategy_state(strategy_id, exchange, symbol, timeframe, last_bar_ts_ms, last_signal, last_intent_id, meta_json, updated_ts) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    str(strategy_id),
                    str(exchange),
                    str(symbol),
                    str(timeframe),
                    None if last_bar_ts_ms is None else int(last_bar_ts_ms),
                    last_signal,
                    last_intent_id,
                    meta_json,
                    _now(),
                ),
            )
