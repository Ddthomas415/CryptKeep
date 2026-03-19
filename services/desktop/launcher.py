from __future__ import annotations

import os
import subprocess
import sys

from services.app.dashboard_launch import (
    dashboard_port_search_limit,
    dashboard_streamlit_cmd,
    open_dashboard_browser,
    port_open,
    repo_root,
    resolve_dashboard_launch,
    wait_for_dashboard,
)

def main(port: int = 8502):
    ctx = resolve_dashboard_launch(
        host="127.0.0.1",
        preferred_port=int(port),
        search_limit=dashboard_port_search_limit(),
    )
    # Start Streamlit if not already running, then open browser (dev-friendly desktop smoke)
    if not port_open(ctx.host, ctx.resolved_port, timeout=0.25):
        cmd = dashboard_streamlit_cmd(ctx, python_executable=sys.executable, headless=True)
        subprocess.Popen(cmd, cwd=str(repo_root()))
        wait_for_dashboard(ctx.host, ctx.resolved_port, timeout_sec=20.0, sleep_sec=0.25)
    open_dashboard_browser(ctx)
    return 0

if __name__ == "__main__":
    main()
