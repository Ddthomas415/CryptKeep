#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from local_dev_ports import resolution_payload, resolve_frontend_binding, save_runtime_ports

STACK_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    binding = resolve_frontend_binding(os.environ)
    resolution = binding["resolution"]
    resolved_port = int(resolution.resolved_port)
    host = str(binding["host"])
    backend_url = str(binding["backend_url"])

    save_runtime_ports(
        {
            "frontend_host": "127.0.0.1" if host == "0.0.0.0" else host,
            "frontend_port": resolved_port,
            "frontend_resolution": resolution_payload(resolution),
            "frontend_backend_url": backend_url,
        }
    )

    env = os.environ.copy()
    env["VITE_DEV_PROXY_TARGET"] = backend_url

    print(
        f"Frontend port: requested {resolution.requested_port}, resolved {resolved_port}"
        f"{' (auto-switched)' if resolution.auto_switched else ''}"
    )
    print(f"Frontend API proxy target: {backend_url}")

    command = [
        "pnpm",
        "dev",
        "--host",
        host,
        "--port",
        str(resolved_port),
        *args,
    ]
    completed = subprocess.run(command, cwd=str(STACK_ROOT / "frontend"), env=env)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
