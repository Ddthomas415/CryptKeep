from pathlib import Path
import os
from services.admin.health import read_health

PID_DIR = Path("runtime") / "pids"

def _pid_alive(pid: int) -> bool:
    try:
        if pid <= 0: return False
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def pid_info(service: str) -> dict:
    pf = PID_DIR / f"{service}.pid"
    if not pf.exists(): return {"pid_file": str(pf), "pid": None, "alive": False, "pid_file_exists": False}
    try: pid = int(pf.read_text().strip())
    except Exception: pid = None
    return {"pid_file": str(pf), "pid": pid, "alive": _pid_alive(pid) if pid else False, "pid_file_exists": True}

def snapshot(service: str) -> dict:
    h = read_health(service) or {}
    p = pid_info(service)
    return {
        "service": service,
        "health_status": h.get("status"),
        "health_ts": h.get("ts"),
        "health_pid": h.get("pid"),
        "pid_file_exists": p.get("pid_file_exists"),
        "pid": p.get("pid"),
        "pid_alive": p.get("alive")
    }
