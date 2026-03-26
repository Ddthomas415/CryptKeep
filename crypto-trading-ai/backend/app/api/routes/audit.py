from fastapi import APIRouter, Depends, Request

from backend.app.api.deps import require_min_role
from backend.app.core.envelopes import success
from backend.app.domain.policy.roles import Role
from backend.app.schemas.audit import AuditEventListResponse
from backend.app.schemas.common import ApiEnvelope
from backend.app.services.audit_service import AuditService

router = APIRouter()
service = AuditService()


@router.get("/events", response_model=ApiEnvelope[AuditEventListResponse], dependencies=[Depends(require_min_role(Role.OWNER))])
def audit_events(request: Request, page: int = 1, page_size: int = 20) -> dict:
    data, meta = service.list_events(page=page, page_size=page_size)
    return success(data=data, meta=meta, request_id=request.state.request_id)
