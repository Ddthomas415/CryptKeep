from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from services.execution.live_executor import LiveCfg, cfg_from_yaml, reconcile_live, submit_pending_live
from services.os.app_paths import ensure_dirs, runtime_dir
from storage.ws_status_sqlite import WSStatusSQLite
from services.os.file_utils import atomic_write


FLAGS = runtime_dir() / "flags"
STOP_FILE = FLAGS / "live_event_executor.stop"
STATUS_FILE = FLAGS / "live_event_executor.status.json"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _now_ms() -> int:
    return int(time.time() * 1000)


def _write_status(payload: Dict[str, Any]) -> None:
    FLAGS.mkdir(parents=True, exist_ok=True)
    atomic_write(STATUS_FILE, json.dumps(payload, indent=2, sort_keys=True))


@dataclass
class EventLoopState:
    loops: int = 0
    triggers: int = 0
    last_recv_ts_ms: int = 0
    last_trigger_ts_ms: int = 0


def run_tick(
    cfg: LiveCfg,
    *,
    state: EventLoopState,
    ws_store: WSStatusSQLite | None = None,
    min_trigger_interval_ms: int = 200,
    now_ms: int | None = None,
) -> Dict[str, Any]:
    state.loops += 1
    ws = ws_store or WSStatusSQLite()
    row = ws.get_status(exchange=str(cfg.exchange_id), symbol=str(cfg.symbol))
    if not row:
        return {"ok": True, "triggered": False, "reason": "ws_status_missing", "loops": state.loops}

    recv_ts_ms = int(row.get("recv_ts_ms") or 0)
    if recv_ts_ms <= int(state.last_recv_ts_ms):
        return {
            "ok": True,
            "triggered": False,
            "reason": "no_new_ws_event",
            "recv_ts_ms": recv_ts_ms,
            "last_recv_ts_ms": int(state.last_recv_ts_ms),
            "loops": state.loops,
        }

    state.last_recv_ts_ms = recv_ts_ms
    now_v = int(now_ms) if now_ms is not None else _now_ms()
    if int(state.last_trigger_ts_ms) > 0 and (now_v - int(state.last_trigger_ts_ms)) < int(max(1, min_trigger_interval_ms)):
        return {
            "ok": True,
            "triggered": False,
            "reason": "trigger_throttled",
            "recv_ts_ms": recv_ts_ms,
            "min_trigger_interval_ms": int(max(1, min_trigger_interval_ms)),
            "loops": state.loops,
        }

    submit_out = submit_pending_live(cfg)
    reconcile_out = reconcile_live(cfg)
    state.last_trigger_ts_ms = now_v
    state.triggers += 1
    return {
        "ok": True,
        "triggered": True,
        "recv_ts_ms": recv_ts_ms,
        "loops": state.loops,
        "triggers": state.triggers,
        "submit": submit_out,
        "reconcile": reconcile_out,
    }


def request_stop() -> Dict[str, Any]:
    ensure_dirs()
    FLAGS.mkdir(parents=True, exist_ok=True)
    atomic_write(STOP_FILE, _now_iso() + "\n")
    return {"ok": True, "stop_file": str(STOP_FILE)}


def run_forever(
    *,
    cfg_path: str = "config/trading.yaml",
    poll_sec: float = 0.2,
    min_trigger_interval_ms: int = 200,
) -> Dict[str, Any]:
    ensure_dirs()
    try:
        if STOP_FILE.exists():
            STOP_FILE.unlink()
    except Exception:
        pass

    cfg = cfg_from_yaml(str(cfg_path))
    state = EventLoopState()
    ws = WSStatusSQLite()
    started = _now_iso()
    _write_status(
        {
            "ok": True,
            "status": "running",
            "started": started,
            "cfg_path": str(cfg_path),
            "exchange_id": str(cfg.exchange_id),
            "symbol": str(cfg.symbol),
            "poll_sec": float(poll_sec),
            "min_trigger_interval_ms": int(min_trigger_interval_ms),
            "pid": int(os.getpid()),
            "loops": 0,
            "triggers": 0,
            "ts": _now_iso(),
        }
    )

    while True:
        if STOP_FILE.exists():
            break
        out = run_tick(
            cfg,
            state=state,
            ws_store=ws,
            min_trigger_interval_ms=int(min_trigger_interval_ms),
        )
        status_payload = {
            "ok": True,
            "status": "running",
            "started": started,
            "cfg_path": str(cfg_path),
            "exchange_id": str(cfg.exchange_id),
            "symbol": str(cfg.symbol),
            "poll_sec": float(poll_sec),
            "min_trigger_interval_ms": int(min_trigger_interval_ms),
            "pid": int(os.getpid()),
            "loops": int(state.loops),
            "triggers": int(state.triggers),
            "last_recv_ts_ms": int(state.last_recv_ts_ms),
            "last_trigger_ts_ms": int(state.last_trigger_ts_ms),
            "last_tick": out,
            "ts": _now_iso(),
        }
        _write_status(status_payload)
        time.sleep(max(0.05, float(poll_sec)))

    final = {
        "ok": True,
        "status": "stopped",
        "started": started,
        "loops": int(state.loops),
        "triggers": int(state.triggers),
        "last_recv_ts_ms": int(state.last_recv_ts_ms),
        "last_trigger_ts_ms": int(state.last_trigger_ts_ms),
        "ts": _now_iso(),
    }
    _write_status(final)
    return final


def status() -> Dict[str, Any]:
    if not STATUS_FILE.exists():
        return {"ok": False, "status": "missing", "status_file": str(STATUS_FILE)}
    try:
        return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        return {"ok": False, "status": "invalid", "status_file": str(STATUS_FILE), "error": f"{type(e).__name__}:{e}"}
