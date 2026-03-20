from __future__ import annotations

from pydantic import BaseModel, Field


class AuditLogIn(BaseModel):
    service_name: str
    event_type: str
    request_id: str | None = None
    entity_type: str | None = None
    entity_id: str | None = None
    level: str = "INFO"
    message: str
    payload: dict = Field(default_factory=dict)
