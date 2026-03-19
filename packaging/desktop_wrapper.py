from __future__ import annotations

import os
import subprocess
from pathlib import Path

from services.app.dashboard_launch import (
    dashboard_port_search_limit,
    dashboard_streamlit_cmd,
    dashboard_streamlit_env,
    resolve_dashboard_launch,
    wait_for_dashboard,
)

def run():
    # Resolve repo root (works when frozen too)
    here = Path(__file__).resolve()
    root = here.parent.parent if (here.parent / "../dashboard/app.py").resolve().exists() else Path.cwd()

    app_py = (root / "dashboard" / "app.py").resolve()
    if not app_py.exists():
        raise FileNotFoundError(f"dashboard/app.py not found at: {app_py}")

    host = os.environ.get("CRYPTBOT_HOST", "127.0.0.1")
    requested_port = int(os.environ.get("CRYPTBOT_PORT") or os.environ.get("STREAMLIT_SERVER_PORT") or "8502")
    ctx = resolve_dashboard_launch(
        host=host,
        preferred_port=requested_port,
        search_limit=dashboard_port_search_limit(),
    )

    env = dashboard_streamlit_env(ctx, base_env=os.environ, headless=True)
    env.setdefault("STREAMLIT_SERVER_ENABLE_CORS", "false")

    # Start streamlit server
    cmd = dashboard_streamlit_cmd(ctx, headless=True)
    proc = subprocess.Popen(cmd, cwd=str(root), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    ok = wait_for_dashboard(ctx.host, ctx.resolved_port, timeout_sec=35.0)
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

    url = ctx.url

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
