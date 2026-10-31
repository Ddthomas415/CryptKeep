# Existing research applications: update and rollback proposal

Date: October20,2026. Active role: DIRECTOR. Risk: HIGH (deployment,
credentials, cancellation and rollback). Plan: READY_FOR_INDEPENDENT_REVIEW.
Runtime: INCOMPLETE. This document is not an executable manifest or permission
to stop, build, create, start or query anything.

## Objective and chosen path

Restore the reviewed explanation path by updating only the four existing research
applications. Keep PostgreSQL/TimescaleDB, Qdrant and MinIO running, with their
original identities, images, mounts, volumes and network memberships preserved.
Reuse the existing installer, native adapter, diagnostics, bounded executor and
dashboard probe. Do not add a second deployment framework, new database, model,
collector or strategy. No research experiment or trading change is included.

This requires a narrowly scoped opt-in extension: the existing installer accepts
only seven exited containers, and its runtime controller owns startup of all
seven. Neither can be used unchanged on the observed running stack. Preserve
the old schemas and their fail-closed behavior; never weaken a stopped-baseline
assertion globally or change saved observations to pretend containers stopped.

## SHOWN evidence and limits

- October20 12:10 EDT: actual orchestrator/memory health endpoints return200;
  orchestrator reports no trading and no model, memory reports connectivity to
  PostgreSQL, Qdrant and MinIO. These are not persisted-citation checks.
- Two live public source hashes exactly match saved legacy versions, not the
  reviewed sources. The legacy explanation route lacks the reviewed strict
  single-query branch. Whole-image and SDK compatibility remain UNVERIFIED.
- An offline check loaded the old manifest and verified all43 source entries
  against current files: audit9, risk9, memory11, orchestrator14; zero mismatches.
  The application sources do not need another speculative rewrite.
- Old manifest SHA256:
  `f5b044858c3d40881239b77745d0b404c4ac05d2f35a6d043fed8f6ba934bf5f`.
  It pins the old CLI and seven exited states. Its consumed attempt cannot be
  reused. The installation backend separately pins engine29.8.2/8af9fe3;
  current engine compatibility is UNVERIFIED, not inferred from CLI29.9.1.
- The prior metadata failure's exact field remains UNVERIFIED. The accepted
  field-level diagnostic is reusable; fingerprint checks must not be bypassed.
- Startup owner is UNVERIFIED. An explicit operator maintenance decision, rather
  than an ownership inference, must authorize interruption of these applications.

Evidence: `companion_continuation_20261020.md`, its running_path_diagnostic.json,
`companion_metadata_diagnostics_20261018.md`, and the existing source files
`companion_installer.py`, `companion_install_docker.py`,
`companion_existing_controller.py`, `companion_runtime_adapter.py`.

## Required implementation, before operational approval

Extend the existing path, not the reviewed application sources:

1. Add an explicit opt-in running-storage contract. Three storage targets may
   remain running; four application targets require an identity-bound quiesce
   and rollback record. Bind new attempt ID, CLI, engine/builder evidence,
   image/source identities and current metadata; refuse drift or unknown fields.
2. Prepare and verify all four replacement images before interruption, using
   local parents only, network disabled, no pull, and the43 pinned source entries.
   Prove builder compatibility first; do not merely update the engine literal.
   Existing stopped install mixes preparation/cutover; refactor only enough to
   expose that separation without changing old-profile behavior.
3. Preserve original application containers for rollback. Capture their complete
   reviewed recreation contract before cutover, but do not export secrets to
   receipts. Reuse credential/label handling in bounded private memory only,
   under separately authorized credential use. Core dumps disabled; no secret
   arguments, environment dumps, plaintext files, hashes or arbitrary logs.
4. Validate replacement configuration, sources, namespaces and installed SDK
   restrictions before startup. Required read-only-startup must refuse missing
   namespaces rather than create them. No ingestion, migration, new documents,
   paid model or external market request. Preserve NO_TRADING and empty model key.
5. Update the existing runtime path to start only the four owned replacements;
   storage targets are checks, never start/stop targets. Recheck exact target
   identity/state before each mutation. A local lock is not proof that other
   Docker clients cannot interfere; observed drift requires refusal.
