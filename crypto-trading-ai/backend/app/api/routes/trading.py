from fastapi import APIRouter, Depends, Request

from backend.app.api.deps import require_min_role
from backend.app.core.envelopes import success
from backend.app.domain.policy.roles import Role
from backend.app.schemas.common import ApiEnvelope
from backend.app.schemas.trading import RecommendationList
from backend.app.services.trading_service import TradingService

router = APIRouter()
service = TradingService()


@router.get("/recommendations", response_model=ApiEnvelope[RecommendationList], dependencies=[Depends(require_min_role(Role.VIEWER))])
def recommendations(request: Request) -> dict:
    data = service.list_recommendations()
    return success(data=data, request_id=request.state.request_id)
