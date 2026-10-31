# Pre-Start Cutover Continuation

## Objective and Scope

2026-10-22 20:29EDT / 2026-10-23T00:29:32Z. ENGINEER, HIGH risk.
Operator requested the next offline continuation repair. Runtime INCOMPLETE;
no new execution, token, service, scheduler, account or trading permission.

SHOWN prior defect: preparation identity and execution reservation were the same
plan.attempt, so the correctly preserved failed reservation prevented another
separately authorized run using the same four stopped replacement IDs. The
accepted optional-Healthcheck repair and prior policy supplements remain intact.

## Implementation

Existing companion_cutover.py gains an optional paired input:
`--continuation-review PATH --reviewed-continuation-review-sha256 SHA256`.
Without both, existing behavior is unchanged or mixed options refuse. No
arbitrary execution-ID override, retry loop, automatic resumption or cleanup
of the old marker is supplied.

New companion_cutover_continuation.py validates a hash-bound accepted review
record with these exact fields:

- schema: companion-prestart-continuation-v1
- decision: ACCEPTED or ACCEPTED_WITH_RISK; nonempty independent reviewer
- execution_id: 16-32 lowercase letters/digits, distinct from plan.attempt
- manifest_sha256, preparation_evidence_sha256, preparation_review_sha256,
  runtime_review_sha256: the currently loaded unchanged preparation/runtime inputs
- prepared_ids: the exact four reviewed replacement IDs in their existing order
- prior_receipt_sha256: the prior preparation-keyed failed cutover receipt
- consumer_sha256: exact map of ten host consumers named by CONSUMERS

The prior receipt is read relative to a no-follow root/ancestor directory chain,
with fixed filename receipt.jsonl, regular owner-only0600 file, same user,
64KiB limit, no duplicate JSON keys. The exact hash and these four records are
required: original inputs bound, installation reserved, staged_checks intended,
staged_preflight failed. Their input hashes and reservation contract must match
the current plan. Canonical comparison distinguishes JSON booleans from numbers.
Other stages, additional/truncated evidence, malformed records and altered
bindings refuse. Recorded pre-start failure is not proof of current native state.

Default mode validates only. Execution rechecks the same reviewed continuation
under the existing global nonblocking installation lock, before exclusive new
execution-ID reservation or token consumption. A failed/partial reservation
stays consumed. New initial receipt binds execution ID, preparation identity,
continuation review and prior receipt hash. Original preparation identity,
container labels/names, four IDs, evidence, source/runtime policies and old
marker remain unchanged. Existing fresh full preflight,600s budget/180s recovery
reserve, owned rollback, single query and success-only running rules are reused.

## Verification

VERIFIED_ENV: Python3.12.10; synthetic native/runtime state, local temporary
fixture receipts only. No Docker/network calls, credentials or real service
operation. Test fixture source maps/review decisions are explicitly synthetic,
not independently accepted operational records.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_cutover_continuation.py tests/test_companion_cutover_entrypoint.py tests/test_companion_cutover_inputs.py tests/test_companion_staged_update.py
```

142passed2.46s. Covers unchanged ordinary path, separate receipt/same prepared
IDs, no duplicate execution, wrong/mixed inputs, wrong hashes/IDs, source drift,
duplicate/extra record fields, path traversal, same preparation/execution ID,
altered/started/truncated prior evidence, numeric-boolean ambiguity, under-lock
review/receipt changes, symlinks/private modes, busy shared lock, fresh fixture
state drift, partial reservation fsync failure and owned rollback.

An initial test intended to mutate original metadata used its already-existing
value and therefore did not mutate anything. Corrected the fixture mutation to
a distinct value; no production change was made for that test error. Initial
run1failed95passed is superseded, not represented as a product defect.

Source freeze for separate review:

| Artifact | SHA256 |
| --- | --- |
| scripts/research/companion_cutover.py | 8740d65d31eade3d94cd849710aa2b1cf00a67ca560e385fd5a54ff4a20aaf4e |
| scripts/research/companion_cutover_continuation.py | 89695031669454307f55601f44953fa5fc42ef3b582ea2df5a4086470260a911 |
| tests/test_companion_cutover_continuation.py | 86aedf49108d63c5a441804b16b1e3ca6222c5d3decf2c88d557faf253ae9ee4 |

## Remaining Boundary

Implementation READY_FOR_INDEPENDENT_REVIEW. No actual continuation review
record or refreshed executable token handoff has been issued by this thread.
Old launcher/policy bindings are preserved and do not automatically accept new
host code. After independent review, actual exact-input continuation/handoff
bindings must be reviewed before a separately authorized operational attempt.
No current native state, real repaired Go-template result, health, connectivity,
source-byte, retrieval, citation or profitability claim follows from these tests.
