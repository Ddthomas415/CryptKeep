from fastapi import APIRouter, Depends, Request

from backend.app.api.deps import current_role, current_subject, require_min_role
from backend.app.core.errors import bad_request
from backend.app.core.envelopes import success
from backend.app.domain.policy.roles import Role
from backend.app.domain.state_machines.mode import Mode
from backend.app.domain.state_machines.safety import SafetyState
from backend.app.schemas.common import ApiEnvelope
from backend.app.schemas.terminal import (
    TerminalConfirmRequest,
    TerminalConfirmResponse,
    TerminalExecuteRequest,
    TerminalExecuteResponse,
)
from backend.app.services.risk_service import RiskService
from backend.app.services.settings_service import SettingsService
from backend.app.services.terminal_service import TerminalService

router = APIRouter()
service = TerminalService()
settings_service = SettingsService()
risk_service = RiskService()


def _current_mode() -> Mode:
    payload = settings_service.get_settings()
    raw = ((payload.get("general") if isinstance(payload, dict) else {}) or {}).get("default_mode")
    try:
        return Mode(str(raw or Mode.RESEARCH_ONLY.value))
    except Exception:
        return Mode.RESEARCH_ONLY


def _current_safety_state() -> SafetyState:
    summary = risk_service.get_summary()
    raw = str((summary.get("risk_status") if isinstance(summary, dict) else "") or SafetyState.SAFE.value).strip().lower()
    mapping = {
        "safe": SafetyState.SAFE,
        "warning": SafetyState.WARNING,
        "restricted": SafetyState.RESTRICTED,
        "paused": SafetyState.PAUSED,
        "blocked": SafetyState.BLOCKED,
    }
    return mapping.get(raw, SafetyState.SAFE)


@router.post("/execute", response_model=ApiEnvelope[TerminalExecuteResponse], dependencies=[Depends(require_min_role(Role.ANALYST))])
def execute_command(request: Request, payload: TerminalExecuteRequest) -> dict:
    data = service.execute(
        payload.command,
        role=current_role(request).value,
        subject=current_subject(request),
        mode=_current_mode().value,
        risk_state=_current_safety_state().value,
        kill_switch_on=False,
    )
    return success(data=data, request_id=request.state.request_id)


@router.post("/confirm", response_model=ApiEnvelope[TerminalConfirmResponse], dependencies=[Depends(require_min_role(Role.ANALYST))])
def confirm_command(request: Request, payload: TerminalConfirmRequest) -> dict:
    data = service.confirm(payload.confirmation_token, subject=current_subject(request))
    if data is None:
        raise bad_request(
            "Invalid or expired terminal confirmation token.",
            code="INVALID_CONFIRMATION_TOKEN",
        )
    return success(data=data, request_id=request.state.request_id)
