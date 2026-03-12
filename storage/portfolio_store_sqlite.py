from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLitePortfolioStore:
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
                CREATE TABLE IF NOT EXISTS portfolio_cash(
                  exchange TEXT PRIMARY KEY,
                  cash REAL NOT NULL,
                  updated_ts TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolio_positions(
                  exchange TEXT NOT NULL,
                  symbol TEXT NOT NULL,
                  qty REAL NOT NULL,
                  updated_ts TEXT NOT NULL,
                  PRIMARY KEY(exchange, symbol)
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolio_cash_v2(
                  exchange TEXT NOT NULL,
                  quote_ccy TEXT NOT NULL,
                  cash REAL NOT NULL,
                  updated_ts TEXT NOT NULL,
                  PRIMARY KEY(exchange, quote_ccy)
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_cash_v2_exchange ON portfolio_cash_v2(exchange)")
        finally:
            con.close()

    def upsert_cash(self, *, exchange: str, cash: float, quote_ccy: str = "USD") -> None:
        con = self._connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO portfolio_cash(exchange, cash, updated_ts) VALUES(?,?,?)",
                (str(exchange), float(cash), _now()),
            )
            con.execute(
                "INSERT OR REPLACE INTO portfolio_cash_v2(exchange, quote_ccy, cash, updated_ts) VALUES(?,?,?,?)",
                (str(exchange), str(quote_ccy).upper().strip(), float(cash), _now()),
            )
        finally:
            con.close()

    def upsert_cash_quote(self, *, exchange: str, quote_ccy: str, cash: float) -> None:
        q = str(quote_ccy).upper().strip()
        if not q:
            raise ValueError("quote_ccy required")
        con = self._connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO portfolio_cash_v2(exchange, quote_ccy, cash, updated_ts) VALUES(?,?,?,?)",
                (str(exchange), q, float(cash), _now()),
            )
        finally:
            con.close()

    def get_cash_quote(self, exchange: str, quote_ccy: str) -> dict[str, Any] | None:
        q = str(quote_ccy).upper().strip()
        if not q:
            return None
        con = self._connect()
        try:
            row = con.execute(
                "SELECT exchange, quote_ccy, cash, updated_ts FROM portfolio_cash_v2 WHERE exchange=? AND quote_ccy=?",
                (str(exchange), q),
            ).fetchone()
        finally:
            con.close()
        if not row:
            return None
        return {
            "exchange": str(row[0]),
            "quote_ccy": str(row[1]),
            "cash": float(row[2]),
            "updated_ts": str(row[3]),
        }

    def list_cash_quotes(self, *, exchange: str | None = None) -> list[dict[str, Any]]:
        con = self._connect()
        try:
            if exchange:
                rows = con.execute(
                    "SELECT exchange, quote_ccy, cash, updated_ts FROM portfolio_cash_v2 WHERE exchange=? ORDER BY quote_ccy ASC",
                    (str(exchange),),
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT exchange, quote_ccy, cash, updated_ts FROM portfolio_cash_v2 ORDER BY exchange ASC, quote_ccy ASC"
                ).fetchall()
        finally:
            con.close()
        return [
            {
                "exchange": str(r[0]),
                "quote_ccy": str(r[1]),
                "cash": float(r[2]),
                "updated_ts": str(r[3]),
            }
            for r in rows
        ]

    def get_cash(self, exchange: str, quote_ccy: str | None = None) -> dict[str, Any] | None:
        if quote_ccy:
            return self.get_cash_quote(exchange, str(quote_ccy))

        con = self._connect()
        try:
            row = con.execute("SELECT exchange, cash, updated_ts FROM portfolio_cash WHERE exchange=?", (str(exchange),)).fetchone()
        finally:
            con.close()
        if row:
            return {"exchange": str(row[0]), "cash": float(row[1]), "updated_ts": str(row[2]), "quote_ccy": "USD"}

        v2 = self.list_cash_quotes(exchange=str(exchange))
        if not v2:
            return None
        if len(v2) == 1:
            return dict(v2[0])
        for item in v2:
            if str(item.get("quote_ccy") or "").upper() == "USD":
                return dict(item)
        return dict(v2[0])

    def upsert_position(self, *, exchange: str, symbol: str, qty: float) -> None:
        con = self._connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO portfolio_positions(exchange, symbol, qty, updated_ts) VALUES(?,?,?,?)",
                (str(exchange), str(symbol), float(qty), _now()),
            )
        finally:
            con.close()

    def list_positions(self, exchange: str | None = None) -> list[dict[str, Any]]:
        con = self._connect()
        try:
            if exchange:
                rows = con.execute(
                    "SELECT exchange, symbol, qty, updated_ts FROM portfolio_positions WHERE exchange=? ORDER BY symbol ASC",
                    (str(exchange),),
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT exchange, symbol, qty, updated_ts FROM portfolio_positions ORDER BY exchange ASC, symbol ASC"
                ).fetchall()
        finally:
            con.close()
        return [
            {"exchange": str(r[0]), "symbol": str(r[1]), "qty": float(r[2]), "updated_ts": str(r[3])}
            for r in rows
        ]
