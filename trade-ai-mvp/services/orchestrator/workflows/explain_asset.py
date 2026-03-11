from __future__ import annotations

import asyncio
import uuid
from typing import Any

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None

from shared.clients.llm_client import polish_explanation
from shared.config import Settings
from shared.logging import get_logger


def _asset_symbol(asset: str) -> str:
    return str(asset or "").upper().replace("-USD", "").replace("/USD", "")


def build_explanation(
    *,
    asset: str,
    question: str,
    market_snapshot: dict[str, Any],
    news_items: list[dict[str, Any]],
    archive_items: list[dict[str, Any]],
    future_docs: list[dict[str, Any]],
) -> dict[str, Any]:
    symbol = _asset_symbol(asset)

    if market_snapshot:
        try:
            bid = float(market_snapshot.get("bid") or 0)
            ask = float(market_snapshot.get("ask") or 0)
            spread = ask - bid
            cause = (
                f"Recent {symbol} price activity shows last price {market_snapshot.get('last_price')} "
                f"with spread {spread:.4f}, alongside fresh document hits."
            )
        except Exception:
            cause = f"Recent {symbol} price activity and fresh document hits suggest current movement drivers."
    else:
        cause = f"Current {symbol} price driver is uncertain due to limited snapshot data."

    past_precedent = (
        archive_items[0].get("title") if archive_items else f"No strong historical precedent for {symbol} found."
    )
    future_catalyst = (
        future_docs[0].get("title") if future_docs else f"No future catalyst found for {symbol}; monitor roadmap/governance updates."
    )

    evidence: list[dict[str, Any]] = []
    if market_snapshot:
        evidence.append(
            {
                "type": "market",
                "source": market_snapshot.get("exchange", "coinbase"),
                "timestamp": market_snapshot.get("timestamp"),
            }
        )

    for item in news_items[:2]:
        evidence.append(
            {
                "type": "document",
                "source": item.get("source", "newsapi"),
                "title": item.get("title"),
                "timestamp": item.get("published_at"),
            }
        )

    if archive_items:
        evidence.append(
            {
                "type": "archive",
                "source": archive_items[0].get("source", "wayback"),
                "title": archive_items[0].get("title"),
                "timestamp": archive_items[0].get("timestamp"),
            }
        )

    confidence = min(0.95, 0.55 + (0.08 * len(news_items)) + (0.07 * len(archive_items)) + (0.05 * len(future_docs)))

    return {
        "asset": symbol,
        "question": question,
        "current_cause": cause,
        "past_precedent": past_precedent,
        "future_catalyst": future_catalyst,
        "confidence": round(confidence, 2),
        "evidence": evidence,
        "execution_disabled": True,
    }


async def _request_with_retry(
    *,
    client: httpx.AsyncClient,
    method: str,
    url: str,
    json_payload: dict[str, Any] | None = None,
    retries: int = 2,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for _ in range(retries + 1):
        try:
            if method == "GET":
                res = await client.get(url)
            else:
                res = await client.post(url, json=json_payload)
            res.raise_for_status()
            return res.json()
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.25)
    raise RuntimeError(f"request_failed:{url}:{last_error}")


async def _emit_audit(
    *,
    client: httpx.AsyncClient,
    settings: Settings,
    request_id: str,
    event_type: str,
    message: str,
    payload: dict[str, Any] | None = None,
    level: str = "INFO",
) -> None:
    body = {
        "service_name": "orchestrator",
        "event_type": event_type,
        "request_id": request_id,
        "level": level,
        "message": message,
        "payload": payload or {},
    }
    try:
        await _request_with_retry(
            client=client,
            method="POST",
            url=f"{settings.audit_log_url}/audit/log",
            json_payload=body,
            retries=1,
        )
    except Exception:
        pass


async def _safe_request_json(
    *,
    client: httpx.AsyncClient,
    settings: Settings,
    logger,
    request_id: str,
    dependency: str,
    method: str,
    url: str,
    success_event_type: str,
    success_message: str,
    failure_event_type: str,
    failure_message: str,
    json_payload: dict[str, Any] | None = None,
    fallback: dict[str, Any] | None = None,
    retries: int = 2,
) -> dict[str, Any]:
    try:
        data = await _request_with_retry(
            client=client,
            method=method,
            url=url,
            json_payload=json_payload,
            retries=retries,
        )
        await _emit_audit(
            client=client,
            settings=settings,
            request_id=request_id,
            event_type=success_event_type,
            message=success_message,
            payload={"dependency": dependency},
        )
        return data
    except Exception as exc:
        logger.warning(
            "dependency_call_failed",
            extra={
                "context": {
                    "request_id": request_id,
                    "dependency": dependency,
                    "url": url,
                    "error": str(exc),
                }
            },
        )
        await _emit_audit(
            client=client,
            settings=settings,
            request_id=request_id,
            event_type=failure_event_type,
            message=failure_message,
            payload={"dependency": dependency, "error": str(exc)},
            level="ERROR",
        )
        return fallback or {}


