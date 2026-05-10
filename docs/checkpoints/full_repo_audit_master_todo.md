# Full Repo Audit Master TODO

**Last updated:** 2026-05-10

This document is a master planning checklist for a future full-repo audit.
It is intentionally organized into bounded sections so the audit can be run in
multiple passes without requiring a single all-at-once review.

This is a planning artifact. It is **not** a claim that the listed sections
have already been audited to completion.

## How to use this document

For each section:

- define scope before starting
- collect visible evidence only
- record `SHOWN` findings separately from `UNVERIFIED` concerns
- choose one highest-leverage next action
- stop when the section has a clear handoff, not when every possible question
  has been exhausted

Recommended output per section:

- checklist status
- key files / surfaces covered
- findings by severity
- open questions
- next action

## Audit sections

### 1. Runtime Control Plane

Goal:

- confirm startup, stop, status, PID, lock, and health truth surfaces are
  coherent

Primary surfaces:

- `scripts/start_bot.py`
- `scripts/stop_bot.py`
- `scripts/bot_status.py`
- `scripts/run_bot_runner.py`
- `services/runtime/process_supervisor.py`
- `services/process/bot_runtime_truth.py`
- `runtime/flags/*.status.json`
- `runtime/health/*.json`

Checklist:

- [ ] Confirm canonical startup/stop/status path is documented and matches code.
- [ ] Verify process supervisor PID truth vs service status-file truth.
- [ ] Verify one-shot converge vs hot-reload behavior.
- [ ] Verify lock-file behavior for managed loops.
- [ ] Verify dead-process detection and stale-status handling.
- [ ] Verify current docs do not overstate legacy startup paths.

Current related artifact:

- [runtime_dashboard_audit_todo.md](./runtime_dashboard_audit_todo.md)
- [dashboard_runtime_digest_audit_pass1.md](./dashboard_runtime_digest_audit_pass1.md)
- [dashboard_overview_provenance_audit_pass1.md](./dashboard_overview_provenance_audit_pass1.md)
- [dashboard_operator_ui_audit_pass1.md](./dashboard_operator_ui_audit_pass1.md)
- [runtime_control_plane_audit_pass1.md](./runtime_control_plane_audit_pass1.md)

### 2. Paper Soak and Runtime Evidence

Goal:

- confirm what counts for the paper trading gate and whether soak evidence is
  decision-useful

Primary surfaces:

- `docs/LAUNCH_CHECKLIST.md`
- `docs/PAPER_SOAK_GATE.md`
- `scripts/report_supervised_soak_status.py`
- `scripts/report_paper_run_diagnostics.py`
- `scripts/run_pipeline_loop.py`
- `scripts/run_intent_executor.py`
- `.cbp_state/runtime/logs/`

Checklist:

- [ ] Verify Section 4.1 interpretation against current runtime design.
- [ ] Verify running soak state vs current desired state handling.
- [ ] Decide policy for symbol freeze vs rotation during soak.
- [ ] Decide policy for recovered transient API failures during soak.
- [ ] Verify evidence command/output is sufficient for operator sign-off.

Current related artifact:

- [paper_soak_runtime_evidence_audit_pass1.md](./paper_soak_runtime_evidence_audit_pass1.md)
- [paper_soak_incident_ledger_pass1.md](./paper_soak_incident_ledger_pass1.md)

### 3. Execution, Routing, and Risk Gates

Goal:

- audit submit/reconcile ownership, fail-closed behavior, and risk enforcement

Primary surfaces:

- `services/execution/`
- `services/risk/`
- `scripts/run_intent_consumer_safe.py`
- `scripts/run_live_reconciler_safe.py`

Checklist:

- [ ] Verify canonical submit owner by mode.
- [ ] Verify reconciler responsibility boundaries.
- [ ] Verify fail-closed paths on startup/runtime degradation.
- [ ] Verify risk accounting write paths and dedupe behavior.
- [ ] Verify current live/paper separation remains explicit and enforced.

### 4. Storage and State Integrity

Goal:

- audit SQLite stores, journaling, queue transitions, and crash consistency

Primary surfaces:

- `storage/`
- `services/os/file_utils.py`
- `trade_intents`, `paper_orders`, `paper_fills`, `journal_fills`, and related
  status/state stores

Checklist:

- [ ] Verify atomic write usage for runtime status and health surfaces.
- [ ] Verify queue transition invariants and idempotency.
- [ ] Verify fill journaling and replay safety.
- [ ] Verify crash-consistency assumptions are documented or enforced.
- [ ] Verify no stale identity overwrites or silent nulling paths remain.

### 5. Market Data and Symbol Management

Goal:

- audit pipeline data fetch behavior, scanner/selection logic, and multi-symbol
  control

Primary surfaces:

- `services/runtime/managed_symbol_config.py`
- `services/runtime/managed_symbol_selection.py`
- `services/runtime/dynamic_symbol_selector.py`
- `services/market_data/`
- `scripts/run_pipeline_loop.py`

