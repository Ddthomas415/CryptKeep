from __future__ import annotations

import json
import math
import os
import signal
import threading
import urllib.error
import urllib.request
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
from time import monotonic
from typing import Any

import yaml

from dashboard.services.views._explain_diagnostics import record_explain_event
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


@dataclass
class _ProbeRequest:
    token: str = field(repr=False)
    base: str
    deadline: float
    submitted: bool = False
    raw_response: Any = field(default=None, repr=False)
    status: int | None = None


_PROBE: ContextVar[_ProbeRequest | None] = ContextVar("companion_probe", default=None)


def companion_request_base(default: str) -> str:
    probe = _PROBE.get()
    return probe.base if probe is not None else default


@contextmanager
def companion_probe_request(token: str, *, base: str, timeout: float = 30):
    """Isolate one probe without changing ordinary dashboard configuration.

    The caller must first prove this loopback binding belongs to the pinned
    orchestrator. This context does not establish container ownership.
    Raw response stays in memory and must never be serialized into a receipt.
    """
    if _PROBE.get() is not None:
        raise RuntimeError("nested_probe_refused")
    if base != "http://127.0.0.1:8002":
        raise ValueError("unpinned_probe_origin")
    if not isinstance(token, str) or not token or any(c in token for c in "\r\n"):
        raise ValueError("invalid_probe_token")
    if isinstance(timeout, bool) or not math.isfinite(timeout) or not 0 < timeout <= 30:
        raise ValueError("invalid_probe_timeout")
    state = _ProbeRequest(token, base, monotonic() + timeout)
    marker = _PROBE.set(state)
    try:
        yield state
    finally:
        state.token = ""
        state.raw_response = None
        _PROBE.reset(marker)


class _NoCompanionRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _probe_http_request(req, timeout):
    """Entire open/read/decode runs in a disposable child, never the caller."""
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoCompanionRedirect())
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read(1_048_577)
            if len(raw) > 1_048_576:
                raise ValueError("probe_response_too_large")
            return {"outcome": "json_received", "status": getattr(resp, "status", None),
                    "data": json.loads(raw.decode("utf-8"))}
    except urllib.error.HTTPError as exc:
        return {"outcome": "http_error", "status": exc.code}
    except (TimeoutError, OSError, ValueError, urllib.error.URLError) as exc:
        reason = "timeout" if isinstance(exc, TimeoutError) else "invalid_json" if isinstance(exc, ValueError) else "network_error"
        return {"outcome": reason, "status": None}


def _bounded_probe_http(req, timeout):
    # Imported only for the explicit research probe, never ordinary UI requests.
    from scripts.research import companion_existing_controller as controller
    if not controller._CHILD_CONTEXT or threading.current_thread() is not threading.main_thread():
        raise OSError("probe_requires_bounded_child")
    if not math.isfinite(timeout) or timeout <= 0:
        raise TimeoutError("probe_http_deadline")
    if any(signal.getitimer(signal.ITIMER_REAL)):
        raise OSError("probe_timer_already_in_use")
    previous = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame):
        raise TimeoutError("probe_http_deadline")
    # Stay in the OUTER child's process group. A nested setsid child could
    # survive termination of its supervisor and outlive both timeout budgets.
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, timeout)
    try:
        return _probe_http_request(req, timeout)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _companion_timeout() -> float:
    try:
        value = float(os.environ.get("CK_PHASE1_API_TIMEOUT_SECONDS", "30"))
    except ValueError:
        return 30.0
    return value if math.isfinite(value) and 0 < value <= 90 else 30.0


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
    probe = _PROBE.get()
    if probe is not None:
        # Spend the budget before dispatch: errors must not enable another try.
        if probe.submitted or base_url != probe.base or path != "/v1/explain" or method != "POST":
            raise RuntimeError("probe_request_boundary")
        if monotonic() >= probe.deadline:
            raise TimeoutError("probe_deadline")
        probe.submitted = True
    companion = probe is not None or base_url.rstrip("/") == PHASE1_ORCHESTRATOR_URL
    route = "companion" if companion else "primary"
    explain = path in ("/v1/explain", "/api/v1/research/explain")
    service_token = probe.token if probe is not None else PHASE1_SERVICE_TOKEN
    if companion and not service_token:
        if explain:
            record_explain_event(route, "transport", "missing_service_token")
        return None
    if companion:
        headers["Authorization"] = f"Bearer {service_token}"
        if probe is not None:
            headers["X-CryptKeep-Probe"] = "single-cited-query-v1"
    req = urllib.request.Request(
        url,
        data=body,
        headers=headers,
        method=method,
    )
    status = None
    try:
        if probe is not None:
            result = _bounded_probe_http(req, probe.deadline - monotonic())
            status = result["status"]
            outcome = result["outcome"]
            data = result.get("data")
            if monotonic() >= probe.deadline:
                record_explain_event(route, "transport", "timeout", http_status=status)
                return None
            if explain:
                record_explain_event(route, "transport", outcome, http_status=status,
                                     payload=data if outcome == "json_received" else None)
            if outcome != "json_received":
                return None
            probe.raw_response, probe.status = data, status
            return data
        # Never forward the companion bearer to a redirect destination or an environment/system proxy.
        open_request = (
            urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoCompanionRedirect()).open
            if companion else urllib.request.urlopen
        )
        timeout = _companion_timeout() if companion else API_TIMEOUT_SECONDS
        with open_request(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None)
            data = json.loads(resp.read().decode("utf-8"))
            if explain:
                record_explain_event(route, "transport", "json_received", http_status=status, payload=data)
            return data
    except urllib.error.HTTPError as exc:
        if explain:
            record_explain_event(route, "transport", "http_error", http_status=exc.code)
        return None
    except (TimeoutError, OSError, ValueError, urllib.error.URLError) as exc:
        if explain:
            reason = "timeout" if isinstance(exc, TimeoutError) else "invalid_json" if isinstance(exc, ValueError) else "network_error"
            record_explain_event(route, "transport", reason, http_status=status)
        return None


def _request_envelope(path: str, *, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    if _PROBE.get() is not None:
        return None
    return _request_envelope_from_base(API_BASE_URL, path, method=method, payload=payload)


def _fetch_envelope(path: str) -> dict[str, Any] | None:
    return _request_envelope(path, method="GET")


