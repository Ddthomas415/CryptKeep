from fastapi import APIRouter, Depends, Request

from backend.app.api.deps import require_min_role
from backend.app.core.envelopes import success
from backend.app.domain.policy.roles import Role
from backend.app.schemas.common import ApiEnvelope
from backend.app.schemas.dashboard import DashboardSummary
from backend.app.services.dashboard_service import DashboardService

router = APIRouter()
service = DashboardService()


@router.get("/summary", response_model=ApiEnvelope[DashboardSummary], dependencies=[Depends(require_min_role(Role.VIEWER))])
def dashboard_summary(request: Request) -> dict:
    data = service.get_summary()
    return success(data=data, request_id=request.state.request_id)
