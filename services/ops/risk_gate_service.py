from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

from services.ops.risk_gate_engine import RiskGateThresholds, decide_gate
from services.os.app_paths import ensure_dirs, runtime_dir
from storage.ops_signal_store_sqlite import OpsSignalStoreSQLite

FLAGS = runtime_dir() / "flags"
HEALTH = runtime_dir() / "health"
STOP_FILE = FLAGS / "ops_risk_gate_service.stop"
STATUS_FILE = HEALTH / "ops_risk_gate_service.json"
logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_status(obj: Dict[str, Any]) -> None:
    ensure_dirs()
    HEALTH.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class RiskGateServiceCfg:
    store_path: str = ""
    poll_interval_sec: float = 1.0
    write_if_unchanged: bool = False


def process_latest_raw_signal(
    *,
    store: OpsSignalStoreSQLite | None = None,
    thresholds: RiskGateThresholds | None = None,
    write_if_unchanged: bool = False,
) -> Dict[str, Any]:
    db = store or OpsSignalStoreSQLite()
    snap = db.latest_raw_signal()
    if not snap:
        return {"ok": False, "reason": "no_raw_signal"}

    gate = decide_gate(snap, th=thresholds)
    new_gate = gate.to_dict()
    last_gate = db.latest_risk_gate()
    if not write_if_unchanged and isinstance(last_gate, dict):
        # Ignore timestamp when checking semantic equality.
        lhs = dict(last_gate)
        rhs = dict(new_gate)
        lhs.pop("ts", None)
        rhs.pop("ts", None)
        if lhs == rhs:
            return {"ok": True, "written": False, "reason": "unchanged", "gate": new_gate}

    gate_id = db.insert_risk_gate(new_gate)
    return {"ok": True, "written": True, "gate_id": int(gate_id), "gate": new_gate}


def run_forever(cfg: RiskGateServiceCfg, *, max_loops: int | None = None) -> Dict[str, Any]:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception as exc:
        logger.warning("ops_risk_gate_stop_file_clear_failed", extra={"path": str(STOP_FILE), "error": str(exc)})

    store = OpsSignalStoreSQLite(path=cfg.store_path)
    loops = 0
    writes = 0
    unchanged = 0
    errors = 0
    _write_status({"ok": True, "status": "running", "ts": _now_iso(), "loops": loops, "writes": writes, "unchanged": unchanged, "errors": errors})
    while True:
        loops += 1
        if STOP_FILE.exists():
            out = {
                "ok": True,
                "status": "stopped",
                "reason": "stop_requested",
                "ts": _now_iso(),
                "loops": loops,
                "writes": writes,
                "unchanged": unchanged,
                "errors": errors,
            }
            _write_status(out)
            return out

        out = process_latest_raw_signal(store=store, write_if_unchanged=bool(cfg.write_if_unchanged))
        if out.get("ok") and out.get("written"):
            writes += 1
        elif out.get("ok"):
            unchanged += 1
        else:
            errors += 1

        _write_status(
            {
                "ok": True,
                "status": "running",
                "ts": _now_iso(),
                "loops": loops,
                "writes": writes,
                "unchanged": unchanged,
                "errors": errors,
            }
        )

        if max_loops is not None and loops >= int(max_loops):
            final = {
                "ok": True,
                "status": "stopped",
                "reason": "max_loops",
                "loops": loops,
                "writes": writes,
                "unchanged": unchanged,
                "errors": errors,
            }
            _write_status({**final, "ts": _now_iso()})
            return final
        time.sleep(max(0.05, float(cfg.poll_interval_sec)))


def request_stop() -> Dict[str, Any]:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text(_now_iso() + "\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(STOP_FILE)}
