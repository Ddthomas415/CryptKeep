from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from services.execution.venue_capabilities import retry_is_safe_after_ambiguous_ack
from services.execution.lifecycle_boundary import fetch_order_via_boundary


@dataclass(frozen=True)
class ReconciliationResult:
    outcome: str  # confirmed_placed | confirmed_not_placed | inconclusive
    details: dict[str, Any]


class SafeToRetryAfterReconciliation(RuntimeError):
    pass


def reconcile_ambiguous_submission(
    *,
    venue: str,
    client: Any,
    symbol: str,
    client_oid: str | None,
    remote_order_id: str | None,
    age_sec: int | None,
) -> ReconciliationResult:
    if remote_order_id:
        try:
            order = fetch_order_via_boundary(
                client.build(),
                venue=venue,
                symbol=symbol,
                order_id=remote_order_id,
                source="order_reconciliation.remote_order_id",
            )
            if order:
                return ReconciliationResult("confirmed_placed", {"source": "remote_order_id"})
        except Exception:
            pass

    if client_oid and retry_is_safe_after_ambiguous_ack(
        venue=venue,
        has_remote_order_id=bool(remote_order_id),
        age_sec=age_sec,
    ):
        try:
            order = client.find_order_by_client_oid(symbol=symbol, client_oid=client_oid)
            if order:
                return ReconciliationResult("confirmed_placed", {"source": "client_oid"})
            return ReconciliationResult("confirmed_not_placed", {"source": "client_oid_not_found"})
        except Exception:
            return ReconciliationResult("inconclusive", {"source": "client_oid_lookup_error"})

    return ReconciliationResult("inconclusive", {"source": "no_safe_reconciliation_path"})
