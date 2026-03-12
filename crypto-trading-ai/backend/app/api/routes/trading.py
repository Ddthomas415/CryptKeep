from fastapi import APIRouter, Request

from backend.app.core.envelopes import success
from backend.app.schemas.common import ApiEnvelope
from backend.app.schemas.trading import RecommendationList
from backend.app.services.trading_service import TradingService

router = APIRouter()
service = TradingService()


@router.get("/recommendations", response_model=ApiEnvelope[RecommendationList])
def recommendations(request: Request) -> dict:
    data = service.list_recommendations()
    return success(data=data, request_id=request.state.request_id)
