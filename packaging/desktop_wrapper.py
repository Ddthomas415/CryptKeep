from __future__ import annotations

import os
import sys
import time
import socket
import subprocess
from pathlib import Path

def _find_free_port() -> int:
    s = socket.socket()
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return int(port)

def _wait_port(host: str, port: int, timeout_sec: int = 25) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        try:
            with socket.create_connection((host, port), timeout=1.0):
                return True
        except Exception:
            time.sleep(0.25)
    return False

def run():
    # Resolve repo root (works when frozen too)
    here = Path(__file__).resolve()
    root = here.parent.parent if (here.parent / "../dashboard/app.py").resolve().exists() else Path.cwd()

    app_py = (root / "dashboard" / "app.py").resolve()
    if not app_py.exists():
        raise FileNotFoundError(f"dashboard/app.py not found at: {app_py}")

    port = int(os.environ.get("CRYPTBOT_PORT") or _find_free_port())
    host = os.environ.get("CRYPTBOT_HOST", "127.0.0.1")

    env = os.environ.copy()
    env.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    env.setdefault("STREAMLIT_SERVER_PORT", str(port))
    env.setdefault("STREAMLIT_SERVER_ADDRESS", host)
    env.setdefault("STREAMLIT_SERVER_ENABLE_CORS", "false")

    # Start streamlit server
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_py), "--server.port", str(port), "--server.address", host]
    proc = subprocess.Popen(cmd, cwd=str(root), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    ok = _wait_port(host, port, timeout_sec=35)
    if not ok:
        # Dump last output for diagnosis
        out = ""
        try:
            if proc.stdout:
                for _ in range(200):
                    line = proc.stdout.readline()
                    if not line:
                        break
                    out += line
        except Exception:
            pass
        proc.terminate()
        raise RuntimeError("Streamlit server did not start in time.\n" + out[:4000])

    url = f"http://{host}:{port}"

    # Open embedded window
    import webview  # pywebview
    win = webview.create_window("CryptoBotPro", url, width=1280, height=800)

    def _on_closed():
        try:
            proc.terminate()
        except Exception:
            pass

    try:
        win.events.closed += _on_closed
    except Exception:
        # older pywebview: best-effort only
        pass

    webview.start()

if __name__ == "__main__":
    run()
