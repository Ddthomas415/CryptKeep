from typing import Literal

from pydantic import BaseModel, Field

DependencyStatus = Literal["ok", "error"]


class HealthLiveResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["backend"]


class HealthDependencyResponse(BaseModel):
    status: Literal["ok", "degraded"]
    service: Literal["backend"]
    checks: dict[str, DependencyStatus]
    errors: dict[str, str] = Field(default_factory=dict)
