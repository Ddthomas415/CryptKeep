from __future__ import annotations

from fastapi import APIRouter, Query, Request

from backend.app.core.envelopes import success
from backend.app.schemas.common import ApiEnvelope
from backend.app.schemas.market import MarketCandlesResponse, MarketSnapshot
from backend.app.services.market_service import MarketService

router = APIRouter()
service = MarketService()


@router.get("/{asset}/snapshot", response_model=ApiEnvelope[MarketSnapshot])
def market_snapshot(
    asset: str,
    request: Request,
    exchange: str = Query(default="coinbase"),
) -> dict:
    data = service.get_snapshot(asset=asset, exchange=exchange)
    return success(data=data, request_id=request.state.request_id)


@router.get("/{asset}/candles", response_model=ApiEnvelope[MarketCandlesResponse])
def market_candles(
    asset: str,
    request: Request,
    exchange: str = Query(default="coinbase"),
    interval: str = Query(default="1h"),
    limit: int = Query(default=24, ge=2, le=240),
) -> dict:
    data = service.get_candles(asset=asset, exchange=exchange, interval=interval, limit=limit)
    return success(data=data, request_id=request.state.request_id)
