from __future__ import annotations

import os
import sys
import time
import socket
import subprocess
import webbrowser
import multiprocessing

def _free_port(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return False
    except Exception:
        return True

def _wait_port(host: str, port: int, timeout_sec: float = 20.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        if not _free_port(host, port):
            return True
        time.sleep(0.25)
    return False

def main() -> int:
    # PyInstaller + multiprocessing safety (common pitfall on Windows) :contentReference[oaicite:1]{index=1}
    multiprocessing.freeze_support()

    host = os.environ.get("CBP_HOST", "127.0.0.1")
    port = int(os.environ.get("CBP_PORT", "8501"))
    open_browser = os.environ.get("CBP_OPEN_BROWSER", "1") not in ("0", "false", "FALSE")

    # If port already in use, don't start another server; just open it.
    if not _free_port(host, port):
        if open_browser:
            webbrowser.open(f"http://{host}:{port}")
        print(f"[launcher] Streamlit already running on {host}:{port}")
        return 0

    # Start streamlit
    # IMPORTANT: packaging often requires using sys.executable to ensure correct interpreter in frozen apps.
    cmd = [
        sys.executable, "-m", "streamlit", "run", "dashboard/app.py",
        "--server.address", host,
        "--server.port", str(port),
        "--server.headless", "true",
    ]

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    print("[launcher] starting:", " ".join(cmd))
    p = subprocess.Popen(cmd, env=env)

    ok = _wait_port(host, port, timeout_sec=25.0)
    if open_browser and ok:
        webbrowser.open(f"http://{host}:{port}")

    # Keep launcher alive while Streamlit runs
    try:
        return p.wait()
    except KeyboardInterrupt:
        try:
            p.terminate()
        except Exception:
            pass
        return 130

if __name__ == "__main__":
    raise SystemExit(main())
