from __future__ import annotations

import json
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir
from services.process.crash_snapshot import write_crash_snapshot

PROC_PATH = data_dir() / "bot_process.json"
LOG_DIR = data_dir() / "logs"
BOT_LOG = LOG_DIR / "bot.log"

def _iso_now() -> str:
    return datetime.utcfromtimestamp(time.time()).isoformat() + "Z"

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
        # Windows: tasklist filter
        out = subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}"], stderr=subprocess.STDOUT)
        s = out.decode("utf-8", errors="replace").lower()
        return str(pid) in s and "no tasks" not in s
    except Exception:
        return False

def status() -> dict:
    st = _read()
    pid = st.get("pid")
    if not pid:
        return {"ok": True, "running": False, "state": st, "log_path": str(BOT_LOG), "proc_path": str(PROC_PATH)}
    alive = _pid_alive(int(pid))
    return {"ok": True, "running": bool(alive), "pid": int(pid), "state": st, "log_path": str(BOT_LOG), "proc_path": str(PROC_PATH)}

def start_bot(*, venue: str, symbols: list[str], force: bool = False) -> dict:
    st = status()
    if st.get("running"):
        return {"ok": False, "reason": "already_running", **st}

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    # append mode
    lf = open(BOT_LOG, "ab", buffering=0)

    syms = [s.strip().upper().replace("-", "/") for s in (symbols or []) if str(s).strip()]
    if not syms:
        syms = ["BTC/USDT"]

    cmd = [
        sys.executable,
        "scripts/run_bot_safe.py",
        "--venue", str(venue),
        "--symbols", ",".join(syms),
    ]
    if force:
        cmd.append("--force")

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
        obj = {
            "pid": p.pid,
            "cmd": cmd,
            "venue": str(venue),
            "symbols": syms,
            "started_ts_iso": _iso_now(),
            "started_ts_epoch": time.time(),
            "force": bool(force),
        }
        _write(obj)
        return {"ok": True, "started": True, "pid": p.pid, "log_path": str(BOT_LOG), "proc_path": str(PROC_PATH)}
    except Exception as e:
        try:
            lf.close()
        except Exception:
            pass
        return {"ok": False, "reason": f"start_failed:{type(e).__name__}", "error": str(e)}

def stop_bot(*, hard: bool = True) -> dict:
    st = _read()
    pid = st.get("pid")
    if not pid:
        return {"ok": True, "stopped": True, "reason": "no_pid"}

    pid = int(pid)
    if not _pid_alive(pid):
        # stale pid file
        _write({})
        return {"ok": True, "stopped": True, "reason": "not_running_stale_pid"}

    try:
        if os.name != "nt":
            # SIGTERM then optional SIGKILL
            import signal
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.6)
            if hard and _pid_alive(pid):
                os.kill(pid, signal.SIGKILL)
        else:
            # taskkill /T /F is the most reliable for child tree
            args = ["taskkill", "/PID", str(pid), "/T"]
            if hard:
                args.append("/F")
            subprocess.check_call(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.4)
    except Exception as e:
        return {"ok": False, "reason": f"stop_failed:{type(e).__name__}", "error": str(e)}

    # clear pid file if process is gone
    if not _pid_alive(pid):
        _write({})
    return {"ok": True, "stopped": True, "pid": pid}

def stop_all(*, hard: bool = True) -> dict:
    # currently only tracks bot; future-proof structure
    r = stop_bot(hard=hard)
    return {"ok": True, "bot": r}