6. Enforce one operation with a600second overall budget, reserving180seconds
   for rollback; finite per-operation timeouts and no automatic retries. These
   are required implementation/test conditions, not claims about today's runner.
   The deadline may not discard uncertain lifecycle outcomes: reconcile exact
   IDs and ownership before cleanup. If rollback cannot finish safely in budget,
   report INCOMPLETE and preserve recoverable artifacts; do not remove unknown
   containers, retry indefinitely or claim rollback succeeded.

The field-level diagnostic must run before cleanup on any metadata rejection.
Retain the strict gate even if that makes the attempt fail. No special-case
acceptance of flag ordering or network metadata without demonstrated evidence.

## Proposed operational sequence after separate approval

No mutating command is supplied now: the existing executable refuses this
baseline. An executable command/hash/attempt packet must follow reviewed offline
implementation; `--apply-install` against the old manifest is expressly excluded.

1. Fresh selected inventory and namespace checks, exact identity/source/CLI and
   engine validation, exclusive receipt and current-state recheck. No drift from
   the newly reviewed baseline; no takeover of unrelated work.
2. Prepare all replacements and verify sources without stopping applications.
3. Quiesce only the four specifically approved original applications in reverse
   dependency order. Do not escalate a failed graceful stop to an unapproved
   forced kill. Keep storage services running and original containers recoverable.
4. Install the four owned replacements with loopback-only published ports,
   existing network identities, approved aliases, restart policy no, unchanged
   persisted storage and the separately reviewed environment contract.
5. Start audit/risk, then memory, then orchestrator. Verify health, namespace
   presence, no model/trading, zero-retry SDK policy and recipient restrictions
   separately. Health alone is insufficient.
6. Submit exactly one request through existing `dashboard_probe` and normal
   transport/normalizer/asset guard, with primary route suppressed only by the
   reviewed probe context. Existing service token in private memory only.
   No fallback to ordinary legacy requests if the probe is unavailable.
7. Verify positive persisted document identity, content hash and article-view
   mapping via existing bounded read-only evidence checks. Report transport,
   retrieval, identity, topical relevance and causal limitations separately.
   Successful retrieval is not proof of causation or trading profitability.

Success: leave only the four accepted replacements running with the unchanged
storage services; preserve stopped originals and rollback receipt. Do not delete
originals/images or prune. If any required check fails, perform the bounded
rollback below, with no automatic second query or installation attempt.

## Rollback, writes and recovery limits

- Stop/remove only replacement IDs demonstrably created by this new attempt.
  Preserve original IDs; restore their original names and network aliases, then
  restart only the original applications that this attempt demonstrably stopped.
  Verify service readiness and selected configuration; exact old StartedAt values
  cannot be restored. Do not claim byte-identical runtime restoration.
- Never stop/recreate storage or remove volumes, networks, unrelated containers
  or database rows. If original identity/configuration cannot be established,
  stop further mutation and report the precise incomplete recovery stage.
- Startup/health requests create normal logs; builds/containers use local disk;
  explanation and audit requests may append audit records. Application rollback
  does not undo those writes. No live Docker.raw copy is called a backup.
- Restoring old application code does not establish or restore old persistent
  data contents. No schema/data mutation is permitted by this proposal.

## Proof and stopping point

Required targeted synthetic coverage: old schemas still reject running baselines;
new contract accepts running storage without lifecycle calls; all preparation
failures precede quiesce; stale identities/unknown owners refuse; failed/uncertain
stop/create/start paths reconcile ownership; metadata failure retains diagnostics;
secret canaries absent from receipts; missing namespaces refuse startup; deadline
includes recovery; rollback never touches storage and restores only owned
interruption; dashboard submits at most once and citation verification remains
separate from relevance. Run focused tests while implementing, one final combined
slice, and independent review on the frozen delta. No broad backtests.

At most two material assumptions, neither accepted as operational evidence:

- The operator wishes to retain this local stack as the restoration target.
  If false: no cutover; identify the actual target first.
- No other actor needs these four applications uninterrupted during a later
  approved maintenance window. If false or ownership drifts: defer cutover.

Plan review can accept the design only. Runtime and executable readiness remain
INCOMPLETE until implementation, independent proof and separate operational
authorization exist. No app/source changes or runtime operations were performed
to prepare this proposal.
