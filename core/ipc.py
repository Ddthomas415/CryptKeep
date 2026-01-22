from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ServiceName(str, Enum):
    DATA_COLLECTOR = "data_collector"
    STRATEGY_RUNNER = "strategy_runner"
    EXECUTION_ROUTER = "execution_router"


class CommandType(str, Enum):
    START = "start"
    STOP = "stop"
    STATUS = "status"
    KILL = "kill"


class IPCEnvelope(BaseModel):
    """JSON-safe UI <-> backend control plane envelope."""
    model_config = ConfigDict(extra="forbid")

    version: Literal["1"] = "1"
    correlation_id: str
    ts: datetime = Field(default_factory=utc_now)

    @field_validator("ts")
    @classmethod
    def ts_must_be_tz_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.utcoffset() is None:
            raise ValueError("ts must be timezone-aware")
        return v


class ControlCommand(IPCEnvelope):
    kind: Literal["command"] = "command"
    command: CommandType
    service: Optional[ServiceName] = None  # None => all services
    params: Dict[str, Any] = Field(default_factory=dict)


class ServiceState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ControlStatus(IPCEnvelope):
    kind: Literal["status"] = "status"
    states: Dict[str, ServiceState] = Field(default_factory=dict)  # service -> state
    detail: Dict[str, Any] = Field(default_factory=dict)
