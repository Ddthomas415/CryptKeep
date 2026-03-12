#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from local_dev_ports import resolution_payload, resolve_backend_binding, save_runtime_ports

STACK_ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    binding = resolve_backend_binding(os.environ)
    resolution = binding["resolution"]
    resolved_port = int(resolution.resolved_port)
    host = str(binding["host"])

    save_runtime_ports(
        {
            "backend_host": "127.0.0.1" if host == "0.0.0.0" else host,
            "backend_port": resolved_port,
            "backend_resolution": resolution_payload(resolution),
        }
    )

    print(
        f"Backend port: requested {resolution.requested_port}, resolved {resolved_port}"
        f"{' (auto-switched)' if resolution.auto_switched else ''}"
    )
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        host,
        "--port",
        str(resolved_port),
        "--reload",
        *args,
    ]
    completed = subprocess.run(command, cwd=str(STACK_ROOT))
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
