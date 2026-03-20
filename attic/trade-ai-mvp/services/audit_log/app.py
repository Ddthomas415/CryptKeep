from __future__ import annotations

from fastapi import FastAPI

from shared.config import get_settings
from shared.db import SessionLocal, check_db_connection
from shared.logging import get_logger
from shared.models.audit import AuditLog
from shared.schemas.audit import AuditLogIn

settings = get_settings("audit_log")
logger = get_logger("audit_log", settings.log_level)
app = FastAPI(title="audit_log")


@app.on_event("startup")
def startup() -> None:
    ok = check_db_connection()
    logger.info("startup_db_check", extra={"context": {"ok": ok}})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/audit/log")
def audit_log(entry: AuditLogIn) -> dict[str, str]:
    with SessionLocal() as db:
        row = AuditLog(
            service_name=entry.service_name,
            event_type=entry.event_type,
            request_id=entry.request_id,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            level=entry.level,
            message=entry.message,
            payload=entry.payload,
        )
        db.add(row)
        db.commit()

    logger.info(
        "audit_event",
        extra={
            "context": {
                "service_name": entry.service_name,
                "event_type": entry.event_type,
                "level": entry.level,
            }
        },
    )
    return {"status": "ok"}
