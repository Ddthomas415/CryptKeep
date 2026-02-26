from pathlib import Path
from services.os.app_paths import runtime_dir, ensure_dirs

# File that stores the current run ID
ensure_dirs()
RUN_ID_FILE = runtime_dir() / "run_id.txt"
RUN_ID_ENV = "RUN_ID"

def get_or_create_run_id() -> str:
    """
    Minimal placeholder: returns the run ID stored in file or default.
    """
    if RUN_ID_FILE.exists():
        return RUN_ID_FILE.read_text().strip()
    rid = "default-run-id"
    RUN_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
    RUN_ID_FILE.write_text(rid)
    return rid

def run_id() -> str:
    return get_or_create_run_id()




def _pid_alive(pid: int) -> bool:
    try:
        if pid <= 0:
            return False
        import os
        # signal 0 works on POSIX; on Windows, os.kill exists too
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def any_services_running() -> bool:
    # Best-effort safety:
    # - if runtime/pids/*.pid exists and any pid is alive => "running"
    # - avoids rotating run_id while bots/services are active
    try:
        pdir = runtime_dir() / "pids"
        if not pdir.exists():
            return False
        for pf in pdir.glob("*.pid"):
            try:
                s = pf.read_text(encoding="utf-8").strip()
                pid = int(s) if s else 0
                if _pid_alive(pid):
                    return True
            except Exception:
                continue
        return False
    except Exception:
        return False

def rotate_run_id(force: bool = False) -> str:
    # Rotate to a new run id.
    # SAFE by default: will refuse if any services appear to be running.
    # Set force=True only if you know processes are stopped.
    if (not force) and any_services_running():
        raise RuntimeError("services_running: stop bots before rotating run id")

    # delete file and env to force regen
    try:
        if RUN_ID_FILE.exists():
            RUN_ID_FILE.unlink()
    except Exception:
        pass
    try:
        import os
        if RUN_ID_ENV in os.environ:
            del os.environ[RUN_ID_ENV]
    except Exception:
        pass
    return get_or_create_run_id()
