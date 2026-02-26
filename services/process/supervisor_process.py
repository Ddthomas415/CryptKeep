from __future__ import annotations

import json
import os
import sys
import time
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from services.os.app_paths import data_dir

SUP_PATH = data_dir() / "supervisor_process.json"
LOG_DIR = data_dir() / "logs"
COCKPIT_LOG = LOG_DIR / "cockpit.log"
WATCHDOG_LOG = LOG_DIR / "watchdog.log"

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _read() -> dict:
    try:
        if not SUP_PATH.exists():
            return {}
        return json.loads(SUP_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _write(obj: dict) -> None:
    SUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUP_PATH.write_text(json.dumps(obj, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

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

def _soft_stop_pid(pid: int) -> None:
    pid = int(pid)
    if pid <= 0:
        return
    if os.name != "nt":
        import signal
        os.kill(pid, signal.SIGTERM)
    else:
        # gentle tree stop (no /F)
        subprocess.check_call(["taskkill", "/PID", str(pid), "/T"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def _hard_kill_pid(pid: int) -> None:
    pid = int(pid)
    if pid <= 0:
        return
    if os.name != "nt":
        import signal
        os.kill(pid, signal.SIGKILL)
    else:
        subprocess.check_call(["taskkill", "/PID", str(pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def status() -> dict:
    st = _read()
    cp = st.get("cockpit_pid")
    wp = st.get("watchdog_pid")
    return {
        "ok": True,
        "running": bool(cp and _pid_alive(int(cp))) or bool(wp and _pid_alive(int(wp))),
        "cockpit": {"pid": cp, "alive": bool(cp and _pid_alive(int(cp)))},
        "watchdog": {"pid": wp, "alive": bool(wp and _pid_alive(int(wp)))},
        "state": st,
        "paths": {"sup_path": str(SUP_PATH), "cockpit_log": str(COCKPIT_LOG), "watchdog_log": str(WATCHDOG_LOG)},
    }

def start(*, streamlit_cmd: list[str], watchdog_cmd: list[str], cwd: Path) -> dict:
    st = status()
    if st["cockpit"]["alive"] or st["watchdog"]["alive"]:
        return {"ok": False, "reason": "already_running", **st}

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    c_log = open(COCKPIT_LOG, "ab", buffering=0)
    w_log = open(WATCHDOG_LOG, "ab", buffering=0)

    try:
        cockpit = subprocess.Popen(
            streamlit_cmd,
            cwd=str(cwd),
            stdout=c_log,
            stderr=c_log,
            stdin=subprocess.DEVNULL,
            close_fds=(os.name != "nt"),
            creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0),
        )
        watchdog = subprocess.Popen(
            watchdog_cmd,
            cwd=str(cwd),
            stdout=w_log,
            stderr=w_log,
            stdin=subprocess.DEVNULL,
            close_fds=(os.name != "nt"),
            creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0),
        )
        obj = {
            "started_ts_iso": _iso_now(),
            "started_ts_epoch": time.time(),
            "cockpit_pid": cockpit.pid,
            "watchdog_pid": watchdog.pid,
            "streamlit_cmd": streamlit_cmd,
            "watchdog_cmd": watchdog_cmd,
        }
        _write(obj)
        return {"ok": True, "started": True, "cockpit_pid": cockpit.pid, "watchdog_pid": watchdog.pid, "paths": {"sup_path": str(SUP_PATH), "cockpit_log": str(COCKPIT_LOG), "watchdog_log": str(WATCHDOG_LOG)}}
    except Exception as e:
        try: c_log.close()
        except Exception: pass
        try: w_log.close()
        except Exception: pass
        return {"ok": False, "reason": f"start_failed:{type(e).__name__}", "error": str(e)}

def stop(*, hard: bool = True, soft_timeout_sec: float = 6.0) -> dict:
    st = _read()
    cp = st.get("cockpit_pid")
    wp = st.get("watchdog_pid")

    pids = []
    if cp: pids.append(int(cp))
    if wp: pids.append(int(wp))

    if not pids:
        _write({})
        return {"ok": True, "stopped": True, "reason": "no_pids"}

    # soft stop all
    for pid in pids:
        if _pid_alive(pid):
            try:
                _soft_stop_pid(pid)
            except Exception:
                pass

    t_end = time.time() + float(soft_timeout_sec)
    while time.time() < t_end:
        if all((not _pid_alive(pid)) for pid in pids):
            _write({})
            return {"ok": True, "stopped": True, "mode": "soft"}
        time.sleep(0.25)

    if hard:
        for pid in pids:
            if _pid_alive(pid):
                try:
                    _hard_kill_pid(pid)
                except Exception:
                    pass
        time.sleep(0.5)

    still = [pid for pid in pids if _pid_alive(pid)]
    if not still:
        _write({})
        return {"ok": True, "stopped": True, "mode": ("hard" if hard else "soft_timeout")}
    return {"ok": False, "stopped": False, "still_running": still, "mode": ("hard" if hard else "soft_timeout")}

def clear_stale() -> dict:
    st = _read()
    cp = st.get("cockpit_pid")
    wp = st.get("watchdog_pid")
    alive_any = False
    if cp and _pid_alive(int(cp)): alive_any = True
    if wp and _pid_alive(int(wp)): alive_any = True
    if not alive_any:
        _write({})
        return {"ok": True, "cleared": True}
    return {"ok": True, "cleared": False, "reason": "still_running"}
