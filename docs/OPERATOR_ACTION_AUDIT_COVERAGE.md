# CryptKeep Operator Action Audit Coverage

Status: `POLICY_DOCUMENTED` · Matrix tooling: `scripts/audit_coverage_matrix.py` (proof-ready)

## Purpose

Define which operator actions and state transitions need a who/what/when audit
trail before capped live. This document does not claim current event coverage is
complete.

## Current Boundary

SHOWN:

- Intent and fill stores exist.
- Work logs and deployment records capture many engineering and migration
  decisions.
- Dashboard/API tests reference audit event surfaces.

UNVERIFIED:

- Every material operator action does not yet have a proven who/what/when
  record.
- Dashboard, CLI, automation, and system-triggered actions have not been
  reconciled into one coverage matrix.
- No capped-live incident-review drill has replayed actions from the event
  trail.

## Coverage Matrix Tooling

`scripts/audit_coverage_matrix.py` (2026-07-10) turns this policy into
executable launch-packet evidence: every family below is classified
SHOWN/PARTIAL/MISSING with store pointers and runtime probes
(`--json`, `--markdown`, `--evidence-dest` writes the packet artifact,
`--strict` fails unless every family is SHOWN — the capped-live posture).
`tests/test_operator_audit_coverage.py` parses the family list FROM this
document so the matrix and policy cannot drift silently. 2026-07-15 update:
`services.audit.operator_event_journal` provides the unified append-only JSONL
substrate and `scripts/record_operator_event.py` can append manual drill
events with required fields and secret-key redaction. `scripts/check_operator_event_secrets.py`
scans the journal for unredacted secret-like payload fields without printing
the leaked values. `services.admin.live_disable_wizard.disable_live_now()` and
`services.admin.live_enable_wizard.disable_live()` now append best-effort
operator events for safety-increasing live-disable/halt transitions.
`services.execution.live_enable.enable_live()`,
`services.admin.live_enable_wizard.enable_live()`, and
`services.admin.resume_gate.resume_if_safe()` now append required
risk-increasing live-enable/resume events and roll back fail-closed when those
event writes fail.
`services.admin.reconcile_safe_steps.run_all_safe_steps()` now appends a
best-effort `manual_reconcile` event with read-only reconciliation step
outcomes.
`scripts/reconcile_positions.py` now appends a best-effort
`manual_reconcile` / `position_drift_flag` event after writing
`risk_sink_failed.flag`; audit-write failure is surfaced to stderr but does not
block the safety flag. Deeper one-off reconcile scripts and future mutating
override paths remain unclassified.
`scripts/check_operator_arm_to_halt_replay.py` replays a live arm/resume event
followed by a halt/disable event from the journal and writes launch-packet
evidence. Current honest verdict is still not green: real host-side
arm-to-halt replay and no-secret scans remain unrun, and other material action
families remain unhooked under the backlog item.

## Actions That Must Be Auditable

Before capped live, these actions need actor, timestamp, action, target,
pre-state, post-state, result, and reason fields where applicable:

- live arm, live disable, halt, resume, and kill-switch changes;
- strategy stage promotion/demotion;
- strategy or campaign manifest change;
- risk-limit change;
- API credential rotation;
- order intent creation, claim, submit, cancel, fill, reject, and reconcile;
- manual reconciliation override;
- backup, restore, migration, and rollback;
- alert suppression or routing change;
- dashboard login, logout, MFA change, and role change;
- AI copilot report generation when external providers are enabled.

Current partial hook for alert routing: dashboard Settings notification changes
write a required `alert_routing_change` event after local config save and
before API sync. If that audit write fails, the local notification-settings
save is rolled back and the API sync is skipped. CLI/runtime config edits and
dispatcher or environment channel changes remain unclassified.

Current partial hook for risk limits: dashboard Settings paper-trading
risk-limit changes write a required `risk_limit_change` event after local
config save and before API sync. If that audit write fails, the local
risk-limit save is rolled back and API sync is skipped. Direct CLI/runtime
config edits, environment live-risk caps, and non-dashboard risk changes remain
unclassified.

Current partial hook for runtime `user.yaml` saves:
`services.admin.config_editor.save_user_yaml()` appends required metadata-only
`runtime_config_save` events after successful non-dry-run writes. If the audit
write fails, the helper restores the previous config file bytes (or removes the
new file for first-write attempts) and returns
`operator_event_write_failed_runtime_config_rolled_back`. Events record file
existence, parse status, top-level section names/count, and result only; config
payloads and values are not logged. Direct file edits, environment overrides,
and campaign manifest files remain unclassified.

