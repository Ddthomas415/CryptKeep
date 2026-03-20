from __future__ import annotations

import asyncio
from typing import Any

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None

from shared.config import Settings


async def emit_audit_event(
    *,
    settings: Settings,
    service_name: str,
    event_type: str,
    message: str,
    payload: dict[str, Any] | None = None,
    request_id: str | None = None,
    level: str = "INFO",
) -> None:
    if httpx is None:
        return
    body = {
        "service_name": service_name,
        "event_type": event_type,
        "request_id": request_id,
        "level": level,
        "message": message,
        "payload": payload or {},
    }
    for _ in range(2):
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                await client.post(f"{settings.audit_log_url}/audit/log", json=body)
            return
        except Exception:
            await asyncio.sleep(0.15)
