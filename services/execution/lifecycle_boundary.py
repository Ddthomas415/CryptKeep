from __future__ import annotations

from typing import Any

from services.execution.event_log import log_event


def _log_lifecycle_event(
    venue: str,
    symbol: str,
    event: str,
    *,
    ref_id: str | None = None,
    source: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    payload = dict(extra or {})
    if source:
        payload["source"] = source
    log_event(venue, symbol, event, ref_id=ref_id, payload=payload)


def cancel_order_via_boundary(
    ex: Any,
    *,
    venue: str,
    symbol: str,
    order_id: str,
    reason: str | None = None,
    source: str = "lifecycle_boundary.cancel",
) -> dict:
    oid = str(order_id)
    _log_lifecycle_event(
        venue,
        symbol,
        "lifecycle_cancel_requested",
        ref_id=oid,
        source=source,
        extra={"reason": reason},
    )
    try:
        out = ex.cancel_order(oid, symbol)
    except Exception as exc:
        _log_lifecycle_event(
            venue,
            symbol,
            "lifecycle_cancel_result",
            ref_id=oid,
            source=source,
            extra={"ok": False, "error": f"{type(exc).__name__}:{exc}"},
        )
        raise
    _log_lifecycle_event(
        venue,
        symbol,
        "lifecycle_cancel_result",
        ref_id=oid,
        source=source,
        extra={"ok": True, "status": str((out or {}).get("status") or "")},
    )
    return out


async def cancel_order_async_via_boundary(
    ex: Any,
    *,
    venue: str,
    symbol: str,
    order_id: str,
    reason: str | None = None,
    source: str = "lifecycle_boundary.cancel_async",
) -> dict:
    oid = str(order_id)
    _log_lifecycle_event(
        venue,
        symbol,
        "lifecycle_cancel_requested",
        ref_id=oid,
        source=source,
        extra={"reason": reason},
    )
    try:
        out = await ex.cancel_order(oid, symbol)
    except Exception as exc:
        _log_lifecycle_event(
            venue,
            symbol,
            "lifecycle_cancel_result",
            ref_id=oid,
            source=source,
            extra={"ok": False, "error": f"{type(exc).__name__}:{exc}"},
        )
        raise
    _log_lifecycle_event(
        venue,
        symbol,
        "lifecycle_cancel_result",
        ref_id=oid,
        source=source,
        extra={"ok": True, "status": str((out or {}).get("status") or "")},
    )
    return out


def fetch_order_via_boundary(
    ex: Any,
    *,
    venue: str,
    symbol: str,
    order_id: str,
    source: str = "lifecycle_boundary.fetch_order",
) -> dict:
    oid = str(order_id)
    _log_lifecycle_event(
        venue,
        symbol,
        "lifecycle_fetch_order_requested",
        ref_id=oid,
        source=source,
    )
    try:
        out = ex.fetch_order(oid, symbol)
    except Exception as exc:
        _log_lifecycle_event(
            venue,
            symbol,
            "lifecycle_fetch_order_result",
            ref_id=oid,
            source=source,
            extra={"ok": False, "error": f"{type(exc).__name__}:{exc}"},
        )
        raise
    _log_lifecycle_event(
        venue,
        symbol,
        "lifecycle_fetch_order_result",
        ref_id=oid,
        source=source,
        extra={"ok": True, "status": str((out or {}).get("status") or "")},
    )
    return out


def fetch_my_trades_via_boundary(
    ex: Any,
    *,
    venue: str,
    symbol: str,
    since_ms: int | None = None,
    limit: int | None = 200,
    source: str = "lifecycle_boundary.fetch_my_trades",
) -> list[dict]:
    _log_lifecycle_event(
        venue,
        symbol,
        "lifecycle_fetch_trades_requested",
        source=source,
        extra={"since_ms": since_ms, "limit": limit},
    )
    try:
        out = list(ex.fetch_my_trades(symbol, since=since_ms, limit=limit) or [])
    except Exception as exc:
        _log_lifecycle_event(
            venue,
            symbol,
            "lifecycle_fetch_trades_result",
            source=source,
            extra={"ok": False, "error": f"{type(exc).__name__}:{exc}"},
        )
        raise
    _log_lifecycle_event(
        venue,
        symbol,
        "lifecycle_fetch_trades_result",
        source=source,
        extra={"ok": True, "count": len(out)},
    )
    return out


def fetch_open_orders_via_boundary(
    ex: Any,
    *,
    venue: str,
    symbol: str,
    source: str = "lifecycle_boundary.fetch_open_orders",
) -> list[dict]:
    _log_lifecycle_event(
        venue,
        symbol,
        "lifecycle_fetch_open_orders_requested",
        source=source,
    )
    try:
        out = list(ex.fetch_open_orders(symbol) or [])
    except Exception as exc:
        _log_lifecycle_event(
            venue,
            symbol,
            "lifecycle_fetch_open_orders_result",
            source=source,
            extra={"ok": False, "error": f"{type(exc).__name__}:{exc}"},
        )
        raise
    _log_lifecycle_event(
        venue,
        symbol,
        "lifecycle_fetch_open_orders_result",
        source=source,
        extra={"ok": True, "count": len(out)},
    )
    return out
