from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)


import os
import subprocess
from pathlib import Path
from services.os.app_paths import data_dir, ensure_dirs

def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def main() -> int:
    ensure_dirs()
    sup_dir = data_dir() / "supervisor"
    sup_dir.mkdir(parents=True, exist_ok=True)
    pid_path = sup_dir / "daemon.pid"
    stop_path = sup_dir / "STOP"
    if stop_path.exists():
        stop_path.unlink()

    if pid_path.exists():
        try:
            pid = int(pid_path.read_text().strip())
            if pid_alive(pid):
                print("Supervisor already running:", pid)
                return 0
        except Exception:
            pass

    cmd = [sys.executable, "-u", "services/supervisor/supervisor_daemon.py"]
    p = subprocess.Popen(cmd, cwd=str(Path(".").resolve()))
    pid_path.write_text(str(p.pid), encoding="utf-8")
    print("Supervisor started:", p.pid)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
