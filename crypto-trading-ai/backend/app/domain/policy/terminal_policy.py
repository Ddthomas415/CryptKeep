from __future__ import annotations

from enum import Enum
import re

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

SAFE_TOKEN = r"[a-z0-9._:/-]+"
UNSAFE_COMMAND_CHARS_RE = re.compile(r"[;&|`$><]")

READ_ONLY_COMMAND_PATTERNS = (
    re.compile(r"^help$"),
    re.compile(r"^status$"),
    re.compile(rf"^market {SAFE_TOKEN}$"),
    re.compile(rf"^why {SAFE_TOKEN}$"),
    re.compile(rf"^news {SAFE_TOKEN}$"),
    re.compile(r"^risk show$"),
)

SEMI_SENSITIVE_COMMAND_PATTERNS = (
    re.compile(r"^connections test$"),
    re.compile(r"^approvals list$"),
    re.compile(r"^logs tail$"),
)

DANGEROUS_COMMAND_PATTERNS = (
    re.compile(rf"^mode set {SAFE_TOKEN}$"),
    re.compile(rf"^approve trade {SAFE_TOKEN}$"),
    re.compile(r"^kill-switch on$"),
    re.compile(r"^kill-switch off$"),
    re.compile(r"^trading resume$"),
)


def normalize_terminal_command(command: str) -> str:
    return " ".join(command.strip().lower().split())


def _matches_any(patterns: tuple[re.Pattern[str], ...], normalized: str) -> bool:
    return any(pattern.fullmatch(normalized) for pattern in patterns)


def is_command_syntax_safe(command: str) -> bool:
    normalized = normalize_terminal_command(command)
    if not normalized:
        return False
    return UNSAFE_COMMAND_CHARS_RE.search(normalized) is None


def is_approved_terminal_command(command: str) -> bool:
    normalized = normalize_terminal_command(command)
    if not is_command_syntax_safe(normalized):
        return False
    return (
        _matches_any(READ_ONLY_COMMAND_PATTERNS, normalized)
        or _matches_any(SEMI_SENSITIVE_COMMAND_PATTERNS, normalized)
        or _matches_any(DANGEROUS_COMMAND_PATTERNS, normalized)
    )


def is_dangerous_terminal_command(command: str) -> bool:
    normalized = normalize_terminal_command(command)
    if not is_command_syntax_safe(normalized):
        return False
    return _matches_any(DANGEROUS_COMMAND_PATTERNS, normalized)


def classify_command(command: str) -> CommandCategory:
    normalized = normalize_terminal_command(command)
    if _matches_any(DANGEROUS_COMMAND_PATTERNS, normalized):
        return CommandCategory.DANGEROUS
    if _matches_any(SEMI_SENSITIVE_COMMAND_PATTERNS, normalized):
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
    normalized = normalize_terminal_command(command)
    if not is_approved_terminal_command(normalized):
        return block_policy(
            reason_codes=["COMMAND_NOT_APPROVED"],
            user_message=(
                "Command rejected. Only approved product terminal commands are allowed."
            ),
            effective_mode=mode.value,
            effective_risk_state=risk_state.value,
        )

    category = classify_command(normalized)

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
    if category == CommandCategory.DANGEROUS and kill_switch_on and normalized == "trading resume":
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
