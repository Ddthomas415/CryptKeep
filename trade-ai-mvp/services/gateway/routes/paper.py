from __future__ import annotations

import asyncio
from typing import Any

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None
from fastapi import APIRouter, HTTPException

from shared.audit_client import emit_audit_event
from shared.config import get_settings
from shared.logging import get_logger
from shared.schemas.paper import (
    PaperEquitySeriesResponse,
    PaperEquitySnapshotResponse,
    PaperFillListResponse,
    PaperPerformanceRollupListResponse,
    PaperPerformanceRollupRefreshResponse,
    PaperPerformanceResponse,
    PaperReadinessResponse,
    PaperReplayRequest,
    PaperReplayResponse,
    PaperRetentionResponse,
    PaperShadowCompareRequest,
    PaperShadowCompareResponse,
    PaperOrderCancelResponse,
    PaperOrderCreateRequest,
    PaperOrderListResponse,
    PaperOrderOut,
    PaperPortfolioSummaryResponse,
)

settings = get_settings("gateway")
logger = get_logger("gateway.paper", settings.log_level)
router = APIRouter(prefix="/paper", tags=["paper"])


def _extract_detail(exc: Exception) -> tuple[int, str]:
    if httpx is not None and isinstance(exc, httpx.HTTPStatusError):
        status = int(exc.response.status_code)
        detail = "execution_sim request failed"
        try:
            body = exc.response.json()
            detail = str(body.get("detail") or detail)
        except Exception:
            detail = exc.response.text or detail
        return status, detail
    return 503, "execution_sim unavailable"


async def _call_execution_sim(
    *,
    method: str,
    path: str,
    json_payload: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    retries: int = 2,
) -> dict[str, Any]:
    if httpx is None:
        raise RuntimeError("httpx_missing")
    url = f"{settings.execution_sim_url}{path}"
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                if method == "GET":
                    resp = await client.get(url, params=params)
                else:
                    resp = await client.post(url, json=json_payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            last_err = exc
            if httpx is not None and isinstance(exc, httpx.HTTPStatusError):
                raise
            await asyncio.sleep(0.25)
    raise RuntimeError(str(last_err) if last_err else "execution_sim_unavailable")


@router.post("/orders", response_model=PaperOrderOut)
async def submit_order(req: PaperOrderCreateRequest) -> PaperOrderOut:
    if settings.paper_order_require_approval:
        approved = bool((req.metadata or {}).get("user_approved"))
        if not approved:
            raise HTTPException(status_code=403, detail="paper order requires user approval")
    try:
        out = await _call_execution_sim(method="POST", path="/paper/orders", json_payload=req.model_dump())
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="paper_order_submit",
            message="Gateway forwarded paper order submit",
            payload={"symbol": req.symbol, "side": req.side, "order_type": req.order_type},
        )
        return PaperOrderOut(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        logger.error("paper_order_submit_failed", extra={"context": {"status": status, "error": str(exc)}})
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="paper_order_submit_failed",
            message="Gateway paper order submit failed",
            payload={"symbol": req.symbol, "error": str(exc)},
            level="ERROR",
        )
        raise HTTPException(status_code=status, detail=detail) from exc


@router.get("/orders", response_model=PaperOrderListResponse)
async def list_orders(
    symbol: str | None = None,
    status: str | None = None,
    limit: int = 50,
    since: str | None = None,
    cursor: str | None = None,
    sort: str = "desc",
) -> PaperOrderListResponse:
    params: dict[str, Any] = {"limit": limit, "sort": sort}
    if symbol:
        params["symbol"] = symbol
    if status:
        params["status"] = status
    if since:
        params["since"] = since
    if cursor:
        params["cursor"] = cursor
    try:
        out = await _call_execution_sim(method="GET", path="/paper/orders", params=params)
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="paper_order_list",
            message="Gateway forwarded paper order list",
            payload={"symbol": symbol, "status": status, "limit": limit, "sort": sort, "cursor": cursor},
        )
        return PaperOrderListResponse(**out)
    except Exception as exc:
        status_code, detail = _extract_detail(exc)
        logger.error("paper_order_list_failed", extra={"context": {"error": str(exc), "status": status_code}})
        raise HTTPException(status_code=status_code, detail=detail) from exc


