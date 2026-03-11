from __future__ import annotations
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from services.os.app_paths import data_dir
from typing import Optional, List, Dict, Any

DB_PATH = data_dir() / "evidence_signals.sqlite"

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS evidence_sources (
  source_id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL, -- 'manual' | 'file' | 'webhook' | 'partner'
  display_name TEXT NOT NULL,
  consent_confirmed INTEGER NOT NULL DEFAULT 0,
  created_ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evidence_events_raw (
  event_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  received_ts TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  FOREIGN KEY(source_id) REFERENCES evidence_sources(source_id)
);
CREATE TABLE IF NOT EXISTS evidence_quarantine (
  quarantine_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  received_ts TEXT NOT NULL,
  reason TEXT NOT NULL, -- why it was quarantined
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued', -- queued|reviewed|normalized|rejected
  reviewed_ts TEXT,
  normalized_signal_id TEXT,
  FOREIGN KEY(event_id) REFERENCES evidence_events_raw(event_id),
  FOREIGN KEY(source_id) REFERENCES evidence_sources(source_id)
);
CREATE INDEX IF NOT EXISTS idx_eq_status_ts ON evidence_quarantine(status, received_ts);
CREATE TABLE IF NOT EXISTS evidence_signals (
  signal_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL,
  source_id TEXT NOT NULL,
  ts TEXT NOT NULL, -- ISO timestamp of the signal as provided
  venue TEXT, -- optional
  symbol TEXT NOT NULL, -- normalized "BTC/USDT" style where possible
  side TEXT NOT NULL, -- 'buy'|'sell'|'long'|'short'|'flat'
  confidence REAL, -- optional 0..1
  size_hint REAL, -- optional
  horizon_sec INTEGER, -- optional evaluation horizon
  notes TEXT,
  status TEXT NOT NULL DEFAULT 'ingested',-- 'ingested'|'scored'|'rejected'
  created_ts TEXT NOT NULL,
  FOREIGN KEY(event_id) REFERENCES evidence_events_raw(event_id),
  FOREIGN KEY(source_id) REFERENCES evidence_sources(source_id)
);
CREATE INDEX IF NOT EXISTS idx_es_ts ON evidence_signals(ts);
CREATE INDEX IF NOT EXISTS idx_es_symbol ON evidence_signals(symbol);
CREATE INDEX IF NOT EXISTS idx_es_source ON evidence_signals(source_id);
CREATE TABLE IF NOT EXISTS evidence_scores (
  score_id TEXT PRIMARY KEY,
  signal_id TEXT NOT NULL,
  scored_ts TEXT NOT NULL,
  method TEXT NOT NULL, -- e.g. 'forward_return'
  horizon_sec INTEGER NOT NULL,
  forward_return REAL, -- e.g. +0.0123
  label INTEGER, -- 1 good, 0 neutral, -1 bad (optional)
  details_json TEXT,
  FOREIGN KEY(signal_id) REFERENCES evidence_signals(signal_id)
);
CREATE INDEX IF NOT EXISTS idx_score_signal ON evidence_scores(signal_id);
"""

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, isolation_level=None, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    for stmt in SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    return con

class EvidenceSignalsSQLite:
    def __init__(self) -> None:
        _connect().close()  # initialize DB if needed

    def upsert_source(self, source_id: str, source_type: str, display_name: str, consent_confirmed: bool) -> Dict[str, Any]:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO evidence_sources(source_id, source_type, display_name, consent_confirmed, created_ts) VALUES(?,?,?,?,?)",
                (str(source_id), str(source_type), str(display_name), 1 if consent_confirmed else 0, _now()),
            )
        finally:
            con.close()
        return {"source_id": source_id, "source_type": source_type, "display_name": display_name, "consent_confirmed": bool(consent_confirmed)}

    def get_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT source_id, source_type, display_name, consent_confirmed, created_ts FROM evidence_sources WHERE source_id=?",
                (str(source_id),),
            ).fetchone()
            if not r:
                return None
            return {
                "source_id": r[0],
                "source_type": r[1],
                "display_name": r[2],
                "consent_confirmed": bool(int(r[3])),
                "created_ts": r[4],
            }
        finally:
            con.close()

    def insert_raw_event(self, event_id: str, source_id: str, payload_json: str) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO evidence_events_raw(event_id, source_id, received_ts, payload_json) VALUES(?,?,?,?)",
                (str(event_id), str(source_id), _now(), str(payload_json)),
            )
        finally:
            con.close()

    def insert_quarantine(self, quarantine_id: str, event_id: str, source_id: str, reason: str, payload_json: str) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO evidence_quarantine(quarantine_id, event_id, source_id, received_ts, reason, payload_json, status) VALUES(?,?,?,?,?,?,?)",
                (str(quarantine_id), str(event_id), str(source_id), _now(), str(reason), str(payload_json), "queued"),
            )
        finally:
            con.close()

    def update_quarantine(self, quarantine_id: str, *, status: str, reviewed_ts: str | None = None, normalized_signal_id: str | None = None) -> None:
        con = _connect()
        try:
            con.execute(
                "UPDATE evidence_quarantine SET status=?, reviewed_ts=?, normalized_signal_id=? WHERE quarantine_id=?",
                (str(status), reviewed_ts, normalized_signal_id, str(quarantine_id)),
            )
        finally:
            con.close()

    def insert_signal(
        self,
        *,
        signal_id: str,
        event_id: str,
        source_id: str,
        ts: str,
        symbol: str,
        side: str,
        venue: str | None = None,
        confidence: float | None = None,
        size_hint: float | None = None,
        horizon_sec: int | None = None,
        notes: str | None = None,
        status: str = "ingested",
    ) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO evidence_signals(signal_id, event_id, source_id, ts, venue, symbol, side, confidence, size_hint, horizon_sec, notes, status, created_ts) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    str(signal_id),
                    str(event_id),
                    str(source_id),
                    str(ts),
                    None if venue is None else str(venue),
                    str(symbol),
                    str(side),
                    None if confidence is None else float(confidence),
                    None if size_hint is None else float(size_hint),
                    None if horizon_sec is None else int(horizon_sec),
                    None if notes is None else str(notes),
                    str(status),
                    _now(),
                ),
            )
        finally:
            con.close()

    def get_signal(self, signal_id: str) -> Optional[Dict[str, Any]]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT signal_id, event_id, source_id, ts, venue, symbol, side, confidence, size_hint, horizon_sec, notes, status, created_ts "
                "FROM evidence_signals WHERE signal_id=?",
                (str(signal_id),),
            ).fetchone()
            if not r:
                return None
            return {
                "signal_id": r[0],
                "event_id": r[1],
                "source_id": r[2],
                "ts": r[3],
                "venue": r[4],
                "symbol": r[5],
                "side": r[6],
                "confidence": r[7],
                "size_hint": r[8],
                "horizon_sec": r[9],
                "notes": r[10],
                "status": r[11],
                "created_ts": r[12],
            }
        finally:
            con.close()

    def recent_signals(self, limit: int = 200, source_id: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = (
                "SELECT signal_id, event_id, source_id, ts, venue, symbol, side, confidence, size_hint, horizon_sec, notes, status, created_ts "
                "FROM evidence_signals"
            )
            args: list[Any] = []
            if source_id:
                q += " WHERE source_id=?"
                args.append(str(source_id))
            q += " ORDER BY ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [
                {
                    "signal_id": r[0],
                    "event_id": r[1],
                    "source_id": r[2],
                    "ts": r[3],
                    "venue": r[4],
                    "symbol": r[5],
                    "side": r[6],
                    "confidence": r[7],
                    "size_hint": r[8],
                    "horizon_sec": r[9],
                    "notes": r[10],
                    "status": r[11],
                    "created_ts": r[12],
                }
                for r in rows
            ]
        finally:
            con.close()

    def insert_score(
        self,
        *,
        score_id: str,
        signal_id: str,
        method: str,
        horizon_sec: int,
        forward_return: float | None = None,
        label: int | None = None,
        details_json: str | None = None,
        scored_ts: str | None = None,
    ) -> None:
        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO evidence_scores(score_id, signal_id, scored_ts, method, horizon_sec, forward_return, label, details_json) VALUES(?,?,?,?,?,?,?,?)",
                (
                    str(score_id),
                    str(signal_id),
                    str(scored_ts or _now()),
                    str(method),
                    int(horizon_sec),
                    None if forward_return is None else float(forward_return),
                    None if label is None else int(label),
                    details_json,
                ),
            )
        finally:
            con.close()

    def recent_quarantine(self, limit: int = 200, status: str | None = None) -> List[Dict[str, Any]]:
        con = _connect()
        try:
            q = "SELECT quarantine_id, event_id, source_id, received_ts, reason, status, reviewed_ts, normalized_signal_id FROM evidence_quarantine"
            args = []
            if status:
                q += " WHERE status=?"
                args.append(str(status))
            q += " ORDER BY received_ts DESC LIMIT ?"
            args.append(int(limit))
            rows = con.execute(q, tuple(args)).fetchall()
            return [
                {
                    "quarantine_id": r[0],
                    "event_id": r[1],
                    "source_id": r[2],
                    "received_ts": r[3],
                    "reason": r[4],
                    "status": r[5],
                    "reviewed_ts": r[6],
                    "normalized_signal_id": r[7],
                }
                for r in rows
            ]
        finally:
            con.close()

    def get_quarantine(self, quarantine_id: str) -> Optional[Dict[str, Any]]:
        con = _connect()
        try:
            r = con.execute(
                "SELECT quarantine_id, event_id, source_id, received_ts, reason, payload_json, status, reviewed_ts, normalized_signal_id "
                "FROM evidence_quarantine WHERE quarantine_id=?",
                (str(quarantine_id),),
            ).fetchone()
            if not r:
                return None
            return {
                "quarantine_id": r[0],
                "event_id": r[1],
                "source_id": r[2],
                "received_ts": r[3],
                "reason": r[4],
                "payload_json": r[5],
                "status": r[6],
                "reviewed_ts": r[7],
                "normalized_signal_id": r[8],
            }
        finally:
            con.close()
