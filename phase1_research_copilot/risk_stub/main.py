from __future__ import annotations

from typing import Any
import hmac

from fastapi import FastAPI, Header, HTTPException

from shared.audit import emit_audit_event
from shared.config import get_settings
from shared.logging import configure_logging

settings = get_settings()
logger = configure_logging(settings.service_name or "risk-stub", settings.log_level)

app = FastAPI(title="risk-stub", version="0.1.0")

def _require_service_token(authorization: str | None) -> None:
    expected = str(getattr(settings, "service_token", "") or "")
    if not expected:
        raise HTTPException(status_code=503, detail="service_auth_not_configured")
    supplied = str(authorization or "").strip()
    prefix = "Bearer "
    if not supplied.startswith(prefix):
        raise HTTPException(status_code=401, detail="unauthorized")
    token = supplied[len(prefix):].strip()
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/healthz")
async def healthz() -> dict[str, Any]:
    return {
        "service": "risk-stub",
        "ok": True,
        "no_trading": True,
    }


@app.get("/v1/risk/status")
async def risk_status(authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
    _require_service_token(authorization)
    payload = {
        "execution_mode": "DISABLED",
        "gate": "NO_TRADING",
        "allow_trading": False,
        "reason": "Phase 1 research copilot mode",
    }
    await emit_audit_event("risk-stub", "risk_status", payload=payload)
    return payload


@app.post("/v1/risk/check-order")
async def check_order(authorization: str | None = Header(default=None, alias="Authorization")) -> dict[str, Any]:
    _require_service_token(authorization)
    payload = {
        "allowed": False,
        "gate": "NO_TRADING",
        "reason": "Order execution is disabled in Phase 1",
    }
    await emit_audit_event("risk-stub", "check_order", payload=payload)
    logger.info("risk_check_blocked", extra={"context": payload})
    return payload
