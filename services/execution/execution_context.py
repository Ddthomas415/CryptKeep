from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class ExecutionContext:
    mode: Literal["live", "paper"]
    authority: Literal["LIVE_SUBMIT_OWNER", "NON_SUBMITTING_LIVE", "PAPER"]
    origin: str = "unknown"

class LiveAuthorityViolation(Exception):
    pass

def _authorize_live(context: ExecutionContext | None) -> None:
    if context is None:
        raise LiveAuthorityViolation("blocked submit: missing execution context")
    if context.mode != "live":
        return
    if context.authority != "LIVE_SUBMIT_OWNER":
        raise LiveAuthorityViolation(
            f"blocked live submit: authority={context.authority}, origin={context.origin}"
        )
