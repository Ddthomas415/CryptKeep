from fastapi import APIRouter, Request

from backend.app.core.envelopes import success
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


@router.get("/exchanges", response_model=ApiEnvelope[ExchangeConnectionListResponse])
def list_exchanges(request: Request) -> dict:
    data = service.list_exchanges()
    return success(data=data, request_id=request.state.request_id)


@router.post("/exchanges/test", response_model=ApiEnvelope[ConnectionTestResult])
def test_exchange(request: Request, payload: ExchangeTestRequest) -> dict:
    data = service.test_exchange(provider=payload.provider, environment=payload.environment)
    return success(data=data, request_id=request.state.request_id)


@router.post("/exchanges", response_model=ApiEnvelope[ExchangeSaveResponse])
def save_exchange(request: Request, payload: ExchangeSaveRequest) -> dict:
    data = service.save_exchange(
        provider=payload.provider,
        label=payload.label,
        environment=payload.environment,
    )
    return success(data=data, request_id=request.state.request_id)
