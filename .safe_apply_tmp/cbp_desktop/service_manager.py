from pathlib import Path

# --- PID files (used by safe Run ID rotation) ---
PID_DIR = Path("runtime") / "pids"

def _pid_path(service_name: str) -> Path:
    PID_DIR.mkdir(parents=True, exist_ok=True)
    return PID_DIR / f"{service_name}.pid"

def _write_pid(service_name: str, pid: int) -> None:
    try:
        _pid_path(service_name).write_text(str(int(pid)) + "\n", encoding="utf-8")
    except Exception:
        pass

def _clear_pid(service_name: str) -> None:
    try:
        p = _pid_path(service_name)
        if p.exists():
            p.unlink()
    except Exception:
        pass

# Minimal stub for service_manager.py (so imports don't crash)
def specs_default():
    return {}

def start_service(spec):
    return True, "Stub: started"

def stop_service(name):
    return True, "Stub: stopped"

def is_running(name):
    return False, "Stub: not running"

def start_stack(items):
    return {"ok": True, "started": items}


def known_service_names() -> list[str]:
    try:
        return sorted(list(SERVICE_SPECS.keys()))
    except Exception:
        return []
