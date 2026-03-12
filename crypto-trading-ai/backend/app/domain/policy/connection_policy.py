from __future__ import annotations

from pydantic import BaseModel


class ConnectionPolicyContext(BaseModel):
    read_enabled: bool
    trade_enabled: bool
    spot_supported: bool
    futures_supported: bool
    sandbox_only: bool
    status: str


def can_submit_order(
    connection: ConnectionPolicyContext,
    *,
    venue_type: str,
    is_live: bool,
) -> tuple[bool, list[str]]:
    reason_codes: list[str] = []
    if connection.status not in {"connected", "degraded"}:
        reason_codes.append("CONNECTION_UNAVAILABLE")
    if not connection.trade_enabled:
        reason_codes.append("TRADE_PERMISSION_MISSING")
    if venue_type == "spot" and not connection.spot_supported:
        reason_codes.append("SPOT_NOT_SUPPORTED")
    if venue_type == "futures" and not connection.futures_supported:
        reason_codes.append("FUTURES_NOT_SUPPORTED")
    if is_live and connection.sandbox_only:
        reason_codes.append("SANDBOX_ONLY_CONNECTION")
    return len(reason_codes) == 0, reason_codes
