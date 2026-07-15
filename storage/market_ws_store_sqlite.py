from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path
from typing import Any, Dict

from services.markets.math_utils import decimal_value
from services.os.app_paths import runtime_dir, ensure_dirs

ensure_dirs()
DEFAULT_DB = runtime_dir() / "market_ws.sqlite"


def _required_ts_ms(value: Any) -> int:
    try:
        out = int(value)
    except Exception as exc:
        raise ValueError("invalid_market_ws_latency_numeric:ts_ms") from exc
    if out <= 0:
        raise ValueError("invalid_market_ws_latency_numeric:ts_ms")
    return out


def _required_value_ms(value: Any) -> float:
    try:
        out = float(decimal_value(value, name="value_ms"))
    except (OverflowError, ValueError) as exc:
        raise ValueError("invalid_market_ws_latency_numeric:value_ms") from exc
    if not math.isfinite(out) or out < 0.0:
        raise ValueError("invalid_market_ws_latency_numeric:value_ms")
    return out


class SQLiteMarketWsStore:
    def __init__(self, path: Path | str | None = None):
        self.db_path = Path(path) if path else DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        return con

    def _ensure(self) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS market_ws_latency (
                    ts_ms INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    value_ms REAL NOT NULL,
                    meta_json TEXT
                )
                """
            )
        finally:
            con.close()

    def log_latency(
        self,
        *,
        ts_ms: int,
        category: str,
        name: str,
        value_ms: float,
        meta: Dict[str, Any] | None = None,
    ) -> None:
        ts = _required_ts_ms(ts_ms)
        value = _required_value_ms(value_ms)
        con = self._connect()
        try:
            con.execute(
                "INSERT INTO market_ws_latency(ts_ms, category, name, value_ms, meta_json) VALUES(?,?,?,?,?)",
                (
                    ts,
                    str(category),
                    str(name),
                    value,
                    json.dumps(meta or {}, ensure_ascii=False),
                ),
            )
        finally:
            con.close()
