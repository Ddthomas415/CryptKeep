# Permissions and Policy Matrix (v1)

This document defines centralized permission/policy behavior for UI, API, terminal, and risk enforcement.

## Roles
- `owner`: full control including credentials/risk/mode/kill-switch/audit export.
- `trader`: operational trading control within policy.
- `analyst`: research + alerts + non-destructive operations.
- `viewer`: read-only.

## Modes
- `research_only`: execution disabled; research and recommendation generation allowed.
- `paper`: simulated execution allowed; live execution blocked.
- `live_approval`: live execution only after approval.
- `live_auto`: automated live execution subject to policy/risk/kill-switch.

## Risk States
- `safe`, `warning`, `restricted`, `paused`, `blocked`
- Risk state can override mode/role for execution paths.

## Kill Switch Rules
- Blocks risk-increasing execution actions when enabled.
- Allows research and risk-reducing actions (close/reduce/cancel).

## Connection Permissions
- Per-connection checks:
  - `read_enabled`, `trade_enabled`
  - `spot_supported`, `futures_supported`
  - `sandbox_only`
  - connection `status` (`connected`, `degraded`, `failed`, `disabled`)

## Approval Triggers
- Mode requires approval (`live_approval`)
- Size above threshold
- Low confidence
- Futures policy
- New asset/exchange
- Restricted risk state

## Policy Decision Contract
- `allowed: bool`
- `requires_approval: bool`
- `reason_codes: list[str]`
- `user_message: str`
- `effective_mode`
- `effective_risk_state`

## Implementation
- `domain/policy/roles.py`
- `domain/policy/modes.py`
- `domain/policy/risk_policy.py`
- `domain/policy/connection_policy.py`
- `domain/policy/approval_policy.py`
- `domain/policy/trade_policy.py`
- `domain/policy/terminal_policy.py`
- `domain/policy/decision.py`
- `domain/policy/reason_codes.py`

## Current Scope
- Central evaluators are implemented and test-covered.
- Route-level enforcement wiring remains tracked under `PM3`.

