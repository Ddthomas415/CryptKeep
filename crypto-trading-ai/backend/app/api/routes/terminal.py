from fastapi import APIRouter, Request

from backend.app.core.errors import bad_request
from backend.app.core.envelopes import success
from backend.app.schemas.common import ApiEnvelope
from backend.app.schemas.terminal import (
    TerminalConfirmRequest,
    TerminalConfirmResponse,
    TerminalExecuteRequest,
    TerminalExecuteResponse,
)
from backend.app.services.terminal_service import TerminalService

router = APIRouter()
service = TerminalService()


@router.post("/execute", response_model=ApiEnvelope[TerminalExecuteResponse])
def execute_command(request: Request, payload: TerminalExecuteRequest) -> dict:
    data = service.execute(payload.command)
    return success(data=data, request_id=request.state.request_id)


@router.post("/confirm", response_model=ApiEnvelope[TerminalConfirmResponse])
def confirm_command(request: Request, payload: TerminalConfirmRequest) -> dict:
    data = service.confirm(payload.confirmation_token)
    if data is None:
        raise bad_request(
            "Invalid or expired terminal confirmation token.",
            code="INVALID_CONFIRMATION_TOKEN",
        )
    return success(data=data, request_id=request.state.request_id)
