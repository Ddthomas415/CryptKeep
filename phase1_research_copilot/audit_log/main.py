from __future__ import annotations

import json
import hmac
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Query
from pydantic import BaseModel

from shared.config import get_settings
from shared.db import Database
from shared.logging import configure_logging
from shared.models import AuditEvent

settings = get_settings()
logger = configure_logging(settings.service_name or "audit-log", settings.log_level)
db = Database(settings.database_url)

app = FastAPI(title="audit-log", version="0.1.0")

def _require_service_token(authorization: str | None) -> None:
    expected = str(getattr(settings, "service_token", "") or "")
    if not expected:
        raise HTTPException(status_code=503, detail="service_auth_not_configured")
    supplied = str(authorization or "").strip()
    prefix = "Bearer "
    if not supplied.startswith(prefix):
        raise HTTPException(status_code=401, detail="unauthorized")
    token = supplied[len(prefix):].strip()
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="unauthorized")


class AuditEventResponse(BaseModel):
    ok: bool
    event_id: int | None = None


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"service": "audit-log", **db.health()}


@app.post("/v1/audit/events", response_model=AuditEventResponse)
def create_event(event: AuditEvent, authorization: str | None = Header(default=None, alias="Authorization")) -> AuditEventResponse:
    _require_service_token(authorization)
    row = db.fetch_one(
        """
        INSERT INTO audit_events (event_ts, service, action, status, correlation_id, payload)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        RETURNING id
        """,
        (
            datetime.now(timezone.utc),
            event.service,
            event.action,
            event.status,
            event.correlation_id,
            json.dumps(event.payload),
        ),
    )
    event_id = int(row["id"]) if row else None
    logger.info(
        "audit_event_created",
        extra={
            "context": {
                "event_id": event_id,
                "service": event.service,
                "action": event.action,
                "status": event.status,
                "correlation_id": event.correlation_id,
            }
        },
    )
    return AuditEventResponse(ok=True, event_id=event_id)


@app.get("/v1/audit/events/recent")
def recent_events(limit: int = Query(default=50, ge=1, le=500), authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
    _require_service_token(authorization)
    rows = db.fetch_all(
        """
        SELECT id, event_ts, service, action, status, correlation_id, payload
        FROM audit_events
        ORDER BY event_ts DESC
        LIMIT %s
        """,
        (limit,),
    )
    return {"ok": True, "count": len(rows), "events": rows}
