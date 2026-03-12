from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class ApiEnvelope(BaseModel, Generic[T]):
    request_id: str
    status: str
    data: T | None = None
    error: ErrorPayload | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
