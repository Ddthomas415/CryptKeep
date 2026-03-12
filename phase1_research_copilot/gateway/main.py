from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import FastAPI, Response
from pydantic import BaseModel

from shared.audit import emit_audit_event
from shared.config import get_settings
from shared.llm_client import OpenAIResponsesClient
from shared.logging import configure_logging
from shared.prompting import CHAT_COPILOT_INSTRUCTIONS
from shared.retry import retry_async

settings = get_settings()
logger = configure_logging(settings.service_name or "gateway", settings.log_level)
llm_client = OpenAIResponsesClient(settings)

app = FastAPI(title="gateway", version="0.2.0")


class ChatRequest(BaseModel):
    asset: str
    question: str
    lookback_minutes: int = 60


def _format_reasoning_provider(value: Any) -> str:
    provider = str(value or "").strip().lower()
    if not provider:
        return "Unknown"
    if provider == "openai":
        return "OpenAI"
    if provider == "backend_api":
        return "Backend API"
    if provider == "phase1_copilot":
        return "Phase 1 Copilot"
    if provider == "gateway_fallback":
        return "Gateway Fallback"
    if provider == "fallback":
        return "Fallback"
    return provider.replace("_", " ").title()


def _format_status_summary(label: str, status: dict[str, Any] | None) -> str:
    payload = status if isinstance(status, dict) else {}
    provider = _format_reasoning_provider(payload.get("provider"))
    model = str(payload.get("model") or "").strip()
    parts = [provider]
    if model:
        parts.append(model)
    if bool(payload.get("fallback")):
        parts.append("fallback")
    if bool(payload.get("upstream_fallback")):
        upstream_reason = str(payload.get("upstream_reason") or "").strip()
        parts.append(f"upstream {upstream_reason}" if upstream_reason else "upstream fallback")
    return f"{label}: {' | '.join(parts)}"


def _build_reasoning_summary(
    explain_status: dict[str, Any] | None,
    chat_status: dict[str, Any] | None,
) -> str:
    return "\n".join(
        [
            _format_status_summary("Explain", explain_status),
            _format_status_summary("Chat", chat_status),
        ]
    )


def _fallback_explain_response(req: ChatRequest, *, reason: str) -> dict[str, Any]:
    asset = str(req.asset or "").upper().strip() or "ASSET"
    current_cause = (
        f"Live explain reasoning is temporarily unavailable for {asset}. "
        "The gateway is returning a research-only fallback summary."
    )
    past_precedent = (
        f"No trusted historical precedent for {asset} is available because the explain service could not be reached."
    )
    future_catalyst = (
        f"No fresh forward catalyst for {asset} can be confirmed until the explain service is reachable again."
    )
    return {
        "ok": True,
        "asset": asset,
        "question": req.question,
        "current_cause": current_cause,
        "past_precedent": past_precedent,
        "relevant_past_precedent": past_precedent,
        "future_catalyst": future_catalyst,
        "confidence": 0.25,
        "confidence_score": 0.25,
        "risk_note": "Research only. Execution disabled.",
        "execution_disabled": True,
        "evidence": [],
        "evidence_bundle": {"market_snapshot": {}, "recent_news": [], "past_context": [], "future_context": []},
        "risk_posture": {
            "execution_mode": "DISABLED",
            "gate": "NO_TRADING",
            "allow_trading": False,
            "reason": "Gateway fallback mode",
        },
        "execution": {"enabled": False, "reason": "Phase 1 research copilot only"},
        "assistant_status": {
            "provider": "gateway_fallback",
            "model": None,
            "fallback": True,
            "message": f"Explain service unavailable; gateway fallback used ({reason}).",
        },
    }


def _fallback_chat_response(payload: dict[str, Any]) -> str:
    asset = str(payload.get("asset") or "asset")
    current = str(payload.get("current_cause") or "No current cause available.")
    future = str(payload.get("future_catalyst") or "No catalyst available.")
    risk_note = str(payload.get("risk_note") or "Research only. Execution disabled.")
    return f"{asset}: {current}\n\nNext catalyst: {future}\n\nRisk note: {risk_note}"


