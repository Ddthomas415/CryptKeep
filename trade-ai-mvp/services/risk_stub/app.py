from __future__ import annotations

from fastapi import FastAPI

from shared.audit_client import emit_audit_event
from shared.config import get_settings
from shared.logging import get_logger

settings = get_settings("risk_stub")
logger = get_logger("risk_stub", settings.log_level)
app = FastAPI(title="risk_stub")

_VALID_GATES = {"ALLOW", "ALLOW_REDUCE_ONLY", "HALT_NEW_EXPOSURE", "FULL_STOP"}


def _as_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _allowed_actions_for_gate(gate: str, *, paper_enabled: bool) -> list[str]:
    actions = ["OBSERVE_ONLY"]
    if not paper_enabled:
        return actions
    actions.append("PAPER_CANCEL")
    if gate == "ALLOW":
        actions.extend(["PAPER_SUBMIT", "PAPER_REDUCE"])
    elif gate in {"ALLOW_REDUCE_ONLY", "HALT_NEW_EXPOSURE"}:
        actions.append("PAPER_REDUCE")
    return actions


def _action_allowed(gate: str, requested_action: str) -> bool:
    action = requested_action.lower()
    if action in {"cancel_order", "cancel", "paper_cancel"}:
        return gate in {"ALLOW", "ALLOW_REDUCE_ONLY", "HALT_NEW_EXPOSURE"}
    if action in {"reduce_position", "paper_reduce"}:
        return gate in {"ALLOW", "ALLOW_REDUCE_ONLY", "HALT_NEW_EXPOSURE"}
    # Defaults to open/new exposure action.
    return gate == "ALLOW"


def _decide_gate(request: dict) -> tuple[str, str]:
    mode = str(request.get("mode") or "research").lower()
    if mode != "paper":
        return "FULL_STOP", "Phase 1 research mode only"
    if not settings.paper_trading_enabled:
        return "FULL_STOP", "Paper trading disabled"

    forced = str(request.get("force_gate") or "").upper()
    if forced in _VALID_GATES:
        return forced, f"Forced gate override: {forced}"

    daily_pnl = _as_float(request.get("daily_pnl"), 0.0)
    proposed_notional = abs(_as_float(request.get("proposed_notional_usd"), _as_float(request.get("notional"), 0.0)))
    position_qty = abs(_as_float(request.get("position_qty"), 0.0))

    if daily_pnl <= -abs(settings.paper_daily_loss_limit_usd):
        return "FULL_STOP", "Daily loss limit breached"
    if position_qty >= abs(settings.paper_max_position_qty):
        return "ALLOW_REDUCE_ONLY", "Position quantity limit reached"
    if proposed_notional > abs(settings.paper_max_notional_usd):
        return "HALT_NEW_EXPOSURE", "Max notional exceeded"
    return "ALLOW", "Within configured paper risk limits"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/risk/evaluate")
async def evaluate_risk(req: dict | None = None) -> dict:
    request = req or {}
    mode = str(request.get("mode") or "research").lower()
    requested_action = str(request.get("requested_action") or "open_position").lower()
    gate, reason = _decide_gate(request)
    paper_enabled = mode == "paper" and settings.paper_trading_enabled
    paper_approved = paper_enabled and _action_allowed(gate, requested_action)
    allowed_actions = _allowed_actions_for_gate(gate, paper_enabled=paper_enabled)

    payload = {
        "execution_disabled": True,
        "approved": False,
        "paper_approved": paper_approved,
        "gate": gate,
        "allowed_actions": allowed_actions,
        "reason": reason,
        "requested_action": requested_action,
        "limits": {
            "paper_max_notional_usd": settings.paper_max_notional_usd,
            "paper_max_position_qty": settings.paper_max_position_qty,
            "paper_daily_loss_limit_usd": settings.paper_daily_loss_limit_usd,
        },
    }
    logger.info("risk_evaluated", extra={"context": payload})
    await emit_audit_event(
        settings=settings,
        service_name="risk_stub",
        event_type="risk_evaluate",
        message="Risk evaluated in research-only mode",
        payload=payload,
    )
    return payload
