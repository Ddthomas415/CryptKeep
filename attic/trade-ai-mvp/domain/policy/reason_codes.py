from __future__ import annotations

ROLE_NOT_ALLOWED = "ROLE_NOT_ALLOWED"
MODE_BLOCKED = "MODE_BLOCKED"
KILL_SWITCH_ACTIVE = "KILL_SWITCH_ACTIVE"
RISK_STATE_BLOCKED = "RISK_STATE_BLOCKED"
READ_ONLY_CONNECTION = "READ_ONLY_CONNECTION"
APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
TRADE_PERMISSION_MISSING = "TRADE_PERMISSION_MISSING"
FUTURES_NOT_SUPPORTED = "FUTURES_NOT_SUPPORTED"
SPOT_NOT_SUPPORTED = "SPOT_NOT_SUPPORTED"
SANDBOX_ONLY_CONNECTION = "SANDBOX_ONLY_CONNECTION"
CONNECTION_UNHEALTHY = "CONNECTION_UNHEALTHY"
CONNECTION_DEGRADED = "CONNECTION_DEGRADED"
TRADE_SIZE_ABOVE_THRESHOLD = "TRADE_SIZE_ABOVE_THRESHOLD"
LOW_CONFIDENCE_APPROVAL = "LOW_CONFIDENCE_APPROVAL"
FUTURES_APPROVAL_REQUIRED = "FUTURES_APPROVAL_REQUIRED"
NEW_ASSET_APPROVAL_REQUIRED = "NEW_ASSET_APPROVAL_REQUIRED"
NEW_EXCHANGE_APPROVAL_REQUIRED = "NEW_EXCHANGE_APPROVAL_REQUIRED"
RISK_RESTRICTED_APPROVAL = "RISK_RESTRICTED_APPROVAL"
UNKNOWN_COMMAND = "UNKNOWN_COMMAND"
COMMAND_BLOCKED = "COMMAND_BLOCKED"

MESSAGE_BY_CODE = {
    ROLE_NOT_ALLOWED: "Your role is not allowed to perform this action.",
    MODE_BLOCKED: "This action is blocked in the current mode.",
    KILL_SWITCH_ACTIVE: "New orders are blocked because the kill switch is active.",
    RISK_STATE_BLOCKED: "This action is blocked by the current risk state.",
    READ_ONLY_CONNECTION: "The selected exchange connection is read-only.",
    APPROVAL_REQUIRED: "This action requires approval before execution.",
    TRADE_PERMISSION_MISSING: "Trading permission is missing for this connection.",
    FUTURES_NOT_SUPPORTED: "Futures trading is not supported on this connection.",
    SPOT_NOT_SUPPORTED: "Spot trading is not supported on this connection.",
    SANDBOX_ONLY_CONNECTION: "This connection is sandbox-only and cannot place live orders.",
    CONNECTION_UNHEALTHY: "Connection is not healthy enough for execution.",
    CONNECTION_DEGRADED: "Connection is degraded; execution is temporarily blocked.",
    TRADE_SIZE_ABOVE_THRESHOLD: "Trade size exceeds the configured approval threshold.",
    LOW_CONFIDENCE_APPROVAL: "Trade confidence is below policy threshold and requires approval.",
    FUTURES_APPROVAL_REQUIRED: "Futures trades require approval by policy.",
    NEW_ASSET_APPROVAL_REQUIRED: "New asset trades require approval by policy.",
    NEW_EXCHANGE_APPROVAL_REQUIRED: "New exchange trades require approval by policy.",
    RISK_RESTRICTED_APPROVAL: "Restricted risk state requires approval.",
    UNKNOWN_COMMAND: "Unknown terminal command.",
    COMMAND_BLOCKED: "This terminal command is not allowed.",
}


def message_for(code: str) -> str:
    return MESSAGE_BY_CODE.get(str(code), "Action blocked by policy.")


def message_for_codes(codes: list[str]) -> str:
    if not codes:
        return "Allowed by current policy."
    return message_for(codes[0])

