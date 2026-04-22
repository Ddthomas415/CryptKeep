from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class LiveStateContext:
    authority: Literal["INTENT_CONSUMER", "RECONCILER", "UNKNOWN"]
    origin: str = "unknown"

class LiveStateViolation(Exception):
    pass

def _authorize_state_write(ctx: LiveStateContext | None) -> None:
    if ctx is None or ctx.authority == "UNKNOWN":
        raise LiveStateViolation("blocked state write: missing or unknown authority")
