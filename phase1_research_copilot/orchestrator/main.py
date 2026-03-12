from __future__ import annotations

import json
from typing import Any

from fastapi import FastAPI

from shared.audit import emit_audit_event
from shared.config import get_settings
from shared.llm_client import OpenAIResponsesClient
from shared.logging import configure_logging
from shared.models import ExplainRequest
from shared.prompting import build_research_explain_instructions
from shared.tools import (
    OPENAI_TOOL_DEFINITIONS,
    execute_tool_call,
    get_market_snapshot,
    get_operations_summary,
    get_risk_summary,
    get_signal_summary,
)

settings = get_settings()
logger = configure_logging(settings.service_name or "orchestrator", settings.log_level)
llm_client = OpenAIResponsesClient(settings)

app = FastAPI(title="orchestrator", version="0.2.0")

EXPLAIN_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "name": "research_explain_response",
    "schema": {
        "type": "object",
        "properties": {
            "current_cause": {"type": "string"},
            "past_precedent": {"type": "string"},
            "future_catalyst": {"type": "string"},
            "confidence": {"type": "number"},
        },
        "required": [
            "current_cause",
            "past_precedent",
            "future_catalyst",
            "confidence",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


def _asset_symbol(asset: str) -> str:
    out = str(asset or "").upper().strip()
    return out.split("/")[0] if "/" in out else out


def _item_value(item: Any, key: str) -> Any:
    if isinstance(item, dict):
        return item.get(key)
    return getattr(item, key, None)


def _extract_function_calls(response: Any) -> list[dict[str, str]]:
    calls: list[dict[str, str]] = []
    for item in getattr(response, "output", []) or []:
        if _item_value(item, "type") != "function_call":
            continue
        calls.append(
            {
                "name": str(_item_value(item, "name") or ""),
                "arguments": str(_item_value(item, "arguments") or "{}"),
                "call_id": str(_item_value(item, "call_id") or ""),
            }
        )
    return calls


def _extract_json_object(text: str) -> dict[str, Any]:
    raw = str(text or "").strip()
    if not raw:
        return {}

    candidates = [raw]
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(raw[start : end + 1])

    for candidate in candidates:
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    return {}


def _clip_confidence(value: Any, *, fallback: float = 0.55) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = fallback
    return round(min(0.99, max(0.0, numeric)), 3)


def _build_evidence(tool_results: dict[str, Any]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    market = tool_results.get("get_market_snapshot") if isinstance(tool_results.get("get_market_snapshot"), dict) else {}
    if market:
        evidence.append(
            {
                "id": "market_snapshot",
                "type": "market",
                "source": str(market.get("exchange") or market.get("source") or "market-data"),
                "timestamp": market.get("as_of"),
                "summary": f"Last price {float(market.get('price') or 0.0):,.2f} with bid {float(market.get('bid') or 0.0):,.2f} and ask {float(market.get('ask') or 0.0):,.2f}.",
                "relevance": 0.95,
            }
        )

    signal = tool_results.get("get_signal_summary") if isinstance(tool_results.get("get_signal_summary"), dict) else {}
    for idx, item in enumerate((signal.get("recent_news") if isinstance(signal.get("recent_news"), list) else [])[:2], start=1):
        if not isinstance(item, dict):
            continue
        evidence.append(
            {
                "id": f"news_{idx}",
                "type": "news",
                "source": str(item.get("source") or "memory-retrieval"),
                "timestamp": item.get("published_at") or item.get("fetched_at"),
                "summary": str(item.get("title") or "Recent news context."),
                "relevance": 0.84,
            }
        )
    for idx, item in enumerate((signal.get("past_context") if isinstance(signal.get("past_context"), list) else [])[:1], start=1):
        if not isinstance(item, dict):
            continue
        evidence.append(
            {
                "id": f"past_{idx}",
                "type": "past",
                "source": str(item.get("source") or "memory-retrieval"),
                "timestamp": item.get("published_at") or item.get("fetched_at"),
                "summary": str(item.get("title") or "Historical context match."),
                "relevance": 0.72,
            }
        )
    for idx, item in enumerate((signal.get("future_context") if isinstance(signal.get("future_context"), list) else [])[:1], start=1):
        if not isinstance(item, dict):
            continue
        evidence.append(
            {
                "id": f"future_{idx}",
                "type": "future",
                "source": str(item.get("source") or "memory-retrieval"),
                "timestamp": item.get("published_at") or item.get("fetched_at"),
                "summary": str(item.get("title") or "Forward catalyst context."),
                "relevance": 0.68,
            }
        )
    return evidence[:6]


def _build_evidence_bundle(tool_results: dict[str, Any]) -> dict[str, Any]:
    signal = tool_results.get("get_signal_summary") if isinstance(tool_results.get("get_signal_summary"), dict) else {}
    return {
        "market": signal.get("market") if isinstance(signal.get("market"), dict) else tool_results.get("get_market_snapshot", {}),
        "market_snapshot": tool_results.get("get_market_snapshot", {}),
        "risk": tool_results.get("get_risk_summary", {}),
        "recent_news": (signal.get("recent_news") if isinstance(signal.get("recent_news"), list) else [])[:3],
        "past_context": (signal.get("past_context") if isinstance(signal.get("past_context"), list) else [])[:3],
        "future_context": (signal.get("future_context") if isinstance(signal.get("future_context"), list) else [])[:3],
        "vector_matches": (signal.get("vector_matches") if isinstance(signal.get("vector_matches"), list) else [])[:3],
        "operations": tool_results.get("get_operations_summary", {}),
    }


def _fallback_reasoning(asset: str, question: str, tool_results: dict[str, Any]) -> dict[str, Any]:
    market = tool_results.get("get_market_snapshot") if isinstance(tool_results.get("get_market_snapshot"), dict) else {}
    signal = tool_results.get("get_signal_summary") if isinstance(tool_results.get("get_signal_summary"), dict) else {}
    recent_news = signal.get("recent_news") if isinstance(signal.get("recent_news"), list) else []
    past_context = signal.get("past_context") if isinstance(signal.get("past_context"), list) else []
    future_context = signal.get("future_context") if isinstance(signal.get("future_context"), list) else []
    market_summary = signal.get("market") if isinstance(signal.get("market"), dict) else {}

    latest_price = float(market.get("price") or market_summary.get("latest_price") or 0.0)
    change_pct = float(market_summary.get("change_pct") or 0.0)
    direction = "up" if change_pct >= 0 else "down"
    top_headline = str((recent_news[0] or {}).get("title") or "No strong fresh headline was retrieved.") if recent_news else "No strong fresh headline was retrieved."
    past_title = str((past_context[0] or {}).get("title") or f"No indexed historical precedent for {asset} was found yet.") if past_context else f"No indexed historical precedent for {asset} was found yet."
    future_title = str((future_context[0] or {}).get("title") or f"No explicit forward catalyst for {asset} is currently indexed.") if future_context else f"No explicit forward catalyst for {asset} is currently indexed."

    confidence = 0.35
    if latest_price > 0:
        confidence += 0.2
    if recent_news:
        confidence += 0.2
    if past_context:
        confidence += 0.1
    if future_context:
        confidence += 0.1

    return {
        "current_cause": (
            f"{asset} is trading {direction} over the current lookback window with the last observed price near {latest_price:,.2f}. "
            f"Top linked narrative: {top_headline}"
        ).strip(),
        "past_precedent": past_title,
        "future_catalyst": future_title,
        "confidence": _clip_confidence(confidence, fallback=0.55),
    }


async def _ensure_core_tool_results(asset: str, tool_results: dict[str, Any]) -> dict[str, Any]:
    results = dict(tool_results)
    if "get_market_snapshot" not in results:
        results["get_market_snapshot"] = await get_market_snapshot(asset)
    if "get_signal_summary" not in results:
        results["get_signal_summary"] = await get_signal_summary(asset)
    if "get_risk_summary" not in results:
        results["get_risk_summary"] = await get_risk_summary()
    if "get_operations_summary" not in results:
        results["get_operations_summary"] = await get_operations_summary()
    return results


async def _run_openai_reasoning(req: ExplainRequest, asset: str) -> tuple[dict[str, Any], dict[str, Any]]:
    instructions = build_research_explain_instructions(
        asset=asset,
        question=req.question,
        lookback_minutes=req.lookback_minutes,
    )
    response = await llm_client.create_response(
        model=settings.openai_reasoning_model,
        instructions=instructions,
        input=(
            f"Asset: {asset}\n"
            f"Question: {req.question}\n"
            f"Lookback minutes: {req.lookback_minutes}\n"
            "Explain the move using tool-grounded research only."
        ),
        tools=OPENAI_TOOL_DEFINITIONS,
        metadata={"mode": "research_explain", "asset": asset},
        reasoning_effort="medium",
        text_format=EXPLAIN_RESPONSE_FORMAT,
    )

    tool_results: dict[str, Any] = {}
    for _ in range(4):
        calls = _extract_function_calls(response)
        if not calls:
            break

        tool_outputs: list[dict[str, str]] = []
        for call in calls:
            result = await execute_tool_call(call["name"], call["arguments"])
            tool_results[call["name"]] = result
            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call["call_id"],
                    "output": json.dumps(result, ensure_ascii=True),
                }
            )
            logger.info(
                "openai_tool_called",
                extra={"context": {"asset": asset, "tool": call["name"]}},
            )

        response = await llm_client.create_response(
            model=settings.openai_reasoning_model,
            instructions=instructions,
            previous_response_id=str(getattr(response, "id", "")),
            input=tool_outputs,
            tools=OPENAI_TOOL_DEFINITIONS,
            metadata={"mode": "research_explain", "asset": asset},
            reasoning_effort="medium",
            text_format=EXPLAIN_RESPONSE_FORMAT,
        )

    tool_results = await _ensure_core_tool_results(asset, tool_results)
    reasoning = _extract_json_object(OpenAIResponsesClient.output_text(response))
    if not reasoning:
        raise RuntimeError("llm_output_parse_failed")
    return reasoning, tool_results


def _assemble_explain_response(
    req: ExplainRequest,
    reasoning: dict[str, Any],
    tool_results: dict[str, Any],
    *,
    llm_status: dict[str, Any],
) -> dict[str, Any]:
    asset = _asset_symbol(req.asset)
    risk = tool_results.get("get_risk_summary") if isinstance(tool_results.get("get_risk_summary"), dict) else {}
    evidence = _build_evidence(tool_results)
    current_cause = str(reasoning.get("current_cause") or "Insufficient explain context was generated.")
    past_precedent = str(reasoning.get("past_precedent") or f"No clear historical precedent for {asset} was retrieved.")
    future_catalyst = str(reasoning.get("future_catalyst") or f"No clear forward catalyst for {asset} was retrieved.")
    confidence = _clip_confidence(reasoning.get("confidence"), fallback=0.55)
    risk_note = "Research only. Execution disabled."

    return {
        "ok": True,
        "asset": asset,
        "question": req.question,
        "current_cause": current_cause,
        "past_precedent": past_precedent,
        "relevant_past_precedent": past_precedent,
        "future_catalyst": future_catalyst,
        "confidence": confidence,
        "confidence_score": confidence,
        "risk_note": risk_note,
        "execution_disabled": True,
        "evidence": evidence,
        "evidence_bundle": _build_evidence_bundle(tool_results),
        "risk_posture": risk,
        "execution": {"enabled": False, "reason": "Phase 1 research copilot only"},
        "assistant_status": llm_status,
    }


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {"service": "orchestrator", "ok": True, "no_trading": True, "openai_enabled": llm_client.enabled}


@app.post("/v1/explain")
async def explain(req: ExplainRequest) -> dict[str, Any]:
    asset = _asset_symbol(req.asset)
    llm_status: dict[str, Any] = {
        "provider": "openai" if llm_client.enabled else "fallback",
        "model": settings.openai_reasoning_model if llm_client.enabled else None,
        "fallback": not llm_client.enabled,
    }

    try:
        if not llm_client.enabled:
            raise RuntimeError("openai_api_key_missing")
        reasoning, tool_results = await _run_openai_reasoning(req, asset)
    except Exception as exc:
        tool_results = await _ensure_core_tool_results(asset, {})
        reasoning = _fallback_reasoning(asset, req.question, tool_results)
        llm_status = {
            "provider": "fallback",
            "model": None,
            "fallback": True,
            "message": f"OpenAI reasoning unavailable; deterministic fallback used ({type(exc).__name__}).",
        }
        logger.warning(
            "openai_reasoning_fallback",
            extra={"context": {"asset": asset, "error": str(exc)}},
        )

    result = _assemble_explain_response(req, reasoning, tool_results, llm_status=llm_status)
    await emit_audit_event(
        "orchestrator",
        "explain",
        payload={
            "asset": asset,
            "question": req.question,
            "confidence_score": result["confidence_score"],
            "tool_calls": sorted(tool_results.keys()),
            "llm_provider": llm_status.get("provider"),
            "llm_model": llm_status.get("model"),
            "fallback": bool(llm_status.get("fallback")),
        },
    )
    logger.info(
        "explain_generated",
        extra={
            "context": {
                "asset": asset,
                "confidence_score": result["confidence_score"],
                "question": req.question,
                "tool_calls": sorted(tool_results.keys()),
                "llm_provider": llm_status.get("provider"),
            }
        },
    )
    return result
