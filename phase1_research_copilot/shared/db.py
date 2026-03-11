from __future__ import annotations

from typing import Any

import psycopg
from psycopg.rows import dict_row


class Database:
    def __init__(self, dsn: str):
        self._dsn = dsn

    def execute(self, sql: str, params: tuple[Any, ...] | None = None) -> None:
        with psycopg.connect(self._dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())

    def fetch_one(self, sql: str, params: tuple[Any, ...] | None = None) -> dict[str, Any] | None:
        with psycopg.connect(self._dsn, autocommit=True, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                row = cur.fetchone()
                return dict(row) if row else None

    def fetch_all(self, sql: str, params: tuple[Any, ...] | None = None) -> list[dict[str, Any]]:
        with psycopg.connect(self._dsn, autocommit=True, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or ())
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def health(self) -> dict[str, Any]:
        row = self.fetch_one("SELECT 1 AS ok")
        return {"ok": bool(row and row.get("ok") == 1)}
