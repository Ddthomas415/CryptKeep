from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class SQLiteReconciliationStore:
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
                CREATE TABLE IF NOT EXISTS reconciliation_balance_snapshots(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts_ms INTEGER NOT NULL,
                  exchange TEXT NOT NULL,
                  quote_ccy TEXT NOT NULL,
                  payload_json TEXT NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_recon_balance_ts ON reconciliation_balance_snapshots(exchange, ts_ms DESC)")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS reconciliation_drift_reports(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts_ms INTEGER NOT NULL,
                  exchange TEXT NOT NULL,
                  severity TEXT NOT NULL,
                  summary TEXT NOT NULL,
                  payload_json TEXT NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_recon_drift_ts ON reconciliation_drift_reports(exchange, ts_ms DESC)")
        finally:
            con.close()

    def insert_balance_snapshot(self, ts_ms: int, exchange: str, quote_ccy: str, payload: dict[str, Any]) -> None:
        con = self._connect()
        try:
            con.execute(
                "INSERT INTO reconciliation_balance_snapshots(ts_ms, exchange, quote_ccy, payload_json) VALUES(?,?,?,?)",
                (int(ts_ms), str(exchange), str(quote_ccy), json.dumps(payload or {}, sort_keys=True)),
            )
        finally:
            con.close()

    def insert_drift_report(self, ts_ms: int, exchange: str, severity: str, summary: str, payload: dict[str, Any]) -> None:
        con = self._connect()
        try:
            con.execute(
                "INSERT INTO reconciliation_drift_reports(ts_ms, exchange, severity, summary, payload_json) VALUES(?,?,?,?,?)",
                (int(ts_ms), str(exchange), str(severity), str(summary), json.dumps(payload or {}, sort_keys=True)),
            )
        finally:
            con.close()

    def list_drift_reports(self, exchange: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        con = self._connect()
        try:
            if exchange:
                rows = con.execute(
                    "SELECT ts_ms, exchange, severity, summary, payload_json FROM reconciliation_drift_reports WHERE exchange=? ORDER BY ts_ms DESC LIMIT ?",
                    (str(exchange), int(limit)),
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT ts_ms, exchange, severity, summary, payload_json FROM reconciliation_drift_reports ORDER BY ts_ms DESC LIMIT ?",
                    (int(limit),),
                ).fetchall()
        finally:
            con.close()
        out: list[dict[str, Any]] = []
        for r in rows:
            try:
                payload = json.loads(r[4] or "{}")
            except Exception:
                payload = {}
            out.append({"ts_ms": int(r[0]), "exchange": str(r[1]), "severity": str(r[2]), "summary": str(r[3]), "payload": payload})
        return out
