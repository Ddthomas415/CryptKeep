from __future__ import annotations

import os
import subprocess, sys, time, socket, webbrowser
from pathlib import Path

from services.os.ports import resolve_preferred_port


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]

def _port_open(host: str, port: int, timeout: float = 0.25) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

def main(port: int = 8502):
    resolution = resolve_preferred_port(
        "127.0.0.1",
        int(port),
        max_offset=int(os.environ.get("CBP_PORT_SEARCH_LIMIT", "50") or "50"),
    )
    resolved_port = int(resolution.resolved_port)
    # Start Streamlit if not already running, then open browser (dev-friendly desktop smoke)
    url = f"http://localhost:{resolved_port}"
    if not _port_open("127.0.0.1", resolved_port):
        repo = _repo_root()
        cmd = [sys.executable, "-m", "streamlit", "run", str(repo / "dashboard" / "app.py"),
               "--server.port", str(resolved_port), "--server.address", "127.0.0.1"]
        subprocess.Popen(cmd, cwd=str(repo))
        # wait for port
        for _ in range(80):
            if _port_open("127.0.0.1", resolved_port):
                break
            time.sleep(0.25)
    webbrowser.open(url)

if __name__ == "__main__":
    main()
