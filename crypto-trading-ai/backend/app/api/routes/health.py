import re

from fastapi import APIRouter
from sqlalchemy import text

import httpx
import redis
from backend.app.api.deps import get_app_settings
from backend.app.core.config import Settings
from backend.app.db.session import engine

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


@router.get("/live")
def live() -> dict:
    return {"status": "ok", "service": "backend"}


def _evaluate_dependencies(settings: Settings) -> tuple[dict[str, str], dict[str, str], str]:
    checks: dict[str, str] = {}
    errors: dict[str, str] = {}

    db_status, db_error = _check_db()
    checks["db"] = db_status
    if db_error:
        errors["db"] = _sanitize_dependency_error(db_error) or "dependency check failed"

    redis_status, redis_error = _check_redis(settings.redis_url)
    checks["redis"] = redis_status
    if redis_error:
        errors["redis"] = _sanitize_dependency_error(redis_error) or "dependency check failed"

    vector_status, vector_error = _check_vector(settings.vector_db_url)
    checks["vector_db"] = vector_status
    if vector_error:
        errors["vector_db"] = _sanitize_dependency_error(vector_error) or "dependency check failed"

    overall_status = "ok" if all(value == "ok" for value in checks.values()) else "degraded"
    return checks, errors, overall_status


@router.get("/ready")
def ready(settings: Settings | None = None) -> dict:
    settings = settings or get_app_settings()
    checks, errors, overall_status = _evaluate_dependencies(settings)
    payload: dict[str, object] = {
        "status": overall_status,
        "service": "backend",
        "checks": checks,
    }
    if errors:
        payload["errors"] = errors
    return payload


def _check_db() -> tuple[str, str | None]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return "ok", None
    except Exception as exc:
        return "error", str(exc)


def _check_redis(redis_url: str) -> tuple[str, str | None]:
    client = None
    try:
        client = redis.Redis.from_url(redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
        client.ping()
        return "ok", None
    except Exception as exc:
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
        return "error", str(exc)


@router.get("/deps")
def deps(settings: Settings | None = None) -> dict:
    settings = settings or get_app_settings()
    checks, errors, overall_status = _evaluate_dependencies(settings)

    payload: dict[str, object] = {
        "status": overall_status,
        "service": "backend",
        "checks": checks,
    }
    if errors:
        payload["errors"] = errors
    return payload
