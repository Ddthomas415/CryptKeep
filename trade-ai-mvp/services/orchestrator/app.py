from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

try:
    import httpx
except Exception:  # pragma: no cover
    httpx = None

from fastapi import FastAPI

from services.orchestrator.workflows.explain_asset import explain_asset_flow
from shared.config import get_settings
from shared.db import SessionLocal, check_db_connection
from shared.logging import get_logger
from shared.models.events import Explanation
from shared.schemas.explain import ExplainRequest, ExplainResponse
from shared.schemas.trade import TradeProposalRequest, TradeProposalResponse

settings = get_settings("orchestrator")
logger = get_logger("orchestrator", settings.log_level)
app = FastAPI(title="orchestrator")


def _as_decimal(value: Any, default: str = "0") -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


async def _request_json_with_retry(
    *,
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    retries: int = 2,
) -> dict[str, Any]:
    if httpx is None:
        return {}
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
                if method == "GET":
                    resp = await client.get(url)
                else:
                    resp = await client.post(url, json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:
            last_err = exc
            await asyncio.sleep(0.25)
    logger.warning("dependency_unavailable", extra={"context": {"url": url, "error": str(last_err)}})
    return {}


@app.on_event("startup")
def startup() -> None:
    ok = check_db_connection()
    logger.info("startup_db_check", extra={"context": {"ok": ok}})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/explain", response_model=ExplainResponse)
async def explain(req: ExplainRequest) -> ExplainResponse:
    request_id, payload = await explain_asset_flow(
        settings=settings,
        logger=logger,
        question=req.question,
        asset=req.asset,
    )

    try:
        with SessionLocal() as db:
            row = Explanation(
                asset_symbol=payload["asset"],
                question=payload["question"],
                current_cause=payload["current_cause"],
                past_precedent=payload["past_precedent"],
                future_catalyst=payload["future_catalyst"],
                confidence=Decimal(str(payload["confidence"])),
                evidence=payload.get("evidence") or [],
                model_name=settings.openai_model if settings.openai_api_key else "deterministic_stub",
            )
            db.add(row)
            db.commit()
    except Exception as exc:
        logger.warning(
            "explanation_persist_failed",
            extra={"context": {"request_id": request_id, "error": str(exc)}},
        )

    return ExplainResponse(**payload)


@app.post("/propose-trade", response_model=TradeProposalResponse)
async def propose_trade(req: TradeProposalRequest) -> TradeProposalResponse:
    symbol = str(req.asset or "").upper().replace("-USD", "").replace("/USD", "")
    question = req.question or f"Should we open a {symbol} paper position now?"
    _request_id, explain_payload = await explain_asset_flow(
        settings=settings,
        logger=logger,
        question=question,
        asset=symbol,
    )

    market = await _request_json_with_retry(
        method="GET",
        url=f"{settings.market_data_url}/market/{symbol}-USD/snapshot",
        retries=1,
    )
    price = _as_decimal(market.get("last_price"), "0")
    confidence = float(explain_payload.get("confidence") or 0.0)
    side = "buy" if confidence >= 0.7 and price > 0 else "hold"
    max_notional = _as_decimal(req.max_notional_usd, "250")
    target_notional = min(max_notional, Decimal("250"))
    qty = Decimal("0")
    if side != "hold" and price > 0:
        qty = target_notional / price
    notional = qty * price

    requested_action = "open_position" if side != "hold" else "observe_only"
    risk = await _request_json_with_retry(
        method="POST",
        url=f"{settings.risk_stub_url}/risk/evaluate",
        payload={
            "asset": symbol,
            "mode": "paper",
            "requested_action": requested_action,
            "proposed_notional_usd": float(notional),
            "position_qty": 0.0,
            "daily_pnl": 0.0,
        },
        retries=1,
    )
    if side != "hold" and not bool(risk.get("paper_approved", False)):
        side = "hold"
        qty = Decimal("0")
        notional = Decimal("0")

    rationale = (
        str(explain_payload.get("current_cause") or "No clear setup identified.")
        + " "
        + str(explain_payload.get("future_catalyst") or "")
    ).strip()

    return TradeProposalResponse(
        asset=symbol,
        question=question,
        side=side,
        suggested_quantity=float(qty),
        estimated_price=float(price) if price > 0 else None,
        estimated_notional_usd=float(notional),
        rationale=rationale,
        confidence=confidence,
        risk=risk or {},
        execution_disabled=True,
        requires_user_approval=True,
    )
