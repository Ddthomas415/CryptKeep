from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
import webview

def _resource_path(rel: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return (base / rel).resolve()

def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])

def _wait_http_ready(url: str, timeout_sec: float = 25.0) -> bool:
    import urllib.request
    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        try:
            with urllib.request.urlopen(url, timeout=2) as r:
                if getattr(r, "status", 200) in (200, 302, 304):
                    return True
        except Exception:
            pass
        time.sleep(0.25)
    return False

def _start_streamlit(app_path: Path, port: int) -> subprocess.Popen:
    env = dict(os.environ)
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    env.setdefault("PYTHONUNBUFFERED", "1")

    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.address", "127.0.0.1",
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]

    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    return subprocess.Popen(
        cmd, env=env, cwd=str(app_path.parent),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        creationflags=creationflags,
    )

def _terminate_process(p: subprocess.Popen, grace_sec: float = 4.0) -> None:
    if p.poll() is not None:
        return
    try:
        if os.name == "nt":
            p.terminate()
        else:
            os.kill(p.pid, signal.SIGTERM)
    except Exception:
        pass
    t0 = time.time()
    while time.time() - t0 < grace_sec:
        if p.poll() is not None:
            return
        time.sleep(0.15)
    try:
        if os.name == "nt":
            p.kill()
        else:
            os.kill(p.pid, signal.SIGKILL)
    except Exception:
        pass

def run_desktop(title: str = "Crypto Bot Pro") -> int:
    app_path = _resource_path("dashboard/app.py")
    if not app_path.exists():
        app_path = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
    if not app_path.exists():
        raise RuntimeError(f"Missing Streamlit entry: {app_path}")

    port = _find_free_port()
    url = f"http://127.0.0.1:{port}"
    proc = _start_streamlit(app_path, port)
    ready = _wait_http_ready(url, timeout_sec=30.0)
    if not ready:
        logs = ""
        try:
            if proc.stdout:
                for _ in range(80):
                    line = proc.stdout.readline()
                    if not line:
                        break
                    logs += line
            _terminate_process(proc)
            raise RuntimeError("Streamlit failed to start.\n\nLast logs:\n" + logs[-4000:])
        except Exception:
            _terminate_process(proc)
            raise

    window = webview.create_window(title, url, width=1280, height=840)
    try:
        window.events.closed += lambda: _terminate_process(proc)
    except Exception:
        pass
    webview.start()
    _terminate_process(proc)
    return 0

if __name__ == "__main__":
    raise SystemExit(run_desktop())
