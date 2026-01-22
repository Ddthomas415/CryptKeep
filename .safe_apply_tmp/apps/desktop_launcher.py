from __future__ import annotations

import os
import sys
import time
import subprocess
import webbrowser
from dataclasses import dataclass

@dataclass(frozen=True)
class LauncherConfig:
    app_path: str = "dashboard/app.py"
    host: str = "127.0.0.1"
    port: int = 8501
    headless: bool = True
    open_browser: bool = True

def _python() -> str:
    return sys.executable

def run_streamlit(cfg: LauncherConfig) -> int:
    # Streamlit must be launched as a subprocess for stability under packaging.
    cmd = [
        _python(), "-m", "streamlit", "run", cfg.app_path,
        "--server.address", cfg.host,
        "--server.port", str(cfg.port),
        "--server.headless", "true" if cfg.headless else "false",
        "--browser.gatherUsageStats", "false",
    ]

    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    p = subprocess.Popen(cmd, env=env)
    try:
        # Give server a moment to come up
        time.sleep(1.5)
        if cfg.open_browser:
            webbrowser.open(f"http://{cfg.host}:{cfg.port}", new=1)
        return p.wait()
    except KeyboardInterrupt:
        try:
            p.terminate()
        except Exception:
            pass
        return 130

def main() -> int:
    port = int(os.environ.get("CRYPTOBOT_PORT", "8501"))
    host = os.environ.get("CRYPTOBOT_HOST", "127.0.0.1")
    cfg = LauncherConfig(port=port, host=host)
    return run_streamlit(cfg)

if __name__ == "__main__":
    raise SystemExit(main())
