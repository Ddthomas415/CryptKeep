from __future__ import annotations

import uuid
from typing import Any

import httpx

from shared.config import get_settings
from shared.logging import configure_logging
from shared.probe import PROBE_PROFILE, probe_active, probe_headers, require_probe_origin


_settings = get_settings()
_logger = configure_logging("audit-client", _settings.log_level)


async def emit_audit_event(
    service: str,
    action: str,
    *,
    status: str = "ok",
    payload: dict[str, Any] | None = None,
    correlation_id: str | None = None,
) -> None:
    body = {
        "service": service,
        "action": action,
        "status": status,
        "correlation_id": correlation_id or str(uuid.uuid4()),
        "payload": payload or {},
    }
    if probe_active():
        body["payload"] = {**body["payload"], "probe_protocol": PROBE_PROFILE}
    url = f"{_settings.audit_service_url.rstrip('/')}/v1/audit/events"
    headers: dict[str, str] = {}
    token = str(getattr(_settings, "service_token", "") or "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    headers.update(probe_headers())
    try:
        require_probe_origin(url)
        client_options: dict[str, Any] = {}
        if probe_active():
            client_options = {
                "trust_env": False, "follow_redirects": False,
                "transport": httpx.AsyncHTTPTransport(retries=0, trust_env=False),
            }
        async with httpx.AsyncClient(timeout=_settings.request_timeout_seconds, **client_options) as client:
            await client.post(url, json=body, headers=headers)
    except Exception as exc:
        _logger.warning(
            "audit_emit_failed",
            extra={"context": {"service": service, "action": action, "error_type": type(exc).__name__}},
        )

