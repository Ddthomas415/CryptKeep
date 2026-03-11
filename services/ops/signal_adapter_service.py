from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

from services.ops.telemetry_snapshot_builder import TelemetrySnapshotCfg, publish_snapshot
from services.os.app_paths import ensure_dirs, runtime_dir

FLAGS = runtime_dir() / "flags"
HEALTH = runtime_dir() / "health"
STOP_FILE = FLAGS / "ops_signal_adapter.stop"
STATUS_FILE = HEALTH / "ops_signal_adapter.json"
logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_status(obj: Dict[str, Any]) -> None:
    ensure_dirs()
    HEALTH.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


@dataclass(frozen=True)
class SignalAdapterServiceCfg:
    poll_interval_sec: float = 1.0
    telemetry: TelemetrySnapshotCfg = TelemetrySnapshotCfg()


def publish_once(cfg: SignalAdapterServiceCfg) -> Dict[str, Any]:
    out = publish_snapshot(cfg.telemetry)
    return {"ok": True, "ts": _now_iso(), **out}


def run_forever(cfg: SignalAdapterServiceCfg, *, max_loops: int | None = None) -> Dict[str, Any]:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception as exc:
        logger.warning("ops_signal_adapter_stop_file_clear_failed", extra={"path": str(STOP_FILE), "error": str(exc)})

    loops = 0
    writes = 0
    errors = 0
    _write_status({"ok": True, "status": "running", "ts": _now_iso(), "loops": 0, "writes": 0, "errors": 0})
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
                "errors": errors,
            }
            _write_status(out)
            return out

        try:
            publish_once(cfg)
            writes += 1
        except Exception as exc:
            errors += 1
            logger.warning("ops_signal_adapter_publish_failed", extra={"error": f"{type(exc).__name__}:{exc}"})

        _write_status(
            {
                "ok": True,
                "status": "running",
                "ts": _now_iso(),
                "loops": loops,
                "writes": writes,
                "errors": errors,
            }
        )
        if max_loops is not None and loops >= int(max_loops):
            out = {
                "ok": True,
                "status": "stopped",
                "reason": "max_loops",
                "ts": _now_iso(),
                "loops": loops,
                "writes": writes,
                "errors": errors,
            }
            _write_status(out)
            return out
        time.sleep(max(0.05, float(cfg.poll_interval_sec)))


def request_stop() -> Dict[str, Any]:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    STOP_FILE.write_text(_now_iso() + "\n", encoding="utf-8")
    return {"ok": True, "stop_file": str(STOP_FILE)}

