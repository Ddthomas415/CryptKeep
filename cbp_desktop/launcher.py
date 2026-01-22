from __future__ import annotations

import atexit
import os
import socket
import subprocess
import sys
import time
import webbrowser
from dataclasses import dataclass
from typing import Optional, List

def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = int(s.getsockname()[1])
    s.close()
    return port

def _env_on(name: str) -> bool:
    return (os.environ.get(name, "") or "").strip().lower() in ("1", "true", "yes", "on")

@dataclass
class Child:
    name: str
    p: subprocess.Popen

def _py() -> str:
    return sys.executable

def _run_streamlit(port: int) -> Child:
    cmd = [
        _py(), "-m", "streamlit", "run", "dashboard/app.py",
        "--server.headless", "true",
        "--server.port", str(port),
        "--server.address", "127.0.0.1",
        "--browser.gatherUsageStats", "false",
    ]

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    os.makedirs("runtime/config", exist_ok=True)
    os.makedirs("data/logs", exist_ok=True)

    log_path = "data/logs/launcher-streamlit.log"
    with open(log_path, "a", encoding="utf-8") as logf:
        p = subprocess.Popen(cmd, stdout=logf, stderr=logf, env=env, cwd=os.getcwd())
    return Child("streamlit", p)

def main() -> int:
    port = int(os.environ.get("CBP_DASH_PORT") or 0) or _free_port()
    url = f"http://127.0.0.1:{port}"

    children: List[Child] = []

    def cleanup():
        for c in reversed(children):
            try:
                if c.p.poll() is None:
                    c.p.terminate()
                    time.sleep(0.5)
                    if c.p.poll() is None:
                        c.p.kill()
            except Exception:
                pass

    atexit.register(cleanup)

    print(f"Starting Crypto Bot Pro dashboard on port {port}...")
    c = _run_streamlit(port)
    children.append(c)

    time.sleep(3.0)  # Give Streamlit time to bind

    print(f"Dashboard ready at: {url}")
    try:
        webbrowser.open(url)
    except Exception:
        print("Auto-open failed — please open manually:", url)

    try:
        while True:
            rc = c.p.poll()
            if rc is not None:
                print(f"Dashboard exited with code {rc}")
                return rc
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Shutting down...")
        return 0

if __name__ == "__main__":
    sys.exit(main())
