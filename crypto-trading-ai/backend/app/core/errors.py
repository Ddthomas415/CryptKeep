import json

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.core.envelopes import failure
from backend.app.core.logging import get_logger

logger = get_logger("backend.errors")
SENSITIVE_KEYS = {"api_key", "api_secret", "passphrase", "secret", "credential", "credentials"}


def bad_request(message: str, code: str = "VALIDATION_ERROR") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=failure(code=code, message=message)["error"],
    )


def not_found(message: str, code: str = "NOT_FOUND") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=failure(code=code, message=message)["error"],
    )


def unauthorized(message: str = "Unauthorized", code: str = "UNAUTHORIZED") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=failure(code=code, message=message)["error"],
    )


def internal_error(message: str = "Internal error", code: str = "INTERNAL_ERROR") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=failure(code=code, message=message)["error"],
    )


def _redact_sensitive_value(value):
    if isinstance(value, dict):
        redacted: dict = {}
        for key, nested in value.items():
            if str(key).lower() in SENSITIVE_KEYS:
                redacted[key] = "***redacted***"
            else:
                redacted[key] = _redact_sensitive_value(nested)
        return redacted
    if isinstance(value, (list, tuple, set)):
        return [_redact_sensitive_value(item) for item in value]
    if isinstance(value, BaseException):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)
    return value


def _sanitize_validation_errors(errors: list[dict]) -> list[dict]:
    sanitized: list[dict] = []
    for error in errors:
        item = dict(error)
        # Never echo the raw input payload in validation errors.
        item.pop("input", None)
        if "ctx" in item:
            item["ctx"] = _redact_sensitive_value(item["ctx"])
        sanitized.append(item)
    return sanitized


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail and "message" in detail:
            payload = failure(
                code=str(detail["code"]),
                message=str(detail["message"]),
                details=detail.get("details") or {},
                request_id=request_id,
            )
        else:
            payload = failure(
                code="HTTP_ERROR",
                message=str(detail) if detail else "Request failed.",
                request_id=request_id,
            )
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        payload = failure(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            details={"errors": _sanitize_validation_errors(exc.errors())},
            request_id=request_id,
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content=payload)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        logger.exception(
            "unhandled_exception",
            extra={"request_id": request_id, "path": str(request.url.path)},
        )
        payload = failure(
            code="INTERNAL_ERROR",
            message="Internal server error.",
            request_id=request_id,
        )
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
