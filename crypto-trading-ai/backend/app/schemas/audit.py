from pydantic import BaseModel


class AuditEvent(BaseModel):
    id: str
    timestamp: str
    service: str
    action: str
    result: str
    request_id: str | None = None
    details: str


class AuditEventListResponse(BaseModel):
    items: list[AuditEvent]
