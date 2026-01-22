from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

def _pick_free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return int(port)

def _repo_root() -> Path:
    # PyInstaller sets sys._MEIPASS; our repo files are bundled inside.
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[1]

def main():
    # Force consistent paths
    root = _repo_root()
    app_path = root / "dashboard" / "app.py"
    if not app_path.exists():
        print(f"ERROR: dashboard app not found at: {app_path}")
        sys.exit(2)

    port = _pick_free_port()
    url = f"http://127.0.0.1:{port}"

    # Start browser shortly after server starts
    def _open_browser():
        time.sleep(1.0)
        try:
            webbrowser.open(url, new=1, autoraise=True)
        except Exception:
            pass

    threading.Thread(target=_open_browser, daemon=True).start()

    # Run Streamlit programmatically
    try:
        import streamlit.web.cli as stcli
    except Exception as e:
        print(f"ERROR: streamlit import failed: {type(e).__name__}: {e}")
        sys.exit(3)

    # Equivalent to: streamlit run dashboard/app.py --server.port <port> --server.headless true
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.address", "127.0.0.1",
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]
    # Note: closing the browser tab does NOT stop the app; user closes the app process.
    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
