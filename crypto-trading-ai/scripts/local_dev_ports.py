#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
STACK_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.os.ports import PortResolution, resolve_preferred_port

PORT_STATE_PATH = STACK_ROOT / ".runtime" / "local_dev_ports.json"


def _normalize_host(host: str | None, *, fallback: str) -> str:
    value = str(host or "").strip()
    return value or fallback


def load_runtime_ports() -> dict[str, Any]:
    try:
        return json.loads(PORT_STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_runtime_ports(payload: Mapping[str, Any]) -> None:
    PORT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged = load_runtime_ports()
    merged.update(dict(payload))
    PORT_STATE_PATH.write_text(json.dumps(merged, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_backend_binding(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source_env = dict(env or os.environ)
    host = _normalize_host(source_env.get("API_HOST"), fallback="0.0.0.0")
    requested_port = int(
        source_env.get("BACKEND_HOST_PORT")
        or source_env.get("API_PORT")
        or "8000"
    )
    resolution = resolve_preferred_port(
        host,
        requested_port,
        max_offset=int(source_env.get("CBP_PORT_SEARCH_LIMIT", "50") or "50"),
    )
    return {
        "host": host,
        "resolution": resolution,
    }


def resolve_frontend_binding(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source_env = dict(env or os.environ)
    host = _normalize_host(source_env.get("FRONTEND_HOST"), fallback="0.0.0.0")
    requested_port = int(source_env.get("FRONTEND_HOST_PORT") or "3000")
    resolution = resolve_preferred_port(
        host,
        requested_port,
        max_offset=int(source_env.get("CBP_PORT_SEARCH_LIMIT", "50") or "50"),
    )

    runtime = load_runtime_ports()
    backend_port = int(
        source_env.get("BACKEND_HOST_PORT")
        or runtime.get("backend_port")
        or source_env.get("API_PORT")
        or "8000"
    )
    backend_host = _normalize_host(
        source_env.get("BACKEND_HOST"),
        fallback=str(runtime.get("backend_host") or "127.0.0.1"),
    )

    return {
        "host": host,
        "resolution": resolution,
        "backend_url": f"http://{backend_host}:{backend_port}",
    }


def resolution_payload(resolution: PortResolution) -> dict[str, Any]:
    return {
        "host": resolution.host,
        "requested_port": int(resolution.requested_port),
        "resolved_port": int(resolution.resolved_port),
        "requested_available": bool(resolution.requested_available),
        "auto_switched": bool(resolution.auto_switched),
    }
