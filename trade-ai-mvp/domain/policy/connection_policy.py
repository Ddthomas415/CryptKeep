from __future__ import annotations

from dataclasses import dataclass

from domain.policy.decision import PolicyDecision, allow, deny
from domain.policy.reason_codes import (
    CONNECTION_DEGRADED,
    CONNECTION_UNHEALTHY,
    FUTURES_NOT_SUPPORTED,
    READ_ONLY_CONNECTION,
    SANDBOX_ONLY_CONNECTION,
    SPOT_NOT_SUPPORTED,
    TRADE_PERMISSION_MISSING,
)
from shared.schemas.api import ConnectionStatus, Mode, RiskStatus


@dataclass(frozen=True)
class ConnectionPermission:
    read_enabled: bool
    trade_enabled: bool
    spot_supported: bool
    futures_supported: bool
    sandbox_only: bool
    status: ConnectionStatus


def evaluate_connection_for_trade(
    *,
    mode: Mode,
    risk_state: RiskStatus,
    connection: ConnectionPermission,
    venue_type: str,
    risk_increasing: bool,
) -> PolicyDecision:
    if not connection.trade_enabled:
        code = READ_ONLY_CONNECTION if connection.read_enabled else TRADE_PERMISSION_MISSING
        return deny(mode=mode, risk_state=risk_state, reason_codes=[code])

    if connection.status in {ConnectionStatus.FAILED, ConnectionStatus.DISABLED}:
        return deny(mode=mode, risk_state=risk_state, reason_codes=[CONNECTION_UNHEALTHY])

    if risk_increasing and connection.status == ConnectionStatus.DEGRADED:
        return deny(mode=mode, risk_state=risk_state, reason_codes=[CONNECTION_DEGRADED])

    if connection.sandbox_only and mode in {Mode.LIVE_APPROVAL, Mode.LIVE_AUTO}:
        return deny(mode=mode, risk_state=risk_state, reason_codes=[SANDBOX_ONLY_CONNECTION])

    vt = str(venue_type or "").lower().strip()
    if vt == "futures" and not connection.futures_supported:
        return deny(mode=mode, risk_state=risk_state, reason_codes=[FUTURES_NOT_SUPPORTED])
    if vt == "spot" and not connection.spot_supported:
        return deny(mode=mode, risk_state=risk_state, reason_codes=[SPOT_NOT_SUPPORTED])

    return allow(mode=mode, risk_state=risk_state)

