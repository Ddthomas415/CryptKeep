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
        finally:
            con.close()

    def upsert_cash(self, *, exchange: str, cash: float) -> None:
        con = self._connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO portfolio_cash(exchange, cash, updated_ts) VALUES(?,?,?)",
                (str(exchange), float(cash), _now()),
            )
        finally:
            con.close()

    def get_cash(self, exchange: str) -> dict[str, Any] | None:
        con = self._connect()
        try:
            row = con.execute("SELECT exchange, cash, updated_ts FROM portfolio_cash WHERE exchange=?", (str(exchange),)).fetchone()
        finally:
            con.close()
        if not row:
            return None
        return {"exchange": str(row[0]), "cash": float(row[1]), "updated_ts": str(row[2])}

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
