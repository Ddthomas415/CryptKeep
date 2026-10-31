# Running update: offline integration candidate

Date: October20,2026. Active role ENGINEER. Risk HIGH.
Offline component: ACCEPTED_WITH_RISK by separate GATE. Native assembly: INCOMPLETE.
No runtime operations or credentials were used to implement/test this candidate.

## Implemented in the existing installer

An optional runtime adapter plus explicit startup authorization runs under the
existing installer deadline:600seconds total,420seconds work,180seconds recovery.
No second controller or concatenated timeout budgets. Work-phase receipt writes
also respect the work deadline. The old stopped profiles remain installation-only.
The v4 CLI apply refusal remains in force; this is not a deployment command.

The candidate compares installer snapshots with runtime inventory, requires all
existing compatibility and storage-namespace checks, starts only the four
replacement applications in dependency order, checks health, spends one guarded
explanation-request budget, records sanitized diagnostics before acceptance, and
uses the existing explanation/evidence gates. The normal dashboard probe/client,
normalizer and asset guard are not replaced. Raw payloads stay in memory.

Failures share the remaining recovery deadline. Cleanup may quiesce/remove only
acknowledged, unchanged, attempt-owned replacements, then use the existing
original-application rollback. Uncertain starts/stops remain unresolved. A pending
start can be resolved by acknowledged removal and confirmed absence of the exact
attempt-owned never-started container; desired observed state alone is not proof
of lifecycle ownership. No storage start/stop/removal is part of the candidate.

## Material native assembly gap, not an authorization formality

The existing PinnedRuntimeAdapter binds exact replacement container IDs. Those
IDs do not exist until creation. A synthetic adapter can match the candidate's
new objects, but a static native adapter prepared before installation generally
cannot. This must not be hidden behind passing unit tests or fixed by generating
trusted policy approvals from observed inventory.

The operator has been asked to choose between:

- Prepare stopped replacements and independently review identities/bindings
  before a separately bounded cutover (recommended; changes the earlier global
  preparation/review/cutover budget and requires an explicit contract amendment).
- Retain preparation, independent binding review, cutover and recovery inside the
  single600second deadline (requires a feasible bounded review/handoff mechanism,
  not an assumed adapter or a reset deadline).

Subsequent operator decision: prepare stopped replacements, independently review
their actual IDs, then use a separately bounded cutover. The implementation and
remaining operational limits are recorded in
`companion_staged_update_20261020.md`. This closes the architecture-choice
question, not native verification or operational authorization. Neither choice
authorizes creation, interruption, credentials or trading.

## Evidence and limits

First synthetic integration/storage slice:71passed0.71s. Expanded parent slice
including existing installer/diagnostics plus the real dashboard probe with fake
HTTP:201passed1.37s. Neither is a full suite or real endpoint result. Native
cleanup helpers and final combined verification/review are pending at this entry.

The first parent review REJECTED two recovery-reporting defects despite passing
tests: renamed resources could be missed by selected inventory, and cleanup
pending was cleared before removal confirmation. Both were corrected with
explicit known-ID reconciliation against complete runtime inventory, all
uncertainty sets checked before recovery acceptance, and pending retained until
removal and absence are confirmed. Original review:
`../review_artifacts/companion_continuation_20261020/running_update_review_r1.json`.

Corrected combined slice:502passed3.14s, exit0, nine focused files including
existing native adapter/controller regressions. Exact command and four frozen
hashes are in `running_update_verification.json` in the same review folder.
The interim205pass/1fail result is retained there: a persistently corrupt observer
can no longer support verified recovery; tests now distinguish transient and
persistent mismatches rather than weakening the stricter recovery gate.

Native cleanup helpers use exact acknowledged public snapshots, SIGTERM only,
no forced removal and no ownership inference after failed acknowledgments. A
v4-only stopped-placeholder allowance enables metadata observation, not lifecycle
authorization; old profile semantics remain unchanged. This is fake-command and
state-machine proof. Neither staged trust nor native assembly is established.

Separate GATE re-review accepted the frozen offline component WITH_RISK, closed
both bounded code findings, independently reproduced502passed2.96s and matched
all four source/test hashes. Receipt: `running_update_review_r2.json` in the same
review folder. No further review is needed for this component unless evidence or
code changes. This does not resolve the native binding-ID assembly decision,
renew a consumed attempt, or authorize an operation. The v4 CLI refusal remains.

Preserve all earlier component receipts, rejection/correction history, source
manifests, registered experiments and the25-symbol mandate. Current installed
source, engine/builder compatibility, namespaces and cited explanations are not
certified by this candidate. No profitability or trading-readiness claim follows.
