import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.api.deps import configured_api_tokens, resolve_api_principal
from backend.app.core.config import get_settings
from backend.app.core.envelopes import failure
from backend.app.core.logging import get_logger

logger = get_logger("api")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", f"req_{uuid.uuid4().hex[:12]}")
        request.state.request_id = request_id
        if request.url.path.startswith("/api/v1"):
            settings = get_settings()
            if not configured_api_tokens(settings):
                return JSONResponse(
                    status_code=503,
                    content=failure(
                        code="API_AUTH_NOT_CONFIGURED",
                        message="API authentication is not configured.",
                        request_id=request_id,
                    ),
                )
            principal = resolve_api_principal(request.headers.get("Authorization"), settings)
            if principal is None:
                return JSONResponse(
                    status_code=401,
                    content=failure(
                        code="UNAUTHORIZED",
                        message="Unauthorized",
                        request_id=request_id,
                    ),
                )
            role, subject = principal
            request.state.auth_role = role.value
            request.state.auth_subject = subject

        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)

        response.headers["X-Request-Id"] = request_id

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response


def register_middleware(app: FastAPI) -> None:
    app.add_middleware(RequestContextMiddleware)
