from __future__ import annotations

import os
import sys
import time
import socket
import webbrowser
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def _find_dashboard_entry() -> Path:
    candidates = [
        ROOT / "dashboard" / "app.py",
        ROOT / "dashboard" / "main_app.py",
        ROOT / "app" / "app.py",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("No dashboard entry found (expected dashboard/app.py or dashboard/main_app.py).")

def _free_port(preferred: int = 8501) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])

def main():
    # Important for packaged apps: ensure relative paths work
    os.chdir(str(ROOT))

    entry = _find_dashboard_entry()
    port = _free_port(8501)
    url = f"http://localhost:{port}"

    # Run Streamlit as a child process so closing this app can terminate it.
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(entry),
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]

    p = subprocess.Popen(cmd, cwd=str(ROOT))
    time.sleep(0.8)
    try:
        webbrowser.open(url, new=1, autoraise=True)
    except Exception:
        pass

    try:
        rc = p.wait()
        raise SystemExit(rc)
    except KeyboardInterrupt:
        try:
            p.terminate()
        except Exception:
            pass
        raise SystemExit(0)

if __name__ == "__main__":
    main()
