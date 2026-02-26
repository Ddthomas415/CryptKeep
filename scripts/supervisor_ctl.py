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

from services.process.supervisor_process import start, status, stop

REPO = Path(__file__).resolve().parents[1]


def _ui_port_default() -> int:
    raw = (
        os.environ.get("CBP_SUPERVISOR_UI_PORT")
        or os.environ.get("CBP_UI_PORT")
        or "8501"
    )
    try:
        return int(raw)
    except Exception:
        return 8501


def _build_streamlit_cmd(*, host: str | None, port: int) -> list[str]:
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(REPO / "dashboard" / "app.py"),
        "--server.port",
        str(int(port)),
    ]
    host_v = (host or "").strip()
    if host_v:
        cmd.extend(["--server.address", host_v])
    return cmd


def _build_watchdog_cmd(*, interval: int) -> list[str]:
    return [
        sys.executable,
        str(REPO / "scripts" / "watchdog.py"),
        "--loop",
        "--interval",
        str(int(interval)),
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["start", "status", "stop"])
    ap.add_argument("--host", default=os.environ.get("CBP_SUPERVISOR_UI_HOST") or "")
    ap.add_argument("--port", type=int, default=_ui_port_default())
    ap.add_argument(
        "--interval",
        type=int,
        default=int(os.environ.get("CBP_WATCHDOG_INTERVAL", "15")),
    )
    ap.add_argument("--hard", action="store_true")
    args = ap.parse_args()

    if args.cmd == "start":
        payload = start(
            streamlit_cmd=_build_streamlit_cmd(
                host=str(args.host or ""),
                port=int(args.port),
            ),
            watchdog_cmd=_build_watchdog_cmd(interval=int(args.interval)),
            cwd=REPO,
        )
        print(payload)
        return 0 if bool(payload.get("ok")) else 2

    if args.cmd == "status":
        payload = status()
        print(payload)
        return 0 if bool(payload.get("ok")) else 2

    if args.cmd == "stop":
        payload = stop(hard=bool(args.hard))
        print(payload)
        return 0 if bool(payload.get("ok")) else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
