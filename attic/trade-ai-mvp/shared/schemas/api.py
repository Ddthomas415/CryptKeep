from __future__ import annotations

from enum import StrEnum
from typing import Any, Generic, TypeVar
from uuid import uuid4

from fastapi import Request
from pydantic import BaseModel, Field


class ApiStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"


class Mode(StrEnum):
    RESEARCH_ONLY = "research_only"
    PAPER = "paper"
    LIVE_APPROVAL = "live_approval"
    LIVE_AUTO = "live_auto"


class RiskStatus(StrEnum):
    SAFE = "safe"
    WARNING = "warning"
    RESTRICTED = "restricted"
    PAUSED = "paused"
    BLOCKED = "blocked"


class ConnectionStatus(StrEnum):
    CONNECTED = "connected"
    DEGRADED = "degraded"
    FAILED = "failed"
    DISABLED = "disabled"


class Timeline(StrEnum):
    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RecommendationSide(StrEnum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


class ApiError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


T = TypeVar("T")


class ApiEnvelope(BaseModel, Generic[T]):
    request_id: str
    status: ApiStatus
    data: T | None = None
    error: ApiError | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


def resolve_request_id(request: Request | None = None, request_id: str | None = None) -> str:
    if request_id and str(request_id).strip():
        return str(request_id).strip()
    if request is not None:
        hdr = str(request.headers.get("X-Request-Id", "")).strip()
        if hdr:
            return hdr
    return str(uuid4())


def success_envelope(
    *,
    data: T,
    request: Request | None = None,
    request_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> ApiEnvelope[T]:
    return ApiEnvelope[T](
        request_id=resolve_request_id(request=request, request_id=request_id),
        status=ApiStatus.SUCCESS,
        data=data,
        error=None,
        meta=meta or {},
    )


def error_envelope(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request: Request | None = None,
    request_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> ApiEnvelope[None]:
    return ApiEnvelope[None](
        request_id=resolve_request_id(request=request, request_id=request_id),
        status=ApiStatus.ERROR,
        data=None,
        error=ApiError(code=code, message=message, details=details or {}),
        meta=meta or {},
    )

