from __future__ import annotations

import json
import os
import sys
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from services.os.app_paths import data_dir

PROC_PATH = data_dir() / "watchdog_process.json"
LOG_DIR = data_dir() / "logs"
WD_LOG = LOG_DIR / "watchdog_loop.log"

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _read() -> dict:
    try:
        if not PROC_PATH.exists():
            return {}
        return json.loads(PROC_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _write(obj: dict) -> None:
    PROC_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROC_PATH.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def _pid_alive(pid: int) -> bool:
    pid = int(pid)
    if pid <= 0:
        return False
    try:
        if os.name != "nt":
            os.kill(pid, 0)
            return True
        out = subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}"], stderr=subprocess.STDOUT)
        s = out.decode("utf-8", errors="replace").lower()
        return str(pid) in s and "no tasks" not in s
    except Exception:
        return False

def status() -> dict:
    st = _read()
    pid = st.get("pid")
    alive = bool(pid and _pid_alive(int(pid)))
    return {"ok": True, "running": alive, "pid": int(pid) if pid else None, "state": st, "log_path": str(WD_LOG), "proc_path": str(PROC_PATH)}

def start_watchdog(*, interval_sec: int = 15) -> dict:
    st = status()
    if st.get("running"):
        return {"ok": False, "reason": "already_running", **st}

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    lf = open(WD_LOG, "ab", buffering=0)

    cmd = [sys.executable, "scripts/watchdog.py", "--loop", "--interval", str(int(interval_sec))]

    try:
        p = subprocess.Popen(
            cmd,
            cwd=str(Path(__file__).resolve().parents[2]),
            stdout=lf,
            stderr=lf,
            stdin=subprocess.DEVNULL,
            close_fds=(os.name != "nt"),
            creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0),
        )
        _write({
            "pid": p.pid,
            "cmd": cmd,
            "interval_sec": int(interval_sec),
            "started_ts_iso": _iso_now(),
            "started_ts_epoch": time.time(),
        })
        return {"ok": True, "started": True, "pid": p.pid, "log_path": str(WD_LOG), "proc_path": str(PROC_PATH)}
    except Exception as e:
        try: lf.close()
        except Exception: pass
        return {"ok": False, "reason": f"start_failed:{type(e).__name__}", "error": str(e)}

def stop_watchdog(*, hard: bool = True, soft_timeout_sec: float = 6.0) -> dict:
    st = _read()
    pid = st.get("pid")
    if not pid:
        _write({})
        return {"ok": True, "stopped": True, "reason": "no_pid"}

    pid = int(pid)
    if not _pid_alive(pid):
        _write({})
        return {"ok": True, "stopped": True, "reason": "stale_pid"}

    # soft stop
    try:
        if os.name != "nt":
            import signal
            os.kill(pid, signal.SIGTERM)
        else:
            subprocess.check_call(["taskkill", "/PID", str(pid), "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        return {"ok": False, "reason": f"soft_stop_failed:{type(e).__name__}", "error": str(e)}

    t_end = time.time() + float(soft_timeout_sec)
    while time.time() < t_end:
        if not _pid_alive(pid):
            _write({})
            return {"ok": True, "stopped": True, "pid": pid, "mode": "soft"}
        time.sleep(0.25)

    if hard and _pid_alive(pid):
        try:
            if os.name != "nt":
                import signal
                os.kill(pid, signal.SIGKILL)
            else:
                subprocess.check_call(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            return {"ok": False, "reason": f"hard_kill_failed:{type(e).__name__}", "error": str(e)}

    time.sleep(0.4)
    if not _pid_alive(pid):
        _write({})
        return {"ok": True, "stopped": True, "pid": pid, "mode": ("hard" if hard else "soft_timeout")}
    return {"ok": False, "reason": "still_running_after_stop", "pid": pid}

def clear_stale() -> dict:
    st = _read()
    pid = st.get("pid")
    if not pid or (pid and (not _pid_alive(int(pid)))):
        _write({})
        return {"ok": True, "cleared": True}
    return {"ok": True, "cleared": False, "reason": "still_running", "pid": int(pid)}
