from collections.abc import Generator
import hmac

from fastapi import Request
from sqlalchemy.orm import Session

from backend.app.core.config import Settings, get_settings
from backend.app.core.errors import forbidden, unauthorized
from backend.app.db.session import get_db
from backend.app.domain.policy.roles import Role


def get_app_settings() -> Settings:
    return get_settings()


def get_db_session() -> Generator[Session, None, None]:
    yield from get_db()


_ROLE_ORDER = {
    Role.VIEWER: 0,
    Role.ANALYST: 1,
    Role.TRADER: 2,
    Role.OWNER: 3,
}


def configured_api_tokens(settings: Settings | None = None) -> dict[Role, str]:
    active = settings or get_settings()
    items = {
        Role.OWNER: str(active.owner_api_token or "").strip(),
        Role.TRADER: str(active.trader_api_token or "").strip(),
        Role.ANALYST: str(active.analyst_api_token or "").strip(),
        Role.VIEWER: str(active.viewer_api_token or "").strip(),
    }
    return {role: token for role, token in items.items() if token}


def resolve_api_principal(authorization: str | None, settings: Settings | None = None) -> tuple[Role, str] | None:
    supplied = str(authorization or "").strip()
    prefix = "Bearer "
    if not supplied.startswith(prefix):
        return None
    token = supplied[len(prefix) :].strip()
    if not token:
        return None
    for role, expected in configured_api_tokens(settings).items():
        if hmac.compare_digest(token, expected):
            return role, f"api-token:{role.value}"
    return None


def current_role(request: Request) -> Role:
    raw = getattr(request.state, "auth_role", None)
    if raw is None:
        raise unauthorized()
    return Role(str(raw))


def current_subject(request: Request) -> str:
    raw = getattr(request.state, "auth_subject", "")
    return str(raw or "")


def require_min_role(required_role: Role):
    def _dep(request: Request) -> None:
        current = current_role(request)
        if _ROLE_ORDER[current] < _ROLE_ORDER[required_role]:
            raise forbidden(message=f"{required_role.value} role required.")

    return _dep
