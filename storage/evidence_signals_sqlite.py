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

    # Add more methods here if you have them (recent_quarantine, insert_signal, insert_score, etc.)
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