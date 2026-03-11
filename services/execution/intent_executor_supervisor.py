from __future__ import annotations

import os, signal, subprocess, sys, time
from typing import Any
from services.os.app_paths import data_dir, code_root

PID_PATH = data_dir() / "intent_executor.pid"

def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def _read_pid() -> int | None:
    try:
        if not PID_PATH.exists():
            return None
        s = PID_PATH.read_text(encoding="utf-8").strip()
        return int(s) if s else None
    except Exception:
        return None

def _write_pid(pid: int):
    PID_PATH.parent.mkdir(parents=True, exist_ok=True)
    PID_PATH.write_text(str(int(pid)), encoding="utf-8")

def _remove_pid():
    try:
        if PID_PATH.exists():
            PID_PATH.unlink()
    except Exception:
        pass

def status() -> dict[str, Any]:
    pid = _read_pid()
    return {"ok": True, "pid_path": str(PID_PATH), "pid": pid, "alive": bool(pid and _pid_alive(pid))}

def start() -> dict[str, Any]:
    cur = _read_pid()
    if cur and _pid_alive(cur):
        return {"ok": True, "already_running": True, "pid": cur, "detail": status()}

    _remove_pid()
    cmd = [sys.executable, "scripts/run_intent_executor.py"]
    kwargs: dict[str, Any] = {
        "cwd": str(code_root()),
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "stdin": subprocess.DEVNULL,
    }
    if os.name == "nt":
        creationflags = 0
        if hasattr(subprocess, "CREATE_NEW_PROCESS_GROUP"):
            creationflags |= subprocess.CREATE_NEW_PROCESS_GROUP
        if hasattr(subprocess, "DETACHED_PROCESS"):
            creationflags |= subprocess.DETACHED_PROCESS
        kwargs["creationflags"] = creationflags
    else:
        kwargs["start_new_session"] = True

    try:
        p = subprocess.Popen(cmd, **kwargs)  # noqa:S603,S607
        _write_pid(int(p.pid))
        return {"ok": True, "pid": int(p.pid), "pid_path": str(PID_PATH), "cmd": cmd}
    except Exception as e:
        return {"ok": False, "reason": f"{type(e).__name__}:{e}", "cmd": cmd}

def stop(force: bool = True) -> dict[str, Any]:
    pid = _read_pid()
    if not pid:
        return {"ok": True, "stopped": False, "reason": "no_pid_file", "pid_path": str(PID_PATH)}
    if not _pid_alive(pid):
        _remove_pid()
        return {"ok": True, "stopped": False, "reason": "pid_not_alive", "pid": pid}

    try:
        os.kill(pid, signal.SIGTERM)
    except Exception as e:
        if os.name == "nt" and force:
            try:
                subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa:S603,S607
            except Exception as e2:
                return {"ok": False, "reason": f"terminate_failed:{type(e).__name__}:{e};taskkill_failed:{type(e2).__name__}:{e2}", "pid": pid}
        else:
            return {"ok": False, "reason": f"terminate_failed:{type(e).__name__}:{e}", "pid": pid}

    t0 = time.time()
    while time.time() - t0 < 3.0:
        if not _pid_alive(pid):
            break
        time.sleep(0.1)

    if not _pid_alive(pid):
        _remove_pid()
        return {"ok": True, "stopped": True, "pid": pid}
    return {"ok": False, "stopped": False, "pid": pid, "reason": "process_still_alive"}
