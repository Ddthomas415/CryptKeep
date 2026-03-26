from fastapi import APIRouter, Depends, Request

from backend.app.api.deps import require_min_role
from backend.app.core.errors import bad_request
from backend.app.core.envelopes import success
from backend.app.domain.policy.roles import Role
from backend.app.schemas.common import ApiEnvelope
from backend.app.schemas.risk import RiskLimits, RiskLimitsUpdate, RiskSummary
from backend.app.services.risk_service import RiskService

router = APIRouter()
service = RiskService()


@router.get("/summary", response_model=ApiEnvelope[RiskSummary], dependencies=[Depends(require_min_role(Role.VIEWER))])
def risk_summary(request: Request) -> dict:
    data = service.get_summary()
    return success(data=data, request_id=request.state.request_id)


@router.get("/limits", response_model=ApiEnvelope[RiskLimits], dependencies=[Depends(require_min_role(Role.OWNER))])
def risk_limits(request: Request) -> dict:
    data = service.get_limits()
    return success(data=data, request_id=request.state.request_id)


@router.put("/limits", response_model=ApiEnvelope[RiskLimits], dependencies=[Depends(require_min_role(Role.OWNER))])
def update_risk_limits(request: Request, payload: RiskLimitsUpdate) -> dict:
    patch = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not patch:
        raise bad_request("At least one risk limit field is required.", code="EMPTY_RISK_LIMITS_UPDATE")

    data = service.update_limits(patch=patch)
    return success(data=data, request_id=request.state.request_id)