Current partial hook for order-intent lifecycle: `storage.live_intent_queue_sqlite`
maintains current intent rows and an append-only `live_trade_intent_events`
table for intent insert, queue claim, and successful status transitions after
the live queue schema is initialized. The coverage matrix separately reports
whether that table is present in the current runtime store, so an old/unmigrated
SQLite file does not get credited with runtime history it does not yet contain.
Events record intent ID, timestamp, actor, action, pre/post status, reason,
source, last error, and order identifiers. Fills remain stored separately, and
venue-reconciliation event unification beyond the queue store remains open.

Current partial hook for backup/restore: `scripts/backup_state.py` appends
best-effort unified operator events for backup and verify command results. CLI
restore requires a pre-mutation `state_restore` operator event after backup
verification and lock/force guards pass; if that required audit write fails,
restore refuses before moving or copying state. Restore still records completion
best-effort after the data directory is restored, and reports the moved-aside
path for the pre-restore event when the old data directory is renamed.
Migrations and rollbacks beyond git/work-log evidence remain unclassified.

Current partial hook for API credential rotation:
`services.security.credential_store.set_exchange_credentials()` and
`delete_exchange_credentials()` append required metadata-only
`api_credential_rotation` events after central keyring mutations. If the audit
write fails, the helper restores the previous keyring entry or removes a newly
created entry and returns
`operator_event_write_failed_api_credential_rotation_rolled_back`. Events
record exchange, operation, result, and stored field names only; API keys, API
secrets, and passphrases are not logged. Direct keyring edits,
environment-based credential changes, and server injection/rotation drills
remain unclassified.

Current partial hook for AI copilot external providers:
`services.ai_copilot.providers.call_llm` appends best-effort
`ai_copilot_external_provider_call` events for provider attempts. These events
record provider/model, prompt character counts, result, and error metadata; they
do not log system prompts, user prompts, incident context, or report content.
Central AI copilot report writers append best-effort metadata-only
`ai_copilot_report_write` events for persisted report artifacts. These events
record report type, status/severity, and artifact names/count only; report
payloads and artifact contents are not logged. Provider-governance policy and
any future provider path that bypasses `call_llm` or the central report writers
remain unclassified.

Current partial hook for strategy config changes: dashboard Operations strategy
parameter saves and preset applies append required `strategy_config_change`
events after the local `user.yaml` save. If the event write fails, the page
attempts to roll back to the prior config and reports the failure. Direct
manifest file edits, CLI/runtime config edits, and campaign manifest changes
remain unclassified.

Current partial hook for dashboard authentication: `dashboard.auth_gate`
appends best-effort `dashboard_login`, `dashboard_logout`,
`dashboard_mfa_change`, and `dashboard_mfa_challenge` events for session and
MFA transitions. `services.security.user_auth_store` requires metadata-only
`dashboard_user_auth_store_change` events for central user upsert/bootstrap,
MFA enrollment/confirmation/disablement, and backup-code consumption; if that
audit write fails, it restores the raw keyring user/index records and returns a
rolled-back failure. Login-hash upgrades roll back the unaudited rehash while
allowing the already-verified login to proceed. These events record usernames,
roles, sources, result, and state metadata only; they do not log passwords,
hashes, MFA codes, TOTP secrets, OTP URIs, or backup code values. Future
user/role management surfaces that bypass `user_auth_store` and dashboard
session event fail-closed policy remain unclassified.

Current partial hook for strategy stage transitions:
`services.control.deployment_stage` appends `strategy_stage_transition` events
for central promote, demote, and safe-degraded transitions. Risk-increasing
`promote()` requires the audit write and rolls back the stage record if the
write fails. Demotion and safe-degraded safety transitions remain best-effort
so audit storage cannot block risk-reducing moves. Host-side promotion proof
remains open.

## Evidence Requirements

The launch packet must include:

- event-store location and retention policy;
- coverage matrix for dashboard, CLI, system, and automation paths;
- at least one replay of a live-arm-to-halt drill from audit records only (use
  `scripts/check_operator_arm_to_halt_replay.py --evidence-dest ...`);
- proof that audit records do not contain secrets (use
  `scripts/check_operator_event_secrets.py --require-events --evidence-dest ...`
  against the launch-packet journal);
- failure behavior when audit writes fail on critical live actions.

## Policy

If a live-affecting action cannot be audited, it must either:

- be blocked before capped live;
- be moved behind a separately logged path; or
- receive an explicit accepted-risk decision with expiry.
