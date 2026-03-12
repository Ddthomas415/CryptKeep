from typing import Literal

from pydantic import BaseModel, ConfigDict

DependencyStatus = Literal["ok", "error", "unavailable"]


class HealthLiveResponse(BaseModel):
    status: Literal["ok"]
    service: Literal["backend"]


class HealthDependencyChecks(BaseModel):
    model_config = ConfigDict(extra="forbid")

    db: DependencyStatus
    redis: DependencyStatus
    vector_db: DependencyStatus


class HealthDependencyErrors(BaseModel):
    model_config = ConfigDict(extra="forbid")

    db: str | None = None
    redis: str | None = None
    vector_db: str | None = None


class HealthDependencyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok", "degraded"]
    service: Literal["backend"]
    checks: HealthDependencyChecks
    errors: HealthDependencyErrors | None = None
