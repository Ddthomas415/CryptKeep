from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional

Action = Literal["BUY", "SELL", "HOLD"]

@dataclass(frozen=True)
class Signal:
    ok: bool
    action: Action
    reason: str
    confidence: float = 0.5
    ts_ms: Optional[int] = None
    close: Optional[float] = None
    features: Dict[str, Any] = field(default_factory=dict)

def hold(reason: str, **kw) -> Signal:
    return Signal(ok=True, action="HOLD", reason=reason, **kw)

def bad(reason: str, **kw) -> Signal:
    return Signal(ok=False, action="HOLD", reason=reason, **kw)
