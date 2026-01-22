from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

DEFAULT_APP = "dashboard/app.py"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8501

def _is_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except Exception:
        return False

def _pick_port(host: str, start: int, max_tries: int = 50) -> int:
    port = int(start)
    for _ in range(max_tries):
        if not _is_port_open(host, port):
            return port
        port += 1
    raise RuntimeError("No free port found")

def _repo_root() -> Path:
    # assumes launcher/ is in repo root
    return Path(__file__).resolve().parents[1]

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", default=DEFAULT_APP, help="Streamlit entry (default dashboard/app.py)")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--no_browser", action="store_true")
    ap.add_argument("--headless", action="store_true", help="Do not auto-open browser; same as --no_browser")
    args = ap.parse_args()

    repo = _repo_root()
    entry = (repo / args.app).resolve()
    if not entry.exists():
        print(f"ERROR: Streamlit entry not found: {entry}")
        return 2

    host = str(args.host)
    port = _pick_port(host, int(args.port))

    url = f"http://{host}:{port}"
    env = os.environ.copy()
    env.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    env["STREAMLIT_SERVER_ADDRESS"] = host
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    cmd = [
        sys.executable, "-m", "streamlit", "run", str(entry),
        "--server.address", host,
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]

    print({"ok": True, "note": "starting_streamlit", "url": url, "cmd": cmd})

    proc = subprocess.Popen(cmd, cwd=str(repo), env=env)

    # wait for server
    deadline = time.time() + 30
    while time.time() < deadline:
        if proc.poll() is not None:
            print({"ok": False, "note": "streamlit_exited_early", "code": proc.returncode})
            return 3
        if _is_port_open(host, port):
            break
        time.sleep(0.25)

    if not _is_port_open(host, port):
        print({"ok": False, "note": "server_not_ready", "url": url})
        try:
            proc.terminate()
        except Exception:
            pass
        return 4

    if not (args.no_browser or args.headless):
        try:
            webbrowser.open(url)
        except Exception:
            pass

    print({"ok": True, "note": "running", "url": url, "pid": proc.pid})

    # Keep parent alive; Ctrl+C stops child cleanly
    try:
        while True:
            if proc.poll() is not None:
                print({"ok": True, "note": "streamlit_stopped", "code": proc.returncode})
                return 0
            time.sleep(0.5)
    except KeyboardInterrupt:
        print({"ok": True, "note": "keyboard_interrupt"})
        try:
            proc.terminate()
        except Exception:
            pass
        return 0

if __name__ == "__main__":
    raise SystemExit(main())
