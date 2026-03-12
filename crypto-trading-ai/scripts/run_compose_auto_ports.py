#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
STACK_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.os.ports import resolve_preferred_port


DEFAULT_HOST_PORTS: dict[str, int] = {
    "POSTGRES_HOST_PORT": 5432,
    "REDIS_HOST_PORT": 6379,
    "VECTOR_HOST_PORT": 6333,
    "BACKEND_HOST_PORT": 8000,
    "FRONTEND_HOST_PORT": 3000,
}


def resolve_compose_port_env(
    env: Mapping[str, str] | None = None,
    *,
    search_limit: int = 50,
    host: str = "127.0.0.1",
) -> dict[str, str]:
    source_env = dict(env or os.environ)
    allocated: set[int] = set()
    resolved: dict[str, str] = {}

    for key, fallback in DEFAULT_HOST_PORTS.items():
        raw_value = source_env.get(key)
        try:
            requested = int(str(raw_value).strip()) if raw_value not in (None, "") else int(fallback)
        except (TypeError, ValueError):
            requested = int(fallback)

        resolution = resolve_preferred_port(host, requested, max_offset=search_limit)
        port = int(resolution.resolved_port)
        while port in allocated:
            resolution = resolve_preferred_port(host, port + 1, max_offset=search_limit)
            port = int(resolution.resolved_port)
        allocated.add(port)
        resolved[key] = str(port)

    return resolved


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    print_only = False
    if "--print-env" in args:
        print_only = True
        args.remove("--print-env")

    port_env = resolve_compose_port_env(
        os.environ,
        search_limit=int(os.environ.get("CBP_PORT_SEARCH_LIMIT", "50") or "50"),
    )

    if print_only:
        for key, value in port_env.items():
            print(f"{key}={value}")
        return 0

    env = os.environ.copy()
    env.update(port_env)
    command = ["docker", "compose", "up", "--build", *args]
    print(
        "Using host ports:",
        ", ".join(f"{key}={value}" for key, value in port_env.items()),
    )
    completed = subprocess.run(command, cwd=str(STACK_ROOT), env=env)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
