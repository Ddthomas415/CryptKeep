from __future__ import annotations

from domain.policy.decision import PolicyDecision, allow, deny
from domain.policy.reason_codes import COMMAND_BLOCKED, KILL_SWITCH_ACTIVE, ROLE_NOT_ALLOWED, UNKNOWN_COMMAND
from domain.policy.roles import Role
from shared.schemas.api import Mode, RiskStatus

_READ_ONLY_PREFIXES = {
    "help",
    "status",
    "mode show",
    "market ",
    "why ",
    "news ",
    "archive ",
    "future unlocks",
    "risk show",
    "approvals list",
    "connections list",
}

_CONNECTION_TEST_PREFIX = "connections test "

_DANGEROUS_PREFIXES = {
    "mode set live_auto",
    "approve trade ",
    "reject trade ",
    "kill-switch on",
    "kill-switch off",
    "trading resume",
    "trading pause",
}

_BLOCKED_PREFIXES = {
    "bash",
    "sh ",
    "zsh ",
    "python",
    "pip ",
    "rm ",
    "sudo ",
    "git ",
    "cat ",
}


def _normalize(command: str) -> str:
    return str(command or "").strip().lower()


def _starts_with_any(text: str, prefixes: set[str]) -> bool:
    return any(text.startswith(p) for p in prefixes)


def can_run_terminal_command(
    *,
    role: Role,
    command: str,
    mode: Mode,
    risk_state: RiskStatus,
    kill_switch: bool,
    allow_viewer_read_only: bool = True,
    allow_trader_live_auto: bool = False,
) -> PolicyDecision:
    cmd = _normalize(command)
    if not cmd:
        return deny(mode=mode, risk_state=risk_state, reason_codes=[UNKNOWN_COMMAND])

    if _starts_with_any(cmd, _BLOCKED_PREFIXES):
        return deny(mode=mode, risk_state=risk_state, reason_codes=[COMMAND_BLOCKED])

    if _starts_with_any(cmd, _READ_ONLY_PREFIXES):
        if role in {Role.OWNER, Role.TRADER, Role.ANALYST}:
            return allow(mode=mode, risk_state=risk_state)
        if role == Role.VIEWER and allow_viewer_read_only:
            return allow(mode=mode, risk_state=risk_state)
        return deny(mode=mode, risk_state=risk_state, reason_codes=[ROLE_NOT_ALLOWED])

    if cmd.startswith(_CONNECTION_TEST_PREFIX):
        if role in {Role.OWNER, Role.TRADER, Role.ANALYST}:
            return allow(mode=mode, risk_state=risk_state)
        return deny(mode=mode, risk_state=risk_state, reason_codes=[ROLE_NOT_ALLOWED])

    if _starts_with_any(cmd, _DANGEROUS_PREFIXES):
        if role not in {Role.OWNER, Role.TRADER}:
            return deny(mode=mode, risk_state=risk_state, reason_codes=[ROLE_NOT_ALLOWED])
        if kill_switch and (cmd.startswith("trading resume") or cmd.startswith("mode set live_auto")):
            return deny(mode=mode, risk_state=risk_state, reason_codes=[KILL_SWITCH_ACTIVE])
        if cmd.startswith("mode set live_auto") and role == Role.TRADER and not allow_trader_live_auto:
            return deny(mode=mode, risk_state=risk_state, reason_codes=[ROLE_NOT_ALLOWED])
        return allow(mode=mode, risk_state=risk_state)

    return deny(mode=mode, risk_state=risk_state, reason_codes=[UNKNOWN_COMMAND])