@router.get("/orders/{order_id}", response_model=PaperOrderOut)
async def get_order(order_id: str) -> PaperOrderOut:
    try:
        out = await _call_execution_sim(method="GET", path=f"/paper/orders/{order_id}")
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="paper_order_get",
            message="Gateway forwarded paper order lookup",
            payload={"order_id": order_id},
        )
        return PaperOrderOut(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        logger.error("paper_order_get_failed", extra={"context": {"order_id": order_id, "error": str(exc)}})
        raise HTTPException(status_code=status, detail=detail) from exc


@router.post("/orders/{order_id}/cancel", response_model=PaperOrderCancelResponse)
async def cancel_order(order_id: str) -> PaperOrderCancelResponse:
    try:
        out = await _call_execution_sim(method="POST", path=f"/paper/orders/{order_id}/cancel", json_payload={})
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="paper_order_cancel",
            message="Gateway forwarded paper order cancel",
            payload={"order_id": order_id},
        )
        return PaperOrderCancelResponse(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        logger.error("paper_order_cancel_failed", extra={"context": {"order_id": order_id, "error": str(exc)}})
        raise HTTPException(status_code=status, detail=detail) from exc


@router.get("/positions")
async def positions() -> dict[str, Any]:
    try:
        return await _call_execution_sim(method="GET", path="/paper/positions")
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc


@router.get("/balances")
async def balances() -> dict[str, Any]:
    try:
        return await _call_execution_sim(method="GET", path="/paper/balances")
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc


@router.get("/fills", response_model=PaperFillListResponse)
async def fills(
    symbol: str | None = None,
    order_id: str | None = None,
    since: str | None = None,
    cursor: str | None = None,
    limit: int = 100,
    sort: str = "desc",
) -> PaperFillListResponse:
    params: dict[str, Any] = {"limit": limit, "sort": sort}
    if symbol:
        params["symbol"] = symbol
    if order_id:
        params["order_id"] = order_id
    if since:
        params["since"] = since
    if cursor:
        params["cursor"] = cursor
    try:
        out = await _call_execution_sim(method="GET", path="/paper/fills", params=params)
        return PaperFillListResponse(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc


@router.post("/equity/snapshot", response_model=PaperEquitySnapshotResponse)
async def snapshot_equity(payload: dict | None = None) -> PaperEquitySnapshotResponse:
    try:
        out = await _call_execution_sim(method="POST", path="/paper/equity/snapshot", json_payload=payload or {})
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="paper_equity_snapshot",
            message="Gateway forwarded paper equity snapshot",
            payload={"note": (payload or {}).get("note")},
        )
        return PaperEquitySnapshotResponse(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc


@router.get("/equity", response_model=PaperEquitySeriesResponse)
async def equity(
    since: str | None = None,
    limit: int = 200,
    sort: str = "desc",
) -> PaperEquitySeriesResponse:
    params: dict[str, Any] = {"limit": limit, "sort": sort}
    if since:
        params["since"] = since
    try:
        out = await _call_execution_sim(method="GET", path="/paper/equity", params=params)
        return PaperEquitySeriesResponse(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc


@router.get("/performance", response_model=PaperPerformanceResponse)
async def performance(
    since: str | None = None,
    limit: int = 5000,
) -> PaperPerformanceResponse:
    params: dict[str, Any] = {"limit": limit}
    if since:
        params["since"] = since
    try:
        out = await _call_execution_sim(method="GET", path="/paper/performance", params=params)
        return PaperPerformanceResponse(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc


@router.post("/performance/rollups/refresh", response_model=PaperPerformanceRollupRefreshResponse)
async def refresh_performance_rollups(payload: dict | None = None) -> PaperPerformanceRollupRefreshResponse:
    try:
        out = await _call_execution_sim(
            method="POST",
            path="/paper/performance/rollups/refresh",
            json_payload=payload or {},
        )
        return PaperPerformanceRollupRefreshResponse(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc


@router.get("/performance/rollups", response_model=PaperPerformanceRollupListResponse)
async def list_performance_rollups(
    interval: str = "daily",
    since: str | None = None,
    limit: int = 200,
    sort: str = "desc",
) -> PaperPerformanceRollupListResponse:
    params: dict[str, Any] = {"interval": interval, "limit": limit, "sort": sort}
    if since:
        params["since"] = since
    try:
        out = await _call_execution_sim(method="GET", path="/paper/performance/rollups", params=params)
        return PaperPerformanceRollupListResponse(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc


@router.get("/readiness", response_model=PaperReadinessResponse)
async def readiness() -> PaperReadinessResponse:
    try:
        out = await _call_execution_sim(method="GET", path="/paper/readiness")
        return PaperReadinessResponse(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc


@router.post("/maintenance/retention", response_model=PaperRetentionResponse)
async def retention(payload: dict | None = None) -> PaperRetentionResponse:
    try:
        out = await _call_execution_sim(
            method="POST",
            path="/paper/maintenance/retention",
            json_payload=payload or {},
        )
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="paper_retention",
            message="Gateway forwarded paper retention request",
            payload={"days": (payload or {}).get("days")},
        )
        return PaperRetentionResponse(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc


@router.post("/replay/run", response_model=PaperReplayResponse)
async def replay(req: PaperReplayRequest) -> PaperReplayResponse:
    try:
        out = await _call_execution_sim(method="POST", path="/paper/replay/run", json_payload=req.model_dump())
        return PaperReplayResponse(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc


@router.post("/shadow/compare", response_model=PaperShadowCompareResponse)
async def shadow_compare(req: PaperShadowCompareRequest) -> PaperShadowCompareResponse:
    try:
        out = await _call_execution_sim(
            method="POST",
            path="/paper/shadow/compare",
            json_payload=req.model_dump(),
        )
        return PaperShadowCompareResponse(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc


@router.get("/summary", response_model=PaperPortfolioSummaryResponse)
async def summary() -> PaperPortfolioSummaryResponse:
    try:
        out = await _call_execution_sim(method="GET", path="/paper/summary")
        return PaperPortfolioSummaryResponse(**out)
    except Exception as exc:
        status, detail = _extract_detail(exc)
        raise HTTPException(status_code=status, detail=detail) from exc
