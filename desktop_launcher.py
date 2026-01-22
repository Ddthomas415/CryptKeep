from __future__ import annotations
import os
import sys
import webbrowser
from pathlib import Path
from services.os.app_paths import code_root, ensure_dirs

def _app_path() -> str:
    # dashboard/app.py is bundled as data into the frozen app
    return str((code_root() / "dashboard" / "app.py").resolve())

def main():
    ensure_dirs()
    host = os.getenv("CBP_HOST", "127.0.0.1")
    port = os.getenv("CBP_PORT", "8501")
    # Open browser to local URL (best-effort)
    try:
        webbrowser.open(f"http://{host}:{port}", new=1)
    except Exception:
        pass
    # Start Streamlit (bootstrap)
    import streamlit.web.bootstrap as bootstrap
    bootstrap.run(_app_path(), "streamlit run", [], {"server.address": host, "server.port": int(port), "browser.gatherUsageStats": False})

if __name__ == "__main__":
    main()
