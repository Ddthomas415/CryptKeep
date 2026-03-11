from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from services.os.app_paths import runtime_dir

SNAPSHOT_FILE = runtime_dir() / "snapshots" / "market_data_poller.latest.json"


class SQLiteMarketDataStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def _read_snapshot_file(self, path: Path) -> list[dict[str, Any]]:
        try:
            if not path.exists():
                return []
            obj = json.loads(path.read_text(encoding="utf-8"))
            rows = obj.get("ticks")
            return rows if isinstance(rows, list) else []
        except Exception:
            return []

    def _read_sqlite_latest(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            con = sqlite3.connect(str(self.path))
            rows = con.execute(
                """
                SELECT t.ts_ms, t.exchange, t.symbol, t.bid, t.ask, t.last, t.base_vol, t.quote_vol
                FROM market_tickers t
                JOIN (
                  SELECT exchange, symbol, MAX(ts_ms) AS ts_ms
                  FROM market_tickers
                  GROUP BY exchange, symbol
                ) latest
                ON t.exchange = latest.exchange
               AND t.symbol = latest.symbol
               AND t.ts_ms = latest.ts_ms
                ORDER BY t.exchange ASC, t.symbol ASC
                """
            ).fetchall()
            con.close()
        except Exception:
            return []

        out: list[dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "ts_ms": int(r[0]),
                    "exchange": str(r[1]),
                    "venue": str(r[1]),
                    "symbol": str(r[2]),
                    "bid": r[3],
                    "ask": r[4],
                    "last": r[5],
                    "base_vol": r[6],
                    "quote_vol": r[7],
                }
            )
        return out

    def get_latest_sync(self) -> list[dict[str, Any]]:
        # Preferred: configured sqlite market DB. Fallback: snapshot JSON file.
        rows = self._read_sqlite_latest()
        if rows:
            return rows

        if self.path.suffix.lower() == ".json":
            alt = self._read_snapshot_file(self.path)
            if alt:
                return alt
        return self._read_snapshot_file(SNAPSHOT_FILE)