Checklist:

- [ ] Verify symbol selection, propagation, and runtime truth alignment.
- [ ] Verify scanner cache behavior and refresh policy.
- [ ] Verify timeout/error handling in market-data path.
- [ ] Verify multi-symbol runtime semantics are documented and consistent.
- [ ] Verify symbol drift is visible to operators.

### 6. Dashboard and Operator UI

Goal:

- audit whether the UI reflects runtime truth accurately and safely

Primary surfaces:

- `dashboard/app.py`
- `dashboard/pages/`
- `dashboard/services/view_data.py`
- `dashboard/services/operator.py`
- `dashboard/services/copilot_reports.py`

Checklist:

- [ ] Verify runtime truth is visible in Operations UI.
- [ ] Verify fallback/sample data is explicitly labeled.
- [ ] Verify operator controls are clearly separated from read-only intelligence.
- [ ] Verify role-guard and allowlist behavior.
- [ ] Verify critical pages compile and basic tests pass.
- [ ] Manually smoke Overview, Operations, Copilot Reports, Markets, Signals, Settings.

Current related artifact:

- [runtime_dashboard_audit_todo.md](./runtime_dashboard_audit_todo.md)

### 7. AI Copilot and Alerting

Goal:

- audit monitor fidelity, report usefulness, context integrity, and safety

Primary surfaces:

- `services/ai_copilot/`
- `services/alerts/`
- `.cbp_state/runtime/ai_reports/`

Checklist:

- [ ] Verify alert monitor status truth and report-pointer fidelity.
- [ ] Verify log/alert dedupe behavior.
- [ ] Verify current context sources reflect canonical runtime/log surfaces.
- [ ] Verify read-only boundaries in UI and operator workflows.
- [ ] Verify copilot artifacts are discoverable and interpretable by operators.

### 8. Evidence, Promotion, and Governance

Goal:

- audit evidence generation, promotion gates, and governance sign-off surfaces

Primary surfaces:

- `services/analytics/`
- `services/backtest/`
- `dashboard/services/strategy_evaluation.py`
- `dashboard/services/promotion_ladder.py`
- `docs/governance/`

Checklist:

- [ ] Verify evidence status terminology matches actual data truth.
- [ ] Verify promotion gate blockers remain enforceable and visible.
- [ ] Verify synthetic/thin evidence cannot be presented as promotion-ready.
- [ ] Verify governance docs still match code and runtime surfaces.

### 9. Auth, Roles, and Safety Boundaries

Goal:

- audit dashboard auth, role guard, and operator-only control boundaries

Primary surfaces:

- `dashboard/auth_gate.py`
- `dashboard/role_guard.py`
- `services/security/`
- `tests/test_dashboard_operator_*`

Checklist:

- [ ] Verify auth runtime guard surfaces are current.
- [ ] Verify role boundaries on operator pages and actions.
- [ ] Verify no unauthorized path exists from viewer flows to state-changing controls.
- [ ] Verify current docs do not overclaim remote/public hardening.

### 10. Release, Validation, and Operator Docs

Goal:

- audit whether setup/run/validate/release instructions still match the repo

Primary surfaces:

- `scripts/validate.py`
- `scripts/pre_release_sanity.py`
- `tools/repo_doctor.py`
- `docs/`

Checklist:

- [ ] Verify checklist commands exist and still match this branch.
- [ ] Verify repo doctor / validation / preflight docs are current.
- [ ] Verify release and installer docs are consistent with actual scripts.
- [ ] Verify operator docs do not mix stale and canonical runtime paths.

## Suggested execution order

If you want the highest leverage order for a later full audit:

1. Runtime Control Plane
2. Paper Soak and Runtime Evidence
3. Dashboard and Operator UI
4. Execution, Routing, and Risk Gates
5. Storage and State Integrity
6. Market Data and Symbol Management
7. AI Copilot and Alerting
8. Evidence, Promotion, and Governance
9. Auth, Roles, and Safety Boundaries
10. Release, Validation, and Operator Docs

## Recommended starting point

If the audit begins while a paper soak is still active:

- start with **Runtime Control Plane**
- then **Paper Soak and Runtime Evidence**
- then **Dashboard and Operator UI**
- run the audit from a side worktree instead of the active soak checkout:
  [SAFE_WORKTREE_DURING_SOAK.md](../SAFE_WORKTREE_DURING_SOAK.md)

That order gives the operator-facing truth surfaces first, before deeper
subsystem review.

## Companion artifacts

- [runtime_dashboard_audit_todo.md](./runtime_dashboard_audit_todo.md)
- [launch_blockers_root_runtime.md](./launch_blockers_root_runtime.md)
- [PAPER_SOAK_GATE.md](../PAPER_SOAK_GATE.md)
- [CURRENT_RUNTIME_TRUTH.md](../CURRENT_RUNTIME_TRUTH.md)
