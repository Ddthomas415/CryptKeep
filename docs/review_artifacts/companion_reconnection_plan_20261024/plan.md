# Minimal existing-stack update plan

Role: DIRECTOR. Risk: HIGH. READY_FOR_INDEPENDENT_REVIEW.
Design only; no new attempt, accepted manifest, service operation or query.

## Decision

Reuse the existing staged running-update path: prepare four stopped application
replacements, independently review their actual identities, then separately
authorize one bounded cutover/query. Keep the three storage services untouched.
No new application rewrite, deployment framework, collector, model or strategy.

Four applications are the already-reviewed unit of this mechanism. Two sampled
main files establish a legacy/parity gap, not four independently diagnosed code
defects. Redesigning the controller for a two-service swap would create a new
lifecycle/recovery contract and is not the smallest reuse path here.

## What can be reused

SHOWN locally: all43application source entries and13preparation-tool consumers
still match the accepted preparation inputs. Their source maps, commands,
options and policies can be reused as inputs, subject to existing preflights.
The actual observed original IDs/images/configuration satisfy the prior baseline
constraints; only four application start timestamps differ. This is saved
baseline equivalence, not current runtime approval.

Reuse `companion_prepare.py`, the staged installer/cutover, existing field-level
diagnostics and private-token handoff, and the normal dashboard transport and
guard. The corrected guard and archived-witness records7,5,47,18 retain their
independent reviews and narrow meanings. Archived topic relevance is not current
cause, market truth or live data identity.

## Required changes, in order

1. **Offline inputs.** Derive a fresh INCOMPLETE preparation candidate using the
   existing pure recipe and a transparent adapter for the new inventory schema.
   Keep original observations intact; never falsify running/exited state. Bind
   current saved baseline, unchanged13consumers/43source entries and a genuinely
   unused attempt label. Do not allocate/reset any durable reservation. Obtain
   independent input review and use the existing inert CLI before requesting an
   operation. The consumed V6d manifest/IDs remain historical only.
2. **Stopped preparation, only after separate authorization.** Existing mechanism
   may reuse matching verified cached images or build source-only from existing
   verified local parents with network disabled/no pull. Cache presence is
   UNVERIFIED; no image inventory/build has been performed for this plan. If
   required parents or identity/source checks fail, stop rather than repair the
   host or fetch unapproved images. Create four new stopped replacements without
   interrupting originals or storage; private config copy stays in memory and
   scoped container configuration, never public artifacts. No startup/query.
3. **Actual identity and runtime review.** Bind the new IDs/images/configuration,
   source/archive witnesses, intended aliases and current clients to the runtime
   packet. Carry the reviewed evidence portion into a new packet; do not activate
   it by editing the consumed packet. Reuse prior dependency/source evidence only
   where exact image/source lineage and review applicability hold. Do not repeat
   broad SDK/Docker audits without changed evidence, but do not claim local byte
   equality alone establishes installed policy. Preserve original policy meanings,
   limits and the distinction between modeled configuration and actual attachment.
4. **Separately authorized cutover/query.** Recheck identities, metadata, recipient
   exclusivity, sources and required persistent namespaces immediately before
   interruption. Use existing graceful four-app quiesce/activation/recovery.
   Storage lifecycle is forbidden. After actual attachments/health checks, submit
   exactly one frozen-question dashboard request and verify current persisted
   identity/body/citations against the reviewed evidence set. No ordinary-route
   fallback, static-dashboard acceptance, witness forcing or second query.

## Bounds and side effects

Existing preparation budget:300s including120s recovery. Existing cutover:600s
including180s recovery. Private handoff pre-controller CLI/source checks have
separate10s limits; this is not a whole-wrapper hard-wall guarantee. No automatic
retry, receipt reset or reused consumed attempt. Review time is outside operation
clocks. Before any interruption, explicit maintenance authorization is required;
running containers do not prove that no other operator needs them.

Preparation may leave cache/images/stopped-container config/logs. Cutover/query
may append audit/log records. Rollback restores only owned interruption and
configuration where provable; it cannot restore old StartedAt values or undo
audit/data writes and is not guaranteed. Never remove unknown containers,
originals, volumes, networks or historical receipts. If ownership/recovery is
uncertain, retain evidence and report INCOMPLETE.

## Success and remaining scope

Success is a real non-static cited answer through the normal client, execution
disabled, current stored identity/body lineage checked, topical/causal limits
preserved. Running containers, source parity and offline fixtures are separate
milestones, not substitutes for this acceptance. No profitability claim follows.

This plan does not create an executable operational command or grant permission
to build/create/stop/start/query. The immediate next action after design review
is offline fresh-input derivation, not another blind runtime attempt. No material
assumption of image availability, maintenance ownership, loaded code, current
namespace contents or future baseline stability is made.
