from __future__ import annotations

from typing import Any

import httpx
from fastapi import FastAPI

from shared.audit import emit_audit_event
from shared.config import get_settings
from shared.logging import configure_logging
from shared.models import ExplainRequest
from shared.retry import retry_async

settings = get_settings()
logger = configure_logging(settings.service_name or "orchestrator", settings.log_level)

app = FastAPI(title="orchestrator", version="0.1.0")


def _asset_symbol(asset: str) -> str:
    out = str(asset or "").upper().strip()
    return out.split("/")[0] if "/" in out else out


def _confidence_score(ctx: dict[str, Any]) -> float:
    market_ok = 1.0 if (ctx.get("market") or {}).get("ok") else 0.0
    news = len(ctx.get("recent_news") or [])
    past = len(ctx.get("past_context") or [])
    future = len(ctx.get("future_context") or [])
    vec = len(ctx.get("vector_matches") or [])
    score = 0.3 * market_ok + 0.25 * min(1.0, news / 3.0) + 0.2 * min(1.0, past / 3.0) + 0.15 * min(1.0, future / 3.0) + 0.1 * min(1.0, vec / 3.0)
    return round(min(0.99, score), 3)


def _current_cause(asset: str, market: dict[str, Any], recent_news: list[dict[str, Any]]) -> str:
    if not market.get("ok"):
        return f"Insufficient live {asset} market data in the selected window."
    direction = "up" if float(market.get("change_pct") or 0.0) >= 0 else "down"
    headline = recent_news[0]["title"] if recent_news else "No strong fresh headline found"
    return (
        f"{asset} moved {direction} {abs(float(market.get('change_pct') or 0.0)):.2f}% in the lookback window. "
        f"Top linked narrative: {headline}."
    )


def _past_precedent(asset: str, past_context: list[dict[str, Any]]) -> str:
    if not past_context:
        return f"No high-confidence historical {asset} precedent was retrieved yet."
    top = past_context[0]
    return f"Most relevant past precedent: {top.get('title')} ({top.get('source')})."


def _future_catalyst(asset: str, future_context: list[dict[str, Any]]) -> str:
    if not future_context:
        return f"No explicit forward catalyst for {asset} is currently indexed."
    top = future_context[0]
    return f"Closest forward catalyst: {top.get('title')} ({top.get('source')})."


async def _retrieve(asset: str, question: str, lookback_minutes: int) -> dict[str, Any]:
    endpoint = f"{settings.memory_service_url.rstrip('/')}/v1/memory/retrieve"

    async def _call() -> dict[str, Any]:
        payload = {"asset": asset, "question": question, "lookback_minutes": lookback_minutes, "limit": 5}
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            res = await client.post(endpoint, json=payload)
            res.raise_for_status()
            return res.json()

    return await retry_async(_call, retries=2, base_delay=0.5)


async def _risk_status() -> dict[str, Any]:
    endpoint = f"{settings.risk_service_url.rstrip('/')}/v1/risk/status"

    async def _call() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            res = await client.get(endpoint)
            res.raise_for_status()
            return res.json()

    return await retry_async(_call, retries=2, base_delay=0.3)


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {"service": "orchestrator", "ok": True, "no_trading": True}


@app.post("/v1/explain")
async def explain(req: ExplainRequest) -> dict[str, Any]:
    asset = _asset_symbol(req.asset)
    ctx = await _retrieve(asset, req.question, req.lookback_minutes)
    risk = await _risk_status()

    market = ctx.get("market") if isinstance(ctx.get("market"), dict) else {}
    recent_news = list(ctx.get("recent_news") or [])
    past_context = list(ctx.get("past_context") or [])
    future_context = list(ctx.get("future_context") or [])
    vector_matches = list(ctx.get("vector_matches") or [])

    result = {
        "ok": True,
        "asset": asset,
        "question": req.question,
        "current_cause": _current_cause(asset, market, recent_news),
        "relevant_past_precedent": _past_precedent(asset, past_context),
        "future_catalyst": _future_catalyst(asset, future_context),
        "confidence_score": _confidence_score(ctx),
        "evidence": {
            "market": market,
            "recent_news": recent_news[:3],
            "past_context": past_context[:3],
            "future_context": future_context[:3],
            "vector_matches": vector_matches[:3],
        },
        "risk_posture": risk,
        "execution": {"enabled": False, "reason": "Phase 1 research copilot only"},
    }

    await emit_audit_event(
        "orchestrator",
        "explain",
        payload={
            "asset": asset,
            "question": req.question,
            "confidence_score": result["confidence_score"],
            "news_count": len(recent_news),
            "past_count": len(past_context),
            "future_count": len(future_context),
        },
    )
    logger.info(
        "explain_generated",
        extra={
            "context": {
                "asset": asset,
                "confidence_score": result["confidence_score"],
                "question": req.question,
            }
        },
    )
    return result
