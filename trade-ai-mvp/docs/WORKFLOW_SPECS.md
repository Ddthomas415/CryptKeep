# Workflow Specs (v1)

Canonical user journeys for Phase 1/1.5 with API, policy, state, and audit mapping.

## WF-A: Connect Exchange

1. User opens Connections and submits credentials.
2. System tests connection.
3. If successful, connection metadata is created/updated.
4. Result is visible on Dashboard/Connections.

### Mapping

- API:
  - `POST /api/v1/connections/exchanges/test`
  - `POST /api/v1/connections/exchanges`
  - `PATCH /api/v1/connections/exchanges/{id}`
  - `GET /api/v1/connections/exchanges`
- Policy checks:
  - role must be `owner|trader` for create/update
  - test allowed for `owner|trader|analyst`
- State transitions:
  - connection status: `disabled|failed -> connected|degraded`
- Audit:
  - `service=connections action=test_connection`
  - `service=connections action=upsert_connection`

## WF-B: Ask Research Query ("Why is SOL moving?")

1. User submits question/asset/filter set.
2. Orchestrator gathers market/news/archive evidence.
3. Explanation is returned with confidence and evidence.
4. Response is logged for traceability.

### Mapping

- API:
  - `POST /api/v1/research/explain`
  - optional support calls: `POST /api/v1/research/search`, `GET /api/v1/market/{asset}/snapshot`
- Policy checks:
  - all roles can query research
- State transitions:
  - research query lifecycle: `received -> synthesized -> persisted`
- Audit:
  - `service=orchestrator action=explain_asset`

## WF-C: Approve Paper Trade

1. User reviews recommendation in paper mode.
2. Approval check runs policy gates.
3. Approval result is stored and surfaced.

### Mapping

- API:
  - `GET /api/v1/trading/recommendations`
  - `POST /api/v1/trading/recommendations/{id}/approve` with `mode=paper`
  - `GET /api/v1/approvals`
- Policy checks:
  - role `owner|trader`
  - mode not `research_only`
  - kill switch must not block risk-increasing paths
  - risk state must allow execution path
- State transitions:
  - recommendation: `ready|pending_review -> approved`
  - approval: `pending -> approved|rejected|expired`
  - order (paper): `created -> submitted -> filled|cancelled|rejected`
- Audit:
  - `service=trading action=approve_recommendation`
  - `service=risk action=evaluate_trade_policy`

## WF-D: Approve Live Trade

1. User is in `live_approval` mode.
2. Recommendation is reviewed and approved.
3. Final policy check passes and live submission path opens.

### Mapping

- API:
  - `POST /api/v1/trading/recommendations/{id}/approve` with `mode=live_approval`
  - `POST /api/v1/approvals/{id}/approve`
- Policy checks:
  - role `owner|trader`
  - mode `live_approval` or `live_auto` policy-compatible
  - connection permissions include trade and venue support
  - kill switch off
  - risk state not `paused|blocked` for new risk-increasing order
- State transitions:
  - recommendation: `pending_review -> approved -> converted_to_order`
  - approval: `pending -> approved`
  - order: `created -> submitted -> acknowledged -> ...`
- Audit:
  - `service=trading action=approve_live_trade`
  - `service=risk action=final_gate_check`

## WF-E: Kill Switch Activation/Release

1. Authorized user toggles kill switch.
2. Risk state is recomputed and execution paths update.
3. Dashboard, trading, and terminal reflect the new state.

### Mapping

- API:
  - `POST /api/v1/risk/kill-switch`
  - `GET /api/v1/risk/summary`
- Policy checks:
  - role `owner|trader`
- State transitions:
  - kill switch: `off -> arming -> on` and `on -> releasing -> off`
  - safety state may move to `blocked` while kill switch is on
- Audit:
  - `service=risk action=kill_switch_changed`

## WF-F: Terminal Command Execution

1. User sends command to controlled terminal endpoint.
2. Command is validated against role-aware allowlist.
3. Dangerous commands return `requires_confirmation=true`.
4. Confirm endpoint executes tokenized command.

### Mapping

- API:
  - `POST /api/v1/terminal/execute`
  - `POST /api/v1/terminal/confirm`
- Policy checks:
  - terminal allowlist policy (`domain/policy/terminal_policy.py`)
  - role gates + kill-switch constraints for risky commands
- State transitions:
  - terminal command: `requested -> waiting_confirmation -> executed|blocked`
- Audit:
  - `service=terminal action=execute|confirm`

## Cross-workflow invariants

- All responses use the same API envelope (`request_id/status/data/error/meta`).
- Every risk-increasing action must pass: role -> mode -> kill switch -> risk state -> connection permission -> approval policy.
- Terminal endpoints must not execute shell commands.
