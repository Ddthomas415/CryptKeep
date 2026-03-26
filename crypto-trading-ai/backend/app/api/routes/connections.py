from fastapi import APIRouter, Depends, Request

from backend.app.api.deps import require_min_role
from backend.app.core.envelopes import success
from backend.app.domain.policy.roles import Role
from backend.app.schemas.common import ApiEnvelope
from backend.app.schemas.connections import (
    ConnectionTestResult,
    ExchangeConnectionListResponse,
    ExchangeSaveRequest,
    ExchangeSaveResponse,
    ExchangeTestRequest,
)
from backend.app.services.connections_service import ConnectionsService

router = APIRouter()
service = ConnectionsService()


@router.get("/exchanges", response_model=ApiEnvelope[ExchangeConnectionListResponse], dependencies=[Depends(require_min_role(Role.VIEWER))])
def list_exchanges(request: Request) -> dict:
    data = service.list_exchanges()
    return success(data=data, request_id=request.state.request_id)


@router.post("/exchanges/test", response_model=ApiEnvelope[ConnectionTestResult], dependencies=[Depends(require_min_role(Role.ANALYST))])
def test_exchange(request: Request, payload: ExchangeTestRequest) -> dict:
    data = service.test_exchange(provider=payload.provider, environment=payload.environment)
    return success(data=data, request_id=request.state.request_id)


@router.post("/exchanges", response_model=ApiEnvelope[ExchangeSaveResponse], dependencies=[Depends(require_min_role(Role.OWNER))])
def save_exchange(request: Request, payload: ExchangeSaveRequest) -> dict:
    data = service.save_exchange(
        provider=payload.provider,
        label=payload.label,
        environment=payload.environment,
    )
    return success(data=data, request_id=request.state.request_id)
