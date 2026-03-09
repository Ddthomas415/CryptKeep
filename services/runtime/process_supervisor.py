from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from services.os.app_paths import runtime_dir, ensure_dirs
from services.logging.app_logger import get_logger

ensure_dirs()
RUNTIME_DIR = runtime_dir()
logger = get_logger("process_supervisor")

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

def start_process(name: str, cmd: list[str]) -> Dict[str, object]:
    if is_running(name):
        return {"ok": True, "note": "already_running", "name": name, "pid": _read_pid(name), "cmd": cmd}

    # detach-ish: new process group so we can kill group on unix
    kwargs = {}
    if os.name != "nt":
        kwargs["preexec_fn"] = os.setsid
    else:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

    proc = subprocess.Popen(cmd, cwd=str(Path(".").resolve()), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
    _write_pid(name, proc.pid)
    return {"ok": True, "note": "started", "name": name, "pid": proc.pid, "cmd": cmd}

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
        out[n] = {"running": is_running(n), "pid": _read_pid(n)}
    return out
