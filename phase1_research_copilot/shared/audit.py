from __future__ import annotations

import uuid
from typing import Any

import httpx

from shared.config import get_settings
from shared.logging import configure_logging


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
    url = f"{_settings.audit_service_url.rstrip('/')}/v1/audit/events"
    try:
        async with httpx.AsyncClient(timeout=_settings.request_timeout_seconds) as client:
            await client.post(url, json=body)
    except Exception as exc:
        _logger.warning(
            "audit_emit_failed",
            extra={"context": {"service": service, "action": action, "error": str(exc)}},
        )
