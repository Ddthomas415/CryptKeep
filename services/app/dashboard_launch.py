from __future__ import annotations

import os
import socket
import sys
import time
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from services.os.ports import resolve_preferred_port


@dataclass(frozen=True)
class DashboardLaunchContext:
    host: str
    requested_port: int
    resolved_port: int
    requested_available: bool
    auto_switched: bool
    url: str
    app_path: str


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def dashboard_app_path() -> Path:
    return (repo_root() / "dashboard" / "app.py").resolve()


def dashboard_default_port(*, fallback: int = 8502) -> int:
    for key in ("CBP_DASHBOARD_PORT", "APP_PORT", "CBP_UI_PORT", "STREAMLIT_SERVER_PORT"):
        raw = str(os.environ.get(key) or "").strip()
        if not raw:
            continue
        try:
            port = int(raw)
        except Exception:
            continue
        if port > 0:
            return port
    return int(fallback)


def dashboard_port_search_limit(*, fallback: int = 50) -> int:
    raw = str(os.environ.get("CBP_PORT_SEARCH_LIMIT") or "").strip()
    if not raw:
        return int(fallback)
    try:
        value = int(raw)
    except Exception:
        return int(fallback)
    return max(1, value)


def resolve_dashboard_launch(
    *,
    host: str = "127.0.0.1",
    preferred_port: int,
    search_limit: int | None = None,
) -> DashboardLaunchContext:
    normalized_host = str(host or "127.0.0.1").strip() or "127.0.0.1"
    resolution = resolve_preferred_port(
        normalized_host,
        int(preferred_port),
        max_offset=int(search_limit if search_limit is not None else dashboard_port_search_limit()),
    )
    resolved_port = int(resolution.resolved_port)
    return DashboardLaunchContext(
        host=resolution.host,
        requested_port=int(resolution.requested_port),
        resolved_port=resolved_port,
        requested_available=bool(resolution.requested_available),
        auto_switched=bool(resolution.auto_switched),
        url=f"http://{resolution.host}:{resolved_port}",
        app_path=str(dashboard_app_path()),
    )


def dashboard_streamlit_cmd(
    ctx: DashboardLaunchContext,
    *,
    python_executable: str | None = None,
    headless: bool = True,
) -> list[str]:
    cmd = [
        str(python_executable or sys.executable),
        "-m",
        "streamlit",
        "run",
        str(ctx.app_path),
        "--server.address",
        str(ctx.host),
        "--server.port",
        str(int(ctx.resolved_port)),
    ]
    if bool(headless):
        cmd.extend(["--server.headless", "true"])
    return cmd


def dashboard_streamlit_env(
    ctx: DashboardLaunchContext,
    *,
    base_env: Mapping[str, str] | None = None,
    headless: bool = True,
) -> dict[str, str]:
    env = dict(base_env or os.environ)
    env["STREAMLIT_SERVER_ADDRESS"] = str(ctx.host)
    env["STREAMLIT_SERVER_PORT"] = str(int(ctx.resolved_port))
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    if bool(headless):
        env["STREAMLIT_SERVER_HEADLESS"] = "true"
    return env


def port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((str(host), int(port)), timeout=float(timeout)):
            return True
    except OSError:
        return False


def wait_for_dashboard(host: str, port: int, *, timeout_sec: float = 20.0, sleep_sec: float = 0.25) -> bool:
    deadline = time.time() + max(0.0, float(timeout_sec))
    while time.time() <= deadline:
        if port_open(host, port, timeout=min(1.0, max(0.1, float(sleep_sec)))):
            return True
        time.sleep(max(0.05, float(sleep_sec)))
    return port_open(host, port, timeout=min(1.0, max(0.1, float(sleep_sec))))


def open_dashboard_browser(ctx: DashboardLaunchContext) -> None:
    webbrowser.open(ctx.url)
