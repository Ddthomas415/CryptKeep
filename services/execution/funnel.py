from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class FunnelIntent:
    venue: str
    symbol: str
    side: str
    qty: float
    order_type: str = "market"
    price: float | None = None
    client_oid: str | None = None


@dataclass(frozen=True)
class FunnelResult:
    ok: bool
    reason: str
    response: dict[str, Any] | None = None
    details: dict[str, Any] | None = None


class FunnelExecutor:
    """
    Minimal routing shim only.
    Not the full gate-enforcement funnel.
    """

    def __init__(self, *, submit_fn: Callable[..., dict[str, Any]]):
        self._submit_fn = submit_fn

    def execute(self, intent: FunnelIntent) -> FunnelResult:
        try:
            resp = self._submit_fn(
                symbol=intent.symbol,
                side=intent.side,
                qty=float(intent.qty),
                price=intent.price,
                order_type=intent.order_type,
                client_oid=intent.client_oid,
            )
            return FunnelResult(ok=True, reason="submitted", response=resp, details={})
        except Exception as exc:
            return FunnelResult(
                ok=False,
                reason="submit_exception",
                response=None,
                details={"error": str(exc), "exception_type": type(exc).__name__},
            )
