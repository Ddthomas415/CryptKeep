from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
STATUS_PATH = data_dir() / "bot_process.json"
LOG_DIR = data_dir() / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

@dataclass(frozen=True)
class ProcStatus:
    running: bool
    pid: Optional[int]
    mode: Optional[str]   # "paper" | "live"
    started_ts_ms: Optional[int]
    cmd: Optional[str]
    log_path: Optional[str]
    note: Optional[str] = None

def _now_ms() -> int:
    return int(time.time() * 1000)

def read_status() -> ProcStatus:
    if not STATUS_PATH.exists():
        return ProcStatus(False, None, None, None, None, None, note="no_status_file")
    try:
        d = json.loads(STATUS_PATH.read_text(encoding="utf-8", errors="replace"))
        pid = d.get("pid")
        running = False
        if pid:
            running = _pid_is_running(int(pid))
        return ProcStatus(
            running=bool(running),
            pid=int(pid) if pid else None,
            mode=d.get("mode"),
            started_ts_ms=d.get("started_ts_ms"),
            cmd=d.get("cmd"),
            log_path=d.get("log_path"),
            note=d.get("note"),
        )
    except Exception as e:
        return ProcStatus(False, None, None, None, None, None, note=f"status_read_error:{type(e).__name__}")

def _write_status(d: Dict[str, Any]) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(d, indent=2, sort_keys=True), encoding="utf-8")

def _pid_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            # tasklist returns 0 if any match; we parse output best-effort
            out = subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}"], text=True, stderr=subprocess.STDOUT)
            return str(pid) in out
        else:
            os.kill(pid, 0)
            return True
    except Exception:
        return False

def start_process(mode: str, module: str, extra_env: Optional[Dict[str, str]] = None) -> ProcStatus:
    st = read_status()
    if st.running and st.pid:
        return ProcStatus(True, st.pid, st.mode, st.started_ts_ms, st.cmd, st.log_path, note="already_running")

    mode = str(mode).lower().strip()
    log_path = str((LOG_DIR / f"{mode}_bot.log").resolve())

    env = os.environ.copy()
    if extra_env:
        env.update({k: str(v) for k, v in extra_env.items()})

    cmd = [sys.executable, "-m", module]
    with open(log_path, "a", encoding="utf-8") as logf:
        p = subprocess.Popen(cmd, stdout=logf, stderr=logf, env=env)

    d = {
        "pid": int(p.pid),
        "mode": mode,
        "started_ts_ms": _now_ms(),
        "cmd": " ".join(cmd),
        "log_path": log_path,
        "note": "started",
    }
    _write_status(d)
    return read_status()

def stop_process() -> ProcStatus:
    st = read_status()
    if not st.pid:
        try:
            if STATUS_PATH.exists():
                STATUS_PATH.unlink()
        except Exception:
            pass
        return ProcStatus(False, None, None, None, None, None, note="not_running")

    pid = int(st.pid)
    if not _pid_is_running(pid):
        try:
            if STATUS_PATH.exists():
                STATUS_PATH.unlink()
        except Exception:
            pass
        return ProcStatus(False, None, None, None, None, None, note="stale_pid_cleared")

    try:
        if os.name == "nt":
            subprocess.check_call(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            os.kill(pid, signal.SIGTERM)
            # give it a moment, then SIGKILL
            time.sleep(0.8)
            if _pid_is_running(pid):
                os.kill(pid, signal.SIGKILL)
    except Exception:
        # best-effort; do not crash UI
        pass

    try:
        if STATUS_PATH.exists():
            STATUS_PATH.unlink()
    except Exception:
        pass

    return ProcStatus(False, None, None, None, None, None, note="stopped")
