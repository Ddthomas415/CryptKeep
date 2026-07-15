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
events with required fields and secret-key redaction. Current honest verdict
is still not green: the journal substrate exists, but material action families
must be hooked to it before they count as SHOWN. The arm-to-halt replay drill,
no-secret payload scan over real launch-packet events, and audit-write
fail-closed behavior for critical live actions remain open under the backlog
item.

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

## Evidence Requirements

The launch packet must include:

- event-store location and retention policy;
- coverage matrix for dashboard, CLI, system, and automation paths;
- at least one replay of a live-arm-to-halt drill from audit records only;
- proof that audit records do not contain secrets;
- failure behavior when audit writes fail on critical live actions.

## Policy

If a live-affecting action cannot be audited, it must either:

- be blocked before capped live;
- be moved behind a separately logged path; or
- receive an explicit accepted-risk decision with expiry.
