from __future__ import annotations

# CBP_BOOTSTRAP_SYS_PATH
import sys
from pathlib import Path

try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

ROOT = add_repo_root_to_syspath(Path(__file__).resolve().parent)

import argparse
import os
import subprocess

from services.app.dashboard_launch import (
    dashboard_default_port,
    dashboard_port_search_limit,
    dashboard_streamlit_cmd,
    dashboard_streamlit_env,
    open_dashboard_browser,
    port_open,
    repo_root,
    resolve_dashboard_launch,
    wait_for_dashboard,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run the dashboard and auto-switch to the next available port when needed.")
    ap.add_argument("--host", default=os.environ.get("CBP_DASHBOARD_HOST") or "127.0.0.1")
    ap.add_argument("--port", type=int, default=dashboard_default_port())
    ap.add_argument("--open", action="store_true", help="Open the dashboard URL in the default browser after startup")
    ap.add_argument("--print-url", action="store_true", help="Print the resolved dashboard URL before launch")
    ap.set_defaults(headless=True)
    ap.add_argument("--no-headless", action="store_false", dest="headless", help="Run Streamlit with browser mode enabled")
    ap.add_argument("--wait-sec", type=float, default=25.0, help="How long to wait for the dashboard port after launch")
    args = ap.parse_args(argv)

    ctx = resolve_dashboard_launch(
        host=str(args.host or "127.0.0.1"),
        preferred_port=int(args.port),
        search_limit=dashboard_port_search_limit(),
    )
    if bool(args.print_url):
        print(ctx.url)
    if ctx.auto_switched:
        print(f"Requested dashboard port {ctx.requested_port} is busy. Using {ctx.resolved_port} instead.")
    else:
        print(f"Using dashboard port {ctx.resolved_port}.")

    cmd = dashboard_streamlit_cmd(ctx, python_executable=sys.executable, headless=bool(args.headless))
    env = dashboard_streamlit_env(ctx, headless=bool(args.headless))
    proc = subprocess.Popen(cmd, cwd=str(repo_root()), env=env)

    if not wait_for_dashboard(ctx.host, ctx.resolved_port, timeout_sec=float(args.wait_sec)):
        if proc.poll() is not None:
            return int(proc.returncode or 1)
        print(
            f"Dashboard process started but {ctx.url} was not reachable within {float(args.wait_sec):g}s.",
            file=sys.stderr,
        )
    elif bool(args.open) and port_open(ctx.host, ctx.resolved_port):
        open_dashboard_browser(ctx)

    try:
        return int(proc.wait())
    except KeyboardInterrupt:
        try:
            proc.terminate()
        except Exception:
            pass
        try:
            return int(proc.wait(timeout=5))
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
            return 130


if __name__ == "__main__":
    raise SystemExit(main())
