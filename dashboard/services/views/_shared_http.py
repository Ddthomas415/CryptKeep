from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml

from dashboard.services.intelligence import build_opportunity_snapshot
from services.admin.config_editor import CONFIG_PATH, load_user_yaml, save_user_yaml
from services.execution.live_arming import set_live_enabled
from services.setup.config_manager import DEFAULT_CFG, deep_merge

REPO_ROOT = Path(__file__).resolve().parents[2]
API_BASE_URL = os.environ.get("CK_API_BASE_URL", "http://localhost:8000").rstrip("/")
PHASE1_ORCHESTRATOR_URL = os.environ.get("CK_PHASE1_ORCHESTRATOR_URL", "http://localhost:8002").rstrip("/")
PHASE1_SERVICE_TOKEN = (
    os.environ.get("CK_PHASE1_SERVICE_TOKEN")
    or os.environ.get("SERVICE_TOKEN")
    or ""
).strip()
API_TIMEOUT_SECONDS = float(os.environ.get("CK_API_TIMEOUT_SECONDS", "0.6"))


def _read_mock_envelope(filename: str) -> dict[str, Any] | None:
    path = REPO_ROOT / "sample_data" / "mock-data" / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _request_envelope_from_base(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    url = f"{base_url}{path}"
    body: bytes | None = None
    headers = {
        "Accept": "application/json",
        "User-Agent": "CryptKeepDashboard/1.0",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if base_url.rstrip("/") == PHASE1_ORCHESTRATOR_URL and PHASE1_SERVICE_TOKEN:
        headers["Authorization"] = f"Bearer {PHASE1_SERVICE_TOKEN}"
    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT_SECONDS) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (TimeoutError, OSError, ValueError, urllib.error.URLError):
        return None


def _request_envelope(path: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    return _request_envelope_from_base(API_BASE_URL, path, method=method, payload=payload)


def _fetch_envelope(path: str) -> dict[str, Any] | None:
    return _request_envelope(path, method="GET")


