from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from services.ops.risk_gate_contract import RawSignalSnapshot, RiskGateSignal
from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite


@dataclass
class LiveSignalAdapter:
    store: OpsSignalStoreSQLite

    @classmethod
    def from_default_db(cls, path: str = "") -> "LiveSignalAdapter":
        return cls(store=OpsSignalStoreSQLite(path=path))

    def publish_snapshot(self, payload: RawSignalSnapshot | Dict[str, Any]) -> int:
        snap = payload if isinstance(payload, RawSignalSnapshot) else RawSignalSnapshot.from_dict(payload)
        return self.store.insert_raw_signal(snap)

    def publish_risk_gate(self, payload: RiskGateSignal | Dict[str, Any]) -> int:
        gate = payload if isinstance(payload, RiskGateSignal) else RiskGateSignal.from_dict(payload)
        return self.store.insert_risk_gate(gate)

    def publish_snapshot_with_gate(self, payload: RawSignalSnapshot | Dict[str, Any]) -> Dict[str, Any]:
        from services.ops.risk_gate_engine import process_snapshot

        return process_snapshot(payload, store=self.store)

    def latest_risk_gate(self) -> Dict[str, Any] | None:
        return self.store.latest_risk_gate()
