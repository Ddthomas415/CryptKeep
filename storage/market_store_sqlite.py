from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Any

from services.markets.math_utils import decimal_value


def _required_float(value: Any, *, name: str) -> float:
    try:
        out = float(decimal_value(value, name=name))
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"invalid_market_ohlcv_numeric:{name}") from exc
    if not math.isfinite(out):
        raise ValueError(f"invalid_market_ohlcv_numeric:{name}")
    return out


def _optional_float(value: Any, *, name: str) -> float | None:
    if value is None:
        return None
    return _required_float(value, name=name)


def _required_ts_ms(value: Any) -> int:
    try:
        out = int(value)
    except Exception as exc:
        raise ValueError("invalid_market_ohlcv_numeric:ts_ms") from exc
    if out <= 0:
        raise ValueError("invalid_market_ohlcv_numeric:ts_ms")
    return out


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
        ts = _required_ts_ms(ts_ms)
        o_f = _required_float(o, name="o")
        h_f = _required_float(h, name="h")
        l_f = _required_float(l, name="l")
        cl_f = _required_float(cl, name="cl")
        v_f = _optional_float(v, name="v")
        if min(o_f, h_f, l_f, cl_f) <= 0.0:
            raise ValueError("invalid_market_ohlcv_numeric:price_nonpositive")
        if h_f < max(o_f, l_f, cl_f) or l_f > min(o_f, h_f, cl_f):
            raise ValueError("invalid_market_ohlcv_numeric:ohlcv_range")
        if v_f is not None and v_f < 0.0:
            raise ValueError("invalid_market_ohlcv_numeric:v_negative")
        con = self._connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO market_ohlcv(ts_ms, exchange, symbol, timeframe, o, h, l, cl, v) VALUES(?,?,?,?,?,?,?,?,?)",
                (ts, str(exchange), str(symbol), str(timeframe), o_f, h_f, l_f, cl_f, v_f),
            )
        finally:
            con.close()

    def load_ohlcv(
        self,
        *,
        exchange: str,
        symbol: str,
        timeframe: str,
        limit: int = 500,
        since_ms: int | None = None,
    ) -> list[list[Any]]:
        lim = max(1, int(limit))
        con = self._connect()
        try:
            if since_ms is None:
                rows = con.execute(
                    """
                    SELECT ts_ms, o, h, l, cl, v
                    FROM market_ohlcv
                    WHERE exchange=? AND symbol=? AND timeframe=?
                    ORDER BY ts_ms DESC
                    LIMIT ?
                    """,
                    (str(exchange), str(symbol), str(timeframe), lim),
                ).fetchall()
                rows = list(reversed(rows))
            else:
                rows = con.execute(
                    """
                    SELECT ts_ms, o, h, l, cl, v
                    FROM market_ohlcv
                    WHERE exchange=? AND symbol=? AND timeframe=? AND ts_ms>=?
                    ORDER BY ts_ms ASC
                    LIMIT ?
                    """,
                    (str(exchange), str(symbol), str(timeframe), int(since_ms), lim),
                ).fetchall()
        finally:
            con.close()
        return [
            [int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), r[5]]
            for r in rows
        ]

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
