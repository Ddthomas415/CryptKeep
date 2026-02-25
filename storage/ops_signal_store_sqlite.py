from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Optional

from services.ops.risk_gate_contract import RawSignalSnapshot, RiskGateSignal
from services.os.app_paths import data_dir, ensure_dirs


def _conn(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    c = sqlite3.connect(path, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL;")
    c.execute("PRAGMA synchronous=NORMAL;")
    return c


DDL = """
CREATE TABLE IF NOT EXISTS ops_raw_signal_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  source TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ops_raw_signal_ts
  ON ops_raw_signal_snapshots(ts DESC);

CREATE TABLE IF NOT EXISTS ops_risk_gate_signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  source TEXT NOT NULL,
  gate_state TEXT NOT NULL,
  system_stress REAL NOT NULL,
  regime TEXT NOT NULL,
  zone TEXT NOT NULL,
  hazards_json TEXT NOT NULL,
  reasons_json TEXT NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ops_risk_gate_ts
  ON ops_risk_gate_signals(ts DESC);
"""


@dataclass
class OpsSignalStoreSQLite:
    path: str = ""

    def __post_init__(self) -> None:
        if not self.path:
            ensure_dirs()
            self.path = str(data_dir() / "ops_intel.sqlite")
        with _conn(self.path) as c:
            c.executescript(DDL)
            c.commit()

    def insert_raw_signal(self, snapshot: RawSignalSnapshot | Dict[str, Any]) -> int:
        snap = snapshot if isinstance(snapshot, RawSignalSnapshot) else RawSignalSnapshot.from_dict(snapshot)
        payload = snap.to_dict()
        with _conn(self.path) as c:
            cur = c.execute(
                """
                INSERT INTO ops_raw_signal_snapshots(ts, source, payload_json)
                VALUES(?,?,?)
                """,
                (snap.ts, snap.source, json.dumps(payload, default=str)),
            )
            c.commit()
            return int(cur.lastrowid or 0)

    def insert_risk_gate(self, signal: RiskGateSignal | Dict[str, Any]) -> int:
        gate = signal if isinstance(signal, RiskGateSignal) else RiskGateSignal.from_dict(signal)
        payload = gate.to_dict()
        with _conn(self.path) as c:
            cur = c.execute(
                """
                INSERT INTO ops_risk_gate_signals(
                  ts, source, gate_state, system_stress, regime, zone, hazards_json, reasons_json, payload_json
                ) VALUES(?,?,?,?,?,?,?,?,?)
                """,
                (
                    gate.ts,
                    gate.source,
                    gate.gate_state.value,
                    float(gate.system_stress),
                    gate.regime,
                    gate.zone,
                    json.dumps(list(gate.hazards), default=str),
                    json.dumps(list(gate.reasons), default=str),
                    json.dumps(payload, default=str),
                ),
            )
            c.commit()
            return int(cur.lastrowid or 0)

    def latest_raw_signal(self) -> Optional[Dict[str, Any]]:
        with _conn(self.path) as c:
            row = c.execute(
                "SELECT payload_json FROM ops_raw_signal_snapshots ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if not row:
            return None
        return dict(json.loads(str(row["payload_json"])))

    def latest_risk_gate(self) -> Optional[Dict[str, Any]]:
        with _conn(self.path) as c:
            row = c.execute(
                "SELECT payload_json FROM ops_risk_gate_signals ORDER BY id DESC LIMIT 1"
            ).fetchone()
        if not row:
            return None
        return dict(json.loads(str(row["payload_json"])))

