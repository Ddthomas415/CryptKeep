from __future__ import annotations

import sys
import time
import socket
import webbrowser
from pathlib import Path

from services.logging.app_logger import configure_logging, get_logger
from services.process.supervisor_process import start as sup_start, stop as sup_stop, status as sup_status

logger = get_logger("launch_supervisor")
ROOT = Path(__file__).resolve().parents[1]

def _find_dashboard_entry() -> Path:
    for p in [ROOT / "dashboard" / "app.py", ROOT / "dashboard" / "main_app.py", ROOT / "app" / "app.py"]:
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
    configure_logging()
    entry = _find_dashboard_entry()
    port = _free_port(8501)
    url = f"http://localhost:{port}"

    streamlit_cmd = [
        sys.executable, "-m", "streamlit", "run", str(entry),
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]
    watchdog_cmd = [sys.executable, "scripts/watchdog.py", "--loop", "--interval", "15"]

    st = sup_status()
    if st.get("cockpit", {}).get("alive") or st.get("watchdog", {}).get("alive"):
        logger.warning("Supervisor already running: %s", st)
        try:
            webbrowser.open(url, new=1, autoraise=True)
        except Exception:
            pass
        # Keep this process alive until user closes it
        try:
            while True:
                time.sleep(2.0)
        except KeyboardInterrupt:
            pass
        return 0

    out = sup_start(streamlit_cmd=streamlit_cmd, watchdog_cmd=watchdog_cmd, cwd=ROOT)
    logger.info("Supervisor started: %s", out)

    time.sleep(0.8)
    try:
        webbrowser.open(url, new=1, autoraise=True)
    except Exception:
        pass

    try:
        # Block here; on close/ctrl-c we stop children
        while True:
            time.sleep(1.5)
    except KeyboardInterrupt:
        logger.info("Supervisor stopping (keyboard interrupt)")
    finally:
        sup_stop(hard=True)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
