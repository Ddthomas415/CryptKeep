from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class MarketStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.path), check_same_thread=False, isolation_level=None)
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        return con

    def _ensure(self) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS market_tickers(
                  ts_ms INTEGER NOT NULL,
                  exchange TEXT NOT NULL,
                  symbol TEXT NOT NULL,
                  bid REAL,
                  ask REAL,
                  last REAL,
                  base_vol REAL,
                  quote_vol REAL,
                  PRIMARY KEY(exchange, symbol, ts_ms)
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_market_tickers_latest ON market_tickers(exchange, symbol, ts_ms DESC)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS market_ohlcv(
                  ts_ms INTEGER NOT NULL,
                  exchange TEXT NOT NULL,
                  symbol TEXT NOT NULL,
                  timeframe TEXT NOT NULL,
                  o REAL NOT NULL,
                  h REAL NOT NULL,
                  l REAL NOT NULL,
                  cl REAL NOT NULL,
                  v REAL,
                  PRIMARY KEY(exchange, symbol, timeframe, ts_ms)
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_market_ohlcv_latest ON market_ohlcv(exchange, symbol, timeframe, ts_ms DESC)")
        finally:
            con.close()

    def upsert_ticker(
        self,
        *,
        ts_ms: int,
        exchange: str,
        symbol: str,
        bid: float | None,
        ask: float | None,
        last: float | None,
        base_vol: float | None = None,
        quote_vol: float | None = None,
    ) -> None:
        con = self._connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO market_tickers(ts_ms, exchange, symbol, bid, ask, last, base_vol, quote_vol) VALUES(?,?,?,?,?,?,?,?)",
                (int(ts_ms), str(exchange), str(symbol), bid, ask, last, base_vol, quote_vol),
            )
        finally:
            con.close()

    def upsert_ohlcv(
        self,
        *,
        ts_ms: int,
        exchange: str,
        symbol: str,
        timeframe: str,
        o: float,
        h: float,
        l: float,
        cl: float,
        v: float | None = None,
    ) -> None:
        con = self._connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO market_ohlcv(ts_ms, exchange, symbol, timeframe, o, h, l, cl, v) VALUES(?,?,?,?,?,?,?,?,?)",
                (int(ts_ms), str(exchange), str(symbol), str(timeframe), float(o), float(h), float(l), float(cl), v),
            )
        finally:
            con.close()

    def last_tickers(self, *, exchange: str, symbol: str, limit: int = 1) -> list[dict[str, Any]]:
        con = self._connect()
        try:
            rows = con.execute(
                "SELECT ts_ms, exchange, symbol, bid, ask, last, base_vol, quote_vol FROM market_tickers WHERE exchange=? AND symbol=? ORDER BY ts_ms DESC LIMIT ?",
                (str(exchange), str(symbol), int(limit)),
            ).fetchall()
        finally:
            con.close()
        return [
            {
                "ts_ms": int(r[0]),
                "exchange": str(r[1]),
                "symbol": str(r[2]),
                "bid": r[3],
                "ask": r[4],
                "last": r[5],
                "base_vol": r[6],
                "quote_vol": r[7],
            }
            for r in rows
        ]
