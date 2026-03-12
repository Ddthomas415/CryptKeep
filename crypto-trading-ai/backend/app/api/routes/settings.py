from fastapi import APIRouter, Request

from backend.app.core.errors import bad_request
from backend.app.core.envelopes import success
from backend.app.schemas.common import ApiEnvelope
from backend.app.schemas.settings import SettingsPayload, SettingsUpdatePayload
from backend.app.services.settings_service import SettingsService

router = APIRouter()
service = SettingsService()


@router.get("", response_model=ApiEnvelope[SettingsPayload])
def get_settings(request: Request) -> dict:
    data = service.get_settings()
    return success(data=data, request_id=request.state.request_id)


@router.put("", response_model=ApiEnvelope[SettingsPayload])
def update_settings(request: Request, payload: SettingsUpdatePayload) -> dict:
    patch = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not patch:
        raise bad_request("At least one settings section is required.", code="EMPTY_SETTINGS_UPDATE")

    data = service.update_settings(patch=patch)
    return success(data=data, request_id=request.state.request_id)