async def explain_asset_flow(
    *,
    settings: Settings,
    logger,
    question: str,
    asset: str,
) -> tuple[str, dict[str, Any]]:
    request_id = str(uuid.uuid4())
    symbol = _asset_symbol(asset)
    if httpx is None:
        response = build_explanation(
            asset=symbol,
            question=question,
            market_snapshot={},
            news_items=[],
            archive_items=[],
            future_docs=[],
        )
        logger.warning(
            "httpx_missing_fallback_response",
            extra={"context": {"request_id": request_id, "asset": symbol}},
        )
        return request_id, response

    async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
        await _emit_audit(
            client=client,
            settings=settings,
            request_id=request_id,
            event_type="request_received",
            message="Explain request received",
            payload={"asset": symbol, "question": question},
        )

        market = await _safe_request_json(
            client=client,
            settings=settings,
            logger=logger,
            request_id=request_id,
            dependency="market_data",
            method="GET",
            url=f"{settings.market_data_url}/market/{symbol}-USD/snapshot",
            success_event_type="market_fetched",
            success_message="Fetched market snapshot",
            failure_event_type="market_fetch_failed",
            failure_message="Market snapshot fetch failed; using fallback",
            fallback={},
        )

        await _safe_request_json(
            client=client,
            settings=settings,
            logger=logger,
            request_id=request_id,
            dependency="news_ingestion",
            method="POST",
            url=f"{settings.news_ingestion_url}/ingest/news",
            json_payload={"asset": symbol},
            success_event_type="news_ingested",
            success_message="News ingestion triggered",
            failure_event_type="news_ingest_failed",
            failure_message="News ingestion trigger failed; continuing with existing documents",
            fallback={"inserted": 0, "asset": symbol},
        )
        news = await _safe_request_json(
            client=client,
            settings=settings,
            logger=logger,
            request_id=request_id,
            dependency="news_ingestion",
            method="GET",
            url=f"{settings.news_ingestion_url}/news/{symbol}",
            success_event_type="news_fetched",
            success_message="Fetched recent news",
            failure_event_type="news_fetch_failed",
            failure_message="News fetch failed; using empty news set",
            fallback={"asset": symbol, "items": []},
        )

        archive = await _safe_request_json(
            client=client,
            settings=settings,
            logger=logger,
            request_id=request_id,
            dependency="archive_lookup",
            method="GET",
            url=f"{settings.archive_lookup_url}/archive/{symbol}",
            success_event_type="archive_fetched",
            success_message="Fetched archive context",
            failure_event_type="archive_fetch_failed",
            failure_message="Archive lookup failed; using empty history",
            fallback={"asset": symbol, "items": []},
        )

        future = await _safe_request_json(
            client=client,
            settings=settings,
            logger=logger,
            request_id=request_id,
            dependency="memory",
            method="POST",
            url=f"{settings.memory_url}/search",
            json_payload={"query": question, "asset": symbol, "timeline": ["future"], "limit": 3},
            success_event_type="future_context_fetched",
            success_message="Fetched future context",
            failure_event_type="future_context_failed",
            failure_message="Future context fetch failed; using empty future set",
            fallback={"results": []},
        )

        risk = await _safe_request_json(
            client=client,
            settings=settings,
            logger=logger,
            request_id=request_id,
            dependency="risk_stub",
            method="POST",
            url=f"{settings.risk_stub_url}/risk/evaluate",
            json_payload={"asset": symbol},
            success_event_type="risk_evaluated",
            success_message="Risk evaluated",
            failure_event_type="risk_evaluation_failed",
            failure_message="Risk evaluation failed; defaulting to execution disabled",
            fallback={"execution_disabled": True, "approved": False, "reason": "risk_unavailable"},
        )
        paper_positions = await _safe_request_json(
            client=client,
            settings=settings,
            logger=logger,
            request_id=request_id,
            dependency="execution_sim",
            method="GET",
            url=f"{settings.execution_sim_url}/paper/positions",
            success_event_type="paper_positions_fetched",
            success_message="Fetched active paper positions",
            failure_event_type="paper_positions_failed",
            failure_message="Paper positions unavailable; using empty set",
            fallback={"positions": []},
        )
        paper_fills = await _safe_request_json(
            client=client,
            settings=settings,
            logger=logger,
            request_id=request_id,
            dependency="execution_sim",
            method="GET",
            url=f"{settings.execution_sim_url}/paper/fills?limit=5&sort=desc",
            success_event_type="paper_fills_fetched",
            success_message="Fetched recent paper fills",
            failure_event_type="paper_fills_failed",
            failure_message="Paper fills unavailable; using empty set",
            fallback={"fills": []},
        )

        response = build_explanation(
            asset=symbol,
            question=question,
            market_snapshot=market,
            news_items=list(news.get("items") or []),
            archive_items=list(archive.get("items") or []),
            future_docs=list(future.get("results") or []),
        )
        response["execution_disabled"] = bool(risk.get("execution_disabled", True))
        response["paper_positions"] = list(paper_positions.get("positions") or [])
        response["recent_paper_fills"] = list(paper_fills.get("fills") or [])
        response["paper_risk_state"] = dict(risk or {})

        polished = await polish_explanation(
            openai_api_key=settings.openai_api_key,
            model=settings.openai_model,
            draft=response,
            timeout=settings.http_timeout_seconds,
        )
        if polished:
            response["current_cause"] = polished.get("current_cause", response["current_cause"])
            response["past_precedent"] = polished.get("past_precedent", response["past_precedent"])
            response["future_catalyst"] = polished.get("future_catalyst", response["future_catalyst"])

        await _emit_audit(
            client=client,
            settings=settings,
            request_id=request_id,
            event_type="response_returned",
            message="Explain response generated",
            payload={"asset": symbol, "confidence": response.get("confidence")},
        )

    logger.info(
        "explain_flow_completed",
        extra={"context": {"request_id": request_id, "asset": symbol, "confidence": response.get("confidence")}},
    )
    return request_id, response
