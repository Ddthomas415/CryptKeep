from fastapi import APIRouter, Depends, Request

from backend.app.api.deps import require_min_role
from backend.app.core.errors import bad_request
from backend.app.core.envelopes import success
from backend.app.domain.policy.roles import Role
from backend.app.schemas.common import ApiEnvelope
from backend.app.schemas.settings import SettingsPayload, SettingsUpdatePayload
from backend.app.services.settings_service import SettingsService

router = APIRouter()
service = SettingsService()


@router.get("", response_model=ApiEnvelope[SettingsPayload], dependencies=[Depends(require_min_role(Role.OWNER))])
def get_settings(request: Request) -> dict:
    data = service.get_settings()
    return success(data=data, request_id=request.state.request_id)


@router.put("", response_model=ApiEnvelope[SettingsPayload], dependencies=[Depends(require_min_role(Role.OWNER))])
def update_settings(request: Request, payload: SettingsUpdatePayload) -> dict:
    patch = payload.model_dump(exclude_unset=True, exclude_none=True)
    patch = {
        section: updates
        for section, updates in patch.items()
        if not (isinstance(updates, dict) and len(updates) == 0)
    }
    if not patch:
        raise bad_request("At least one settings section is required.", code="EMPTY_SETTINGS_UPDATE")

    data = service.update_settings(patch=patch)
    return success(data=data, request_id=request.state.request_id)
