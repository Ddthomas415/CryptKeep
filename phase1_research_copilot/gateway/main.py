from __future__ import annotations

from typing import Any

import httpx
from fastapi import FastAPI, Response
from pydantic import BaseModel

from shared.audit import emit_audit_event
from shared.config import get_settings
from shared.logging import configure_logging
from shared.retry import retry_async

settings = get_settings()
logger = configure_logging(settings.service_name or "gateway", settings.log_level)

app = FastAPI(title="gateway", version="0.1.0")


class ChatRequest(BaseModel):
    asset: str
    question: str
    lookback_minutes: int = 60


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {"service": "gateway", "ok": True, "ui": True}


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

    response = await retry_async(_call, retries=2, base_delay=0.3)
    await emit_audit_event(
        "gateway",
        "chat",
        payload={"asset": req.asset, "question": req.question, "lookback_minutes": req.lookback_minutes},
    )
    logger.info("chat_completed", extra={"context": {"asset": req.asset, "question": req.question}})
    return response
