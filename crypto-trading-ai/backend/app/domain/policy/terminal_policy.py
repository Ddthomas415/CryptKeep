from __future__ import annotations

from enum import Enum

from backend.app.domain.policy.decision import PolicyDecision, allow_policy, block_policy
from backend.app.domain.policy.roles import Role, role_allows_action
from backend.app.domain.state_machines.mode import Mode
from backend.app.domain.state_machines.safety import SafetyState


class CommandCategory(str, Enum):
    READ_ONLY = "read_only"
    SEMI_SENSITIVE = "semi_sensitive"
    DANGEROUS = "dangerous"


READ_ONLY_PREFIXES = ("help", "status", "market ", "why ", "news ", "risk show")
SEMI_SENSITIVE_PREFIXES = ("connections test", "approvals list", "logs tail")
DANGEROUS_PREFIXES = (
    "mode set",
    "approve trade",
    "kill-switch on",
    "kill-switch off",
    "trading resume",
)


def classify_command(command: str) -> CommandCategory:
    normalized = command.strip().lower()
    if normalized.startswith(DANGEROUS_PREFIXES):
        return CommandCategory.DANGEROUS
    if normalized.startswith(SEMI_SENSITIVE_PREFIXES):
        return CommandCategory.SEMI_SENSITIVE
    return CommandCategory.READ_ONLY


def evaluate_terminal_command(
    *,
    role: Role,
    command: str,
    mode: Mode,
    risk_state: SafetyState,
    kill_switch_on: bool,
) -> PolicyDecision:
    category = classify_command(command)

    if category == CommandCategory.DANGEROUS and not role_allows_action(role, "terminal_dangerous"):
        return block_policy(
            reason_codes=["ROLE_NOT_ALLOWED"],
            user_message="Your role cannot run dangerous terminal commands.",
            effective_mode=mode.value,
            effective_risk_state=risk_state.value,
        )
    if category != CommandCategory.DANGEROUS and not role_allows_action(role, "terminal_read_only"):
        return block_policy(
            reason_codes=["ROLE_NOT_ALLOWED"],
            user_message="Your role cannot run terminal commands.",
            effective_mode=mode.value,
            effective_risk_state=risk_state.value,
        )
    if category == CommandCategory.DANGEROUS and kill_switch_on and command.lower().startswith(
        "trading resume"
    ):
        return block_policy(
            reason_codes=["KILL_SWITCH_ACTIVE"],
            user_message="Trading resume is blocked while kill switch is active.",
            effective_mode=mode.value,
            effective_risk_state=risk_state.value,
        )
    if category == CommandCategory.DANGEROUS and risk_state == SafetyState.BLOCKED:
        return block_policy(
            reason_codes=["RISK_STATE_BLOCKED"],
            user_message="Dangerous command blocked by risk state.",
            effective_mode=mode.value,
            effective_risk_state=risk_state.value,
        )

    requires_approval = category == CommandCategory.DANGEROUS
    return allow_policy(
        requires_approval=requires_approval,
        user_message="Command allowed." if not requires_approval else "Confirmation required.",
        effective_mode=mode.value,
        effective_risk_state=risk_state.value,
    )
