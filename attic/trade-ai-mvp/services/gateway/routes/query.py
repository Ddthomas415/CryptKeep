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
from shared.schemas.documents import DocumentSearchRequest, DocumentSearchResponse
from shared.schemas.explain import ExplainRequest, ExplainResponse
from shared.schemas.trade import TradeProposalRequest, TradeProposalResponse

settings = get_settings("gateway")
logger = get_logger("gateway.query", settings.log_level)
router = APIRouter(prefix="/query", tags=["query"])


async def _call_orchestrator(payload: dict[str, Any], retries: int = 2) -> dict[str, Any]:
    if httpx is None:
        raise RuntimeError("httpx_missing")
    url = f"{settings.orchestrator_url}/explain"
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            last_err = exc
            await asyncio.sleep(0.25)
    raise RuntimeError(str(last_err) if last_err else "orchestrator_unavailable")


async def _call_orchestrator_propose(payload: dict[str, Any], retries: int = 2) -> dict[str, Any]:
    if httpx is None:
        raise RuntimeError("httpx_missing")
    url = f"{settings.orchestrator_url}/propose-trade"
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            last_err = exc
            await asyncio.sleep(0.25)
    raise RuntimeError(str(last_err) if last_err else "orchestrator_unavailable")


async def _call_memory(payload: dict[str, Any], retries: int = 2) -> dict[str, Any]:
    if httpx is None:
        raise RuntimeError("httpx_missing")
    url = f"{settings.memory_url}/search"
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            last_err = exc
            await asyncio.sleep(0.25)
    raise RuntimeError(str(last_err) if last_err else "memory_unavailable")


async def _call_market_snapshot(symbol: str, retries: int = 2) -> dict[str, Any]:
    if httpx is None:
        raise RuntimeError("httpx_missing")
    url = f"{settings.market_data_url}/market/{symbol}/snapshot"
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            last_err = exc
            await asyncio.sleep(0.25)
    raise RuntimeError(str(last_err) if last_err else "market_unavailable")


@router.post("/explain", response_model=ExplainResponse)
async def explain(req: ExplainRequest) -> ExplainResponse:
    try:
        out = await _call_orchestrator(req.model_dump())
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="query_explain",
            message="Gateway query forwarded and returned",
            payload={"asset": req.asset, "question": req.question},
        )
        return ExplainResponse(**out)
    except Exception as exc:
        logger.error("query_explain_failed", extra={"context": {"error": str(exc)}})
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="query_explain_failed",
            message="Gateway explain call failed",
            payload={"asset": req.asset, "question": req.question, "error": str(exc)},
            level="ERROR",
        )
        raise HTTPException(status_code=503, detail="orchestrator unavailable") from exc


@router.post("/why-moving", response_model=ExplainResponse)
async def why_moving(payload: dict[str, str]) -> ExplainResponse:
    asset = str(payload.get("asset") or "SOL")
    req = ExplainRequest(asset=asset, question=f"Why is {asset.upper()} moving?")
    return await explain(req)


@router.post("/propose-trade", response_model=TradeProposalResponse)
async def propose_trade(req: TradeProposalRequest) -> TradeProposalResponse:
    try:
        out = await _call_orchestrator_propose(req.model_dump())
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="query_propose_trade",
            message="Gateway trade proposal forwarded and returned",
            payload={"asset": req.asset, "question": req.question, "max_notional_usd": req.max_notional_usd},
        )
        return TradeProposalResponse(**out)
    except Exception as exc:
        logger.error("query_propose_trade_failed", extra={"context": {"error": str(exc)}})
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="query_propose_trade_failed",
            message="Gateway trade proposal call failed",
            payload={"asset": req.asset, "error": str(exc)},
            level="ERROR",
        )
        raise HTTPException(status_code=503, detail="orchestrator unavailable") from exc


@router.post("/documents/search", response_model=DocumentSearchResponse)
async def documents_search(req: DocumentSearchRequest) -> DocumentSearchResponse:
    try:
        out = await _call_memory(req.model_dump())
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="documents_search",
            message="Gateway documents search completed",
            payload={"asset": req.asset, "query": req.query, "limit": req.limit},
        )
        return DocumentSearchResponse(**out)
    except Exception as exc:
        logger.error("documents_search_failed", extra={"context": {"error": str(exc)}})
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="documents_search_failed",
            message="Gateway documents search failed",
            payload={"asset": req.asset, "query": req.query, "error": str(exc)},
            level="ERROR",
        )
        raise HTTPException(status_code=503, detail="memory unavailable") from exc


@router.get("/market/{symbol}/snapshot")
async def market_snapshot(symbol: str) -> dict[str, Any]:
    try:
        out = await _call_market_snapshot(symbol)
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="market_snapshot_proxy",
            message="Gateway market snapshot proxied",
            payload={"symbol": symbol},
        )
        return out
    except Exception as exc:
        logger.error("market_snapshot_proxy_failed", extra={"context": {"symbol": symbol, "error": str(exc)}})
        await emit_audit_event(
            settings=settings,
            service_name="gateway",
            event_type="market_snapshot_proxy_failed",
            message="Gateway market snapshot proxy failed",
            payload={"symbol": symbol, "error": str(exc)},
            level="ERROR",
        )
        raise HTTPException(status_code=503, detail="market_data unavailable") from exc
