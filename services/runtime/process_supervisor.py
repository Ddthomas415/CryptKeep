from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from services.admin.system_guard import set_state as set_system_guard_state
from services.os.app_paths import runtime_dir, ensure_dirs, code_root
from services.logging.app_logger import get_logger

ensure_dirs()
RUNTIME_DIR = runtime_dir()
logger = get_logger("process_supervisor")
FLAGS_DIR = RUNTIME_DIR / "flags"
HEALTH_DIR = RUNTIME_DIR / "health"

SERVICE_STATUS_PATHS = {
    "pipeline": FLAGS_DIR / "pipeline.status.json",
    "executor": FLAGS_DIR / "intent_executor.status.json",
    "intent_consumer": FLAGS_DIR / "live_intent_consumer.status.json",
    "reconciler": FLAGS_DIR / "live_reconciler.status.json",
    "ops_signal_adapter": HEALTH_DIR / "ops_signal_adapter.json",
    "ops_risk_gate": HEALTH_DIR / "ops_risk_gate_service.json",
    "ai_alert_monitor": HEALTH_DIR / "ai_alert_monitor.json",
}

UNHEALTHY_STATUSES = {"safe_idle", "blocked", "error", "failed", "crashed"}

def _pidfile(name: str) -> Path:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return RUNTIME_DIR / f"{name}.pid"

def _read_pid(name: str) -> Optional[int]:
    p = _pidfile(name)
    if not p.exists():
        return None
    try:
        return int(p.read_text(encoding="utf-8").strip())
    except Exception:
        return None

def _write_pid(name: str, pid: int) -> None:
    _pidfile(name).write_text(str(int(pid)), encoding="utf-8")

def _clear_pid(name: str) -> None:
    p = _pidfile(name)
    try:
        if p.exists():
            p.unlink()
    except Exception:
        logger.exception("process_supervisor: failed to remove pid file path=%s", p)

def _load_json(path: Path) -> dict[str, object]:
    try:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _service_status_payload(name: str) -> dict[str, object]:
    path = SERVICE_STATUS_PATHS.get(name)
    if path is None:
        return {}
    payload = _load_json(path)
    if payload:
        payload["_path"] = str(path)
    return payload

def _service_healthy(*, running: bool, status_value: object) -> bool:
    if not running:
        return False
    normalized = str(status_value or "").strip().lower()
    if normalized in UNHEALTHY_STATUSES:
        return False
    return True

def is_running(name: str) -> bool:
    pid = _read_pid(name)
    if not pid:
        return False
    try:
        # Windows: os.kill(pid, 0) works in py3.8+ for existence in most cases
        os.kill(pid, 0)
        return True
    except Exception:
        _clear_pid(name)
        return False

def start_process(name: str, cmd: list[str], *, env: Dict[str, str] | None = None) -> Dict[str, object]:
    if is_running(name):
        return {"ok": True, "note": "already_running", "name": name, "pid": _read_pid(name), "cmd": cmd}

    # detach-ish: new process group so we can kill group on unix
    kwargs = {}
    if os.name != "nt":
        kwargs["preexec_fn"] = os.setsid
    else:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    # Persist stdout/stderr to a named log file so exits leave durable evidence.
    log_path = runtime_dir() / "logs" / f"{name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_fh = open(log_path, "a", buffering=1)

    child_env = os.environ.copy()
    if env:
        child_env.update({str(k): str(v) for k, v in env.items()})

    proc = subprocess.Popen(
        cmd,
        cwd=str(code_root()),
        env=child_env,
        stdout=log_fh,
        stderr=log_fh,
        **kwargs,
    )
    _write_pid(name, proc.pid)
    return {"ok": True, "note": "started", "name": name, "pid": proc.pid, "cmd": cmd}


def request_system_guard_halt(*, writer: str, reason: str) -> Dict[str, object]:
    try:
        payload = set_system_guard_state("HALTING", writer=str(writer or "process_supervisor"), reason=str(reason or "runtime_stop"))
        return {"ok": True, "payload": payload}
    except Exception as exc:
        logger.exception(
            "process_supervisor: system_guard halt failed writer=%s reason=%s",
            writer,
            reason,
        )
        return {
            "ok": False,
            "reason": f"system_guard_write_failed:{type(exc).__name__}",
            "error": str(exc),
        }

def stop_process(name: str, timeout_sec: float = 5.0) -> Dict[str, object]:
    pid = _read_pid(name)
    if not pid:
        return {"ok": True, "note": "not_running", "name": name}

    # Try graceful terminate
    try:
        if os.name != "nt":
            os.killpg(pid, signal.SIGTERM)
        else:
            os.kill(pid, signal.SIGTERM)
    except Exception as e:
        logger.warning(
            "process_supervisor: graceful stop signal failed name=%s pid=%s error=%s:%s",
            name,
            pid,
            type(e).__name__,
            e,
        )

    deadline = time.time() + float(timeout_sec)
    while time.time() < deadline:
        try:
            os.kill(pid, 0)
            time.sleep(0.2)
        except Exception:
            _clear_pid(name)
            return {"ok": True, "note": "stopped", "name": name, "pid": pid}

    # Force kill
    try:
        if os.name != "nt":
            os.killpg(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGKILL)
    except Exception as e:
        logger.warning(
            "process_supervisor: force kill signal failed name=%s pid=%s error=%s:%s",
            name,
            pid,
            type(e).__name__,
            e,
        )

    _clear_pid(name)
    return {"ok": True, "note": "killed", "name": name, "pid": pid}

def status(names: list[str]) -> Dict[str, object]:
    out = {}
    for n in names:
        running = is_running(n)
        pid = _read_pid(n)
        payload = _service_status_payload(n)
        status_value = payload.get("status") or ("running" if running else "not_running")
        out[n] = {
            "running": running,
            "pid": pid,
            "status": status_value,
            "reason": payload.get("reason"),
            "healthy": _service_healthy(running=running, status_value=status_value),
        }
        if payload.get("ts_epoch") is not None:
            out[n]["ts_epoch"] = payload.get("ts_epoch")
        if payload.get("_path"):
            out[n]["status_path"] = payload.get("_path")
    return out
