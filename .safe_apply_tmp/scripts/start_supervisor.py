from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

def pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def main() -> int:
    data_dir = Path("data/supervisor")
    data_dir.mkdir(parents=True, exist_ok=True)
    pid_path = data_dir / "daemon.pid"
    stop_path = data_dir / "STOP"
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
