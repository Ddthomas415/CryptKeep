# Research service incident log: October 25, 2026

Role: AUDITOR. Documentation risk: LOW. Record state: ACCEPTED.
Research runtime state: INCOMPLETE.

Scope: the four known incidents in this chat's research-service reconnection
sequence, not an exhaustive account of all repository, laptop or other-agent
activity today. Date uses America/New_York. Exact failure times were not retained
in the reviewed event receipts and are not reconstructed from file timestamps.
No new service, health, account, credential or trading inspection was performed
to prepare this log.

## INC-20261025-01: cited-query acceptance failed

**State:** INCOMPLETE.

**SHOWN in saved evidence:** the single authorized V6e attempt reached query
verification and failed. Its 97-event receipt records companion HTTP 200 and
accepted client normalization, then a verify_evidence invocation and failure
at runtime_verification. Execution was disabled in the response diagnostics.
Transport/client success did not establish a valid cited explanation.

**Impact:** four prepared research applications were started for the attempt;
the failed attempt triggered their removal and restoration/restart of the four
original applications. The controller reports configuration rollback verified,
exact baseline restoration false and no unresolved tracked recovery actions.
That is not proof of endpoint health, connectivity, persistent data integrity
or exact restoration. The later paired capture supports original identity and
configuration continuity, not a successful explanation. Preparation and cutover
reservations remain consumed; removed replacement IDs must not be reused.

**Cause boundary:** three citation-ID hashes do not match the frozen archive's
55 IDs. Static code also shows live rows can enter retrieval while the verifier
requires archived IDs. This incompatibility is SHOWN. Its status as the unique
or first remote failure remains UNVERIFIED: the receipt saved neither the raw
response nor the five verifier Boolean results. Timeout/transport/other predicate
failures cannot be excluded. The earlier recoverable primary-route envelope
error is not sufficient to explain the final failure.

**Corrective work completed offline:** the archival probe now selects frozen
document candidates before the five SQL queries' ranking/limits. Ordinary live
retrieval is preserved. Fixed-key verifier-result/shape/exception diagnostics
are recorded before acceptance or recovery without raw payloads or exception
text. Archive, witness approvals and evidence predicates are unchanged.
Parent focused run: 285 passed. Independent repair-review run: 124 passed.
These are synthetic/offline results, not installed runtime proof.

**Remaining limits:** Qdrant limits candidates before frozen SQL hydration and
may underfill vector results. Grouped exception diagnostics still cannot identify
a remote first predicate. The repair is independently ACCEPTED_WITH_RISK for
offline scope only; it has not been demonstrated in a successful service query.

**Evidence:**

- [Public event receipt](../review_artifacts/companion_reconnection_plan_20261024/actual_runtime_v6e/receipt.jsonl).
- [Outcome attribution](../review_artifacts/companion_reconnection_plan_20261024/actual_runtime_v6e/outcome.json):
  parent transcription of session 10100's exit-1 result, not independently
  captured process output.
- [Independent result review](../review_artifacts/companion_reconnection_plan_20261024/actual_runtime_v6e/independent_review.json).
- [Repair and test record](../checkpoints/companion_archive_scope_repair_20261025.md).

## INC-20261025-02: my metadata-capture wrapper rejected valid schema

**State:** ACCEPTED_WITH_RISK for the corrected saved inputs only.

**SHOWN:** my wrapper incorrectly required an empty attempt field, but the
existing metadata formatter does not emit that field. The wrapper failed after
the first read, before saving a usable paired baseline. This was my validation
mistake, not a confirmed Docker or service defect. The initial native-read count
and lack of retained raw observation are parent-attributed in the saved failure
record; independent review did not re-observe that acquisition.

**Impact:** lost capture evidence and an avoidable additional approval/capture
cycle. No service mutation or exported credential value is reported for that
read-only command. Exact delay, token consumption and financial cost attributable
to this mistake were not measured and are UNVERIFIED.

**Correction:** after fresh explicit approval, the corrected wrapper performed
two read-only inspections and saved both sanitized responses before validation.
Their bytes are identical; both contain seven original-container observations.
Capture time was 12:06:23 UTC, or 08:06:23 America/New_York, from the saved
observation's UTC fields. The reported capture elapsed time is 0.083 seconds.
These acquisition timings are parent provenance, not independently observed
native events. The failed capture record remains preserved.

**Verification:** the derivation accepts legitimate rows without an attempt
field; 13 synthetic tests passed, including an independent 13-case run. Actual
saved inputs were separately reviewed: only four original application start
timestamps and the three accepted source bindings changed. The actual default
preparation entrypoint exited 0 under native/token/backend/reservation tripwires,
with actions false and startup false. No new image/container or reservation was
created by that check. Fresh inputs are ACCEPTED_WITH_RISK, not runtime ready.

**Recurrence control actually used:** retain sanitized raw captures before local
validation; validate the formatter's real schema rather than an assumed field;
preserve failed records and distinguish synthetic tests from actual acquisition.
These checks reduced the demonstrated failure mode. They are not a guarantee
that all future capture wrappers or agent actions enforce the same behavior.

**Evidence:**

- [Initial failure record](../review_artifacts/companion_integration_inputs_v6f_20261025/initial_capture_failure.json).
- [Corrected paired observation](../review_artifacts/companion_integration_inputs_v6f_20261025/baseline_observation.json).
- [Actual-input independent review](../review_artifacts/companion_integration_inputs_v6f_20261025/actual_input_review.json).
- [Inert validation receipt](../review_artifacts/companion_integration_inputs_v6f_20261025/inert_validation_receipt.json).

