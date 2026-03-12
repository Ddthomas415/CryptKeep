import re

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

import httpx
import redis
from backend.app.api.deps import get_app_settings
from backend.app.core.config import Settings
from backend.app.db.session import engine
from backend.app.schemas.health import HealthDependencyResponse, HealthLiveResponse

router = APIRouter()


def _sanitize_dependency_error(message: str | None) -> str | None:
    if not message:
        return None

    sanitized = message
    # Redact URL credentials e.g. scheme://user:pass@host
    sanitized = re.sub(r"://([^:/\s@]+):([^@\s/]+)@", "://***:***@", sanitized)

    # Redact common secret-bearing key/value fragments.
    for key in ("password", "passwd", "pwd", "api_key", "api_secret", "token", "passphrase", "secret"):
        sanitized = re.sub(rf"(?i)({key}\s*[=:]\s*)([^,\s;]+)", r"\1***", sanitized)

    return sanitized


@router.get("/live", response_model=HealthLiveResponse)
def live() -> dict:
    return HealthLiveResponse(status="ok", service="backend").model_dump()


def _evaluate_dependencies(settings: Settings) -> tuple[dict[str, str], dict[str, str], str]:
    checks: dict[str, str] = {}
    errors: dict[str, str] = {}

    db_status, db_error = _check_db()
    checks["db"] = db_status
    if db_status == "error" and db_error:
        errors["db"] = _sanitize_dependency_error(db_error) or "dependency check failed"

    redis_status, redis_error = _check_redis(settings.redis_url)
    checks["redis"] = redis_status
    if redis_status == "error" and redis_error:
        errors["redis"] = _sanitize_dependency_error(redis_error) or "dependency check failed"

    vector_status, vector_error = _check_vector(settings.vector_db_url)
    checks["vector_db"] = vector_status
    if vector_status == "error" and vector_error:
        errors["vector_db"] = _sanitize_dependency_error(vector_error) or "dependency check failed"

    overall_status = "degraded" if any(value == "error" for value in checks.values()) else "ok"
    return checks, errors, overall_status


def _build_dependency_payload(settings: Settings) -> dict:
    checks, errors, overall_status = _evaluate_dependencies(settings)
    payload: dict[str, object] = {
        "status": overall_status,
        "service": "backend",
        "checks": checks,
    }
    if errors:
        payload["errors"] = errors
    return HealthDependencyResponse.model_validate(payload).model_dump(exclude_none=True)


@router.get("/ready", response_model=HealthDependencyResponse)
def ready(settings: Settings | None = None) -> dict:
    settings = settings or get_app_settings()
    return _build_dependency_payload(settings)


def _check_db() -> tuple[str, str | None]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "ok", None
    except Exception as exc:
        if _dependency_is_unavailable(exc):
            return "unavailable", None
        return "error", str(exc)


def _check_redis(redis_url: str) -> tuple[str, str | None]:
    client = None
    try:
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
        client.ping()
        return "ok", None
    except Exception as exc:
        if _dependency_is_unavailable(exc):
            return "unavailable", None
        return "error", str(exc)
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


def _check_vector(vector_db_url: str) -> tuple[str, str | None]:
    try:
        response = httpx.get(f"{vector_db_url.rstrip('/')}/healthz", timeout=0.75)
        if response.is_success:
            return "ok", None
        return "error", f"HTTP {response.status_code}"
    except Exception as exc:
        if _dependency_is_unavailable(exc):
            return "unavailable", None
        return "error", str(exc)


def _dependency_is_unavailable(exc: Exception) -> bool:
    if isinstance(exc, (TimeoutError, OSError, redis.exceptions.ConnectionError, httpx.TimeoutException)):
        return True
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, OperationalError):
        message = str(exc).lower()
        if any(
            token in message
            for token in (
                "connection refused",
                "could not connect",
                "timeout",
                "timed out",
                "name or service not known",
                "temporary failure",
                "nodename nor servname provided",
                "network is unreachable",
                "no route to host",
            )
        ):
            return True

    message = str(exc).lower()
    return any(
        token in message
        for token in (
            "connection refused",
            "could not connect",
            "failed to establish a new connection",
            "timed out",
            "timeout",
            "name or service not known",
            "temporary failure",
            "nodename nor servname provided",
            "network is unreachable",
            "no route to host",
            "getaddrinfo failed",
        )
    )


@router.get("/deps", response_model=HealthDependencyResponse)
def deps(settings: Settings | None = None) -> dict:
    settings = settings or get_app_settings()
    return _build_dependency_payload(settings)
