from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from services.execution.venue_capabilities import retry_is_safe_after_ambiguous_ack
from services.execution.lifecycle_boundary import fetch_order_via_boundary

_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReconciliationResult:
    outcome: str  # confirmed_placed | confirmed_not_placed | inconclusive
    details: dict[str, Any]


class SafeToRetryAfterReconciliation(RuntimeError):
    pass


def _safe_close(ex: Any, *, where: str) -> None:
    try:
        ex.close()
    except Exception as exc:
        _LOG.warning("exchange close failed in %s: %s: %s", where, type(exc).__name__, exc)


def _fetch_order_compat(
    client: Any,
    *,
    venue: str,
    symbol: str,
    order_id: str,
    source: str,
) -> dict[str, Any] | None:
    built_client: Any | None = None
    fetch_client = client
    build = getattr(client, "build", None)
    if callable(build):
        built_client = build()
        fetch_client = built_client
    try:
        return fetch_order_via_boundary(
            fetch_client,
            venue=venue,
            symbol=symbol,
            order_id=order_id,
            source=source,
        )
    finally:
        if built_client is not None:
            _safe_close(built_client, where="_fetch_order_compat")


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
            order = _fetch_order_compat(
                client,
                venue=venue,
                symbol=symbol,
                order_id=remote_order_id,
                source="order_reconciliation.remote_order_id",
            )
            if order:
                return ReconciliationResult("confirmed_placed", {"source": "remote_order_id"})
        except Exception as _silent_err:
            _LOG.debug("suppressed: %s", _silent_err)

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