## INC-20261025-03: local postcheck used the wrong manifest interface

**State:** ACCEPTED_WITH_RISK for the saved postcheck evidence only.

Following separately approved stopped preparation, two read-only metadata
responses for the seven originals and four new containers were saved before
local validation. My wrapper then incorrectly looked for a network_bindings
key in the raw manifest instead of using the existing Plan.network_bindings
property. It exited with KeyError. This was another local schema-assumption
mistake; it did not establish a service or preparation failure.

**Impact and correction:** the raw responses were preserved, so offline
normalization through the existing Plan loader completed without another native
call, repeat capture or service action. All eleven rows match across the two
reads; reconstructed original snapshots match the reviewed baseline and four
staged snapshots match the published preparation evidence. No health or query
success follows from those comparisons. Capture clock start/end values were
lost with the wrapper process and were not reconstructed; recorded_at in the
normalized artifact means normalization time.

Independent actual-ID review subsequently reproduced the eleven snapshots and
accepted the saved evidence with its attribution limits. It did not repeat any
native read or establish service health. The four replacements remain stopped
in the reviewed snapshots; startup/cutover/query is not approved by this review.

The earlier save-before-validation correction prevented evidence loss here.
It did not prevent the repeated schema-assumption error. Future wrappers should
use the existing typed model rather than guessed raw keys; that recommendation
is not presented as an already-enforced universal control.

**Evidence:**

- [Postcheck, raw hashes and error attribution](../review_artifacts/companion_integration_inputs_v6f_20261025/actual_preparation/postcheck.json).
- [Actual preparation checkpoint](../checkpoints/companion_actual_preparation_v6f_20261025.md).
- [Independent saved-evidence review](../review_artifacts/companion_integration_inputs_v6f_20261025/actual_preparation/independent_review.json).

## INC-20261025-04: V6f cited response rejected by dashboard guard

**State:** runtime INCOMPLETE; saved evidence separately ACCEPTED_WITH_RISK.

**SHOWN:** the separately authorized single V6f attempt exited 1. Its 96-event
receipt records companion HTTP 200 with five citations/execution disabled, then
foreign_asset normalization rejection and dashboard_fallback selection. No
evidence_verification_checks event exists. This is not a demonstrated second
failure inside verify_evidence. The initial interim "failed evidence acceptance
again" wording is clarified accordingly.

**Impact:** four prepared apps were started; failure triggered replacement
cleanup and original-app restoration. Controller reports configuration rollback
verified, exact baseline false, no unresolved tracked recovery actions and
preparation consumed. Connectivity and post-recovery health remain unverified.
Removed replacement IDs and consumed reservations must not be reused.

**SHOWN offline:** all five document ID/URL hash pairs match frozen archive
records, unlike V6e. The saved citation names correlate to keyword_5, keyword_47,
keyword_18, past_1(document 5) and future_1(document 26). The guard permits the
mixed BTC/ETH document-5 title in its labelled current_cause passage but rejects
the identical title in past_precedent. Three synthetic cases reproduce this
gap without changing code or gates; both keyword-only and BTC-only-past controls
pass. The title-as-precedent is a plausible runtime mechanism, not a proven
unique cause: the actual prose and typed fields were not retained.

**Correction boundary:** preserve this failure and pursue one offline
citation-context contract repair with negative controls. No new live attempt,
reset, preparation or source/gate change was performed during diagnosis. No full
suite or health checks were run. Independent GATE read all 96 events, reproduced
the diagnostic exactly and found no blocking overclaim. Parent verified its 17
source/evidence bindings; this accepts the saved record, not service restoration
or a guard repair. The unique runtime trigger remains UNVERIFIED.

**Evidence:**

- [Actual attempt checkpoint](../checkpoints/companion_runtime_attempt_v6f_20261025.md).
- [Public receipt](../review_artifacts/companion_integration_inputs_v6f_20261025/actual_runtime_v6f/receipt.jsonl).
- [Parent-attributed outcome](../review_artifacts/companion_integration_inputs_v6f_20261025/actual_runtime_v6f/outcome.json).
- [Offline diagnostic and hashes](../review_artifacts/companion_integration_inputs_v6f_20261025/actual_runtime_v6f/diagnosis.json).
- [Independent saved-evidence review](../review_artifacts/companion_integration_inputs_v6f_20261025/actual_runtime_v6f/independent_review.json).

## Historical boundary before the V6f attempt

The original log did not authorize stopped preparation. The operator later
separately approved it, and the controller reported successful preparation of
four stopped replacements without starting services or interrupting originals.
This log update grants no further permission. Preparation is consumed; the next
safe scope is offline actual-ID runtime integration, not startup or query.
No approval is inferred from the ambiguous incident-log message or this record's
documentation acceptance.

## Record verification

The original eight evidence digests were checked against the hashes retained in
the existing checkpoints/reviews. All matched; the runtime receipt has 97 events,
the saved baseline pair is equal, actual inputs are ACCEPTED_WITH_RISK and the
inert result reports no actions. Markdown links checked for local existence.
No code changed and no tests or runtime checks were rerun for this documentation
task. The third incident's saved postcheck is part of the subsequent bounded
preparation verification, separately recorded and independently reviewed as saved
evidence only. No native acquisition history is independently re-observed.
This log does not provide independent proof of its author's reliability.
