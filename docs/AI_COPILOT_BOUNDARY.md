# AI Copilot Boundary

This repo treats AI as a copilot and lab assistant, not as the live trading
brain.

## Allowed

- Read repo files, docs, tests, configs, and sanitized runtime state
- Summarize incidents, drift, and repo risk
- Generate reports, draft recommendations, and suggested patches
- Run tests, replay jobs, and paper-only simulations
- Open draft review artifacts for human approval

## Forbidden

- Arm live trading
- Disarm kill switch
- Submit or cancel live orders
- Write production config directly
- Modify databases directly
- Merge code without human review

The canonical forbidden action list lives in
`services/ai_copilot/policy.py::PROHIBITED_ACTIONS`.

## Protected paths

Changes touching the following areas are treated as approval-required:

- `services/execution/`
- `services/risk/`
- `services/admin/`
- `services/security/`
- `dashboard/auth_gate.py`
- `scripts/`
- `config/`

These are enforced as path-prefix rules in
`services/ai_copilot/policy.py`.

## Outputs

Repo copilot reports are written under the writable runtime root:

- `runtime/ai_reports/` in packaged/frozen mode
- `.cbp_state/runtime/ai_reports/` in repo/dev mode

Copilot runtime config belongs under:

- `runtime/config/ai_copilot.yaml` in packaged/frozen mode
- `.cbp_state/runtime/config/ai_copilot.yaml` in repo/dev mode

## AI roles

- Dashboard/ops copilot: read-only incident and health analysis
- Repo reviewer: diff-aware change review with explicit approval guidance
- Safety auditor: checks live-guard, authority, and fail-closed assumptions
- Simulation runner: paper/sandbox replay only

Codex, OpenAI, and Anthropic may all participate in these copilot roles, but
none of them are allowed to become the direct authority for live trading.
