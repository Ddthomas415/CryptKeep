# CryptKeep Operator Action Audit Coverage

Status: `POLICY_DOCUMENTED`

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