async def _generate_chat_response(explain_payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if not llm_client.enabled:
        return _fallback_chat_response(explain_payload), {
            "provider": "fallback",
            "model": None,
            "fallback": True,
            "message": "OpenAI chat phrasing unavailable; deterministic formatter used.",
        }

    try:
        response = await llm_client.create_response(
            model=settings.openai_model,
            instructions=CHAT_COPILOT_INSTRUCTIONS,
            input=json.dumps(
                {
                    "asset": explain_payload.get("asset"),
                    "question": explain_payload.get("question"),
                    "current_cause": explain_payload.get("current_cause"),
                    "past_precedent": explain_payload.get("past_precedent")
                    or explain_payload.get("relevant_past_precedent"),
                    "future_catalyst": explain_payload.get("future_catalyst"),
                    "confidence": explain_payload.get("confidence")
                    or explain_payload.get("confidence_score"),
                    "risk_note": explain_payload.get("risk_note"),
                    "execution_disabled": explain_payload.get("execution_disabled", True),
                },
                ensure_ascii=True,
            ),
            metadata={
                "mode": "chat_copilot",
                "asset": str(explain_payload.get("asset") or ""),
            },
        )
        text = OpenAIResponsesClient.output_text(response).strip()
        if text:
            return text, {
                "provider": "openai",
                "model": settings.openai_model,
                "fallback": False,
            }
        raise RuntimeError("empty_chat_output")
    except Exception as exc:
        logger.warning(
            "chat_generation_fallback",
            extra={"context": {"asset": explain_payload.get("asset"), "error": str(exc)}},
        )
        return _fallback_chat_response(explain_payload), {
            "provider": "fallback",
            "model": None,
            "fallback": True,
            "message": f"OpenAI chat phrasing unavailable; deterministic formatter used ({type(exc).__name__}).",
        }


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {"service": "gateway", "ok": True, "ui": True, "openai_enabled": llm_client.enabled}


@app.get("/", response_class=Response)
async def chat_ui() -> Response:
    html = """
<!doctype html>
<html>
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Crypto Research Copilot (Phase 1)</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, sans-serif; margin: 0; background: #0b1020; color: #e9ecf1; }
    .wrap { max-width: 900px; margin: 24px auto; padding: 0 16px; }
    .card { background: #121933; border: 1px solid #202a4d; border-radius: 10px; padding: 16px; }
    input, textarea, button { width: 100%; box-sizing: border-box; border-radius: 8px; border: 1px solid #33416f; padding: 10px; background: #0f1730; color: #e9ecf1; }
    button { margin-top: 10px; background: #2a4fde; border: 0; cursor: pointer; }
    pre { white-space: pre-wrap; background: #0e152a; padding: 12px; border-radius: 8px; }
    .row { display: grid; grid-template-columns: 180px 1fr; gap: 10px; margin-bottom: 10px; }
    .note { color: #9fb2ff; font-size: 13px; margin-top: 8px; }
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>Crypto Research Copilot (Phase 1)</h1>
    <div class=\"card\">
      <div class=\"row\"><label>Asset</label><input id=\"asset\" value=\"SOL\"/></div>
      <div class=\"row\"><label>Question</label><textarea id=\"question\" rows=\"3\">Why is SOL moving?</textarea></div>
      <div class=\"row\"><label>Lookback (min)</label><input id=\"lookback\" value=\"60\"/></div>
      <button onclick=\"ask()\">Ask</button>
      <div class=\"note\">Execution is disabled. This is research-only.</div>
      <pre id=\"out\">Waiting for query...</pre>
    </div>
  </div>
<script>
async function ask() {
  const body = {
    asset: document.getElementById('asset').value,
    question: document.getElementById('question').value,
    lookback_minutes: parseInt(document.getElementById('lookback').value || '60', 10),
  };
  const out = document.getElementById('out');
  out.textContent = 'Loading...';
  const res = await fetch('/v1/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (data.assistant_response) {
    const summary = data.reasoning_summary ? data.reasoning_summary + '\n\n' : '';
    out.textContent = summary + data.assistant_response + '\n\n--- details ---\n' + JSON.stringify(data, null, 2);
    return;
  }
  out.textContent = JSON.stringify(data, null, 2);
}
</script>
</body>
</html>
"""
    return Response(content=html, media_type="text/html")


@app.post("/v1/chat")
async def chat(req: ChatRequest) -> dict[str, Any]:
    endpoint = f"{settings.orchestrator_url.rstrip('/')}/v1/explain"

    async def _call() -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            res = await client.post(
                endpoint,
                json={
                    "asset": req.asset,
                    "question": req.question,
                    "lookback_minutes": req.lookback_minutes,
                },
            )
            res.raise_for_status()
            return res.json()

    explain_fallback_reason: str | None = None
    try:
        response = await retry_async(_call, retries=2, base_delay=0.3)
    except Exception as exc:
        explain_fallback_reason = type(exc).__name__
        response = _fallback_explain_response(req, reason=explain_fallback_reason)
        logger.warning(
            "orchestrator_chat_fallback",
            extra={"context": {"asset": req.asset, "question": req.question, "error": str(exc)}},
        )

    assistant_response, assistant_status = await _generate_chat_response(response)
    if explain_fallback_reason:
        assistant_status = {
            **assistant_status,
            "upstream_fallback": True,
            "upstream_reason": explain_fallback_reason,
        }
    response["assistant_response"] = assistant_response
    response["chat_status"] = assistant_status
    response["reasoning_summary"] = _build_reasoning_summary(
        response.get("assistant_status") if isinstance(response.get("assistant_status"), dict) else None,
        assistant_status,
    )

    await emit_audit_event(
        "gateway",
        "chat",
        payload={
            "asset": req.asset,
            "question": req.question,
            "lookback_minutes": req.lookback_minutes,
            "chat_provider": assistant_status.get("provider"),
            "chat_model": assistant_status.get("model"),
            "fallback": bool(assistant_status.get("fallback")),
        },
    )
    logger.info(
        "chat_completed",
        extra={
            "context": {
                "asset": req.asset,
                "question": req.question,
                "chat_provider": assistant_status.get("provider"),
            }
        },
    )
    return response
