# Fixed Offline V6i Handoff

Role: GATE closeout of separate review. Risk: HIGH. ACCEPTED_WITH_RISK
for the exact offline handoff only.
Runtime INCOMPLETE. No execution, credential or startup authorization.

## Delivered Scope and Exact Delta

Continue the accepted restoration objective using the reviewed V6i runtime
packet and four prepared actual IDs. New execute_reviewed_v6i.py reuses the
reviewed V6h handoff, changing labels/attempt/date and four fixed receipt/review/
scope/runtime hashes. One demonstrated compatibility repair additionally binds
the V6i scope's inline exact_subjects list to its hash-pinned subjects.draft.json.
No accepted packet, policy record, controller, transport, private pipe helper,
token parsing, credential source, recipient or runtime execution logic changed.

The initial test run exposed the format mismatch: 16 passed/16 failed because
the old launcher indexed exact_subjects as a path/hash object, while the accepted
V6i scope uses a list and binds its subject file through input_sha256. New handoff
reads that fixed packet-local file using the accepted scope's hash and requires
its full list to equal both inline scope and V2 runtime subjects. Wrong/missing
pin, contradictory inline data or legacy shape refuses. The accepted record is
preserved rather than edited to fit an old consumer. Exact whole-source-delta
regression documents this change; no permissive dual-schema fallback.

New validate_cutover_default.py/verify_handoff_default.py reuse the existing
proofs with only packet/attempt/module labels and the explicit subject-file
allowlist path updated. The fixed original private-pipe helper remains hash-bound
at 5c319350681e2fb4fdac363e29b829947e0348678fdcc8ecabc84820713adf12;
its functions load under a non-main name and its old CLI is never invoked.

## Default and Future Execution Boundary

Default validates the existing accepted inputs and prints an inert response.
It verifies review/output/scope links, all 20 current host consumers, seven
subjects/132 source pins, configuration/network contract, actual plan/attempt
and receipt bindings. Execution flags and token arguments in recorded argv
are refused. The new memory image and accepted archival-only repair remain bound
to the independently reviewed source/configuration profile and fresh gates.

A future separately approved --execute-once would disable core dumps, validate
inputs, refuse a consumed cutover marker, verify the pinned CLI and privately
read the existing token from the exact original orchestrator. Existing anonymous
pipe hands it to the existing controller. No token logging/printing/export or
persistence; clearing Python references is not secure zeroization.

Controller budget is 600 seconds including 180 recovery. Separate CLI/token-source
checks have their existing ten-second bounds before that controller budget;
there is no whole-wrapper 600-second guarantee. Marker precheck is advisory;
controller reservation remains authoritative. No automatic retry/reset.

If later authorized, the attempt gracefully stops four originals, starts four
reviewed replacements, and runs the required checks plus one frozen cited query.
Three storage services/volumes, trading, risk settings and schedules remain
untouched. Only all-checks success permits leaving replacements running. Failure
attempts owned cleanup/original restoration, not guaranteed; logs/audit effects
may persist. No such token read, startup, query, service or core-limit operation
occurred in this offline work.

## Verification

VERIFIED_ENV local source binding, synthetic tests and actual inert default:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6i_handoff.py
```

SHOWN: 36 passed in 0.37 seconds, no warnings. Retains the hash-bound historical
synthetic suite, exact launcher delta, current guard/consumer/output/receipt drift,
consumed marker/broken symlink, synthetic one-read/private-pipe behavior, malformed
fake token and sanitized failure/no-retry cases; adds four subject-shape/hash
binding negatives. Test tokens are synthetic and are not actual credentials.

Actual cutover entrypoint default first exited zero under tripwires, with 13
allowlisted read-only loader opens; saved runtime_packet_v6i/inert_validation_receipt.json,
SHA256 ba02957d5dd0ef5ef5435c0dcb253ce1a3f240676a8eb0d22fa9c3ddb6cfb795.
Actual handoff module default via runpy then exited zero, response exactly equal
to that receipt, empty stderr,26 read-only loader os.open calls, zero operation
tripwire calls and absent cutover marker before/after. Exact file allowlists and
backend/native/socket/subprocess/token/reservation/lock/pipe/temp-config/core-limit
tripwires were active. Count covers explicit os.open loader calls, not every
interpreter/Path read; initial proof receipt/scope reads are local preflight.
handoff_default_proof.json binds actual source/receipt/proof script.

No full suite, SDK initialization, real token/CLI/network/DB/application call,
container state change, capture repeat or trading operation. Preparation remains
consumed; cutover unused at this advisory observation. No material assumptions.

## Review Handoff

Review exact launcher/schema adaptation and inert proofs, not old SDK semantics
or a new runtime experiment. Handoff is frozen for separate GATE review. Passing
default/tests do not establish runtime health, original-state continuity, query
success or profitability. Fresh identity/configuration/source/callable/namespace/
fixed-recipient/storage-lineage/archive/body/witness/citation gates stay mandatory.
After acceptance, the next step is explicit operator authorization for ONE
bounded actual attempt, not implicit execution of this handoff.

## Independent Acceptance and Operator Boundary

Separate GATE accepted the exact launcher/subject adaptation/proof sources with
risk, no blockers. Review: handoff_independent_review.json, SHA256
197dc454d31944faeff1312e25d616a3dad2833ef2f9bb440577f032116636ea.
It independently ran 36 tests once (0.31 seconds, no warnings), reproduced the
actual guarded module-default proof once exactly (exit zero, matching response,
empty stderr,26 read-only opens/zero tripwires/marker absent), and verified the
whole-source and proof-source deltas. Its later static label-normalization check
initially missed the module-directory date, then passed after comparison-only
correction; actual default was not rerun and reviewed source was not changed.

Parent rehashed 50 unique current files before this documentation-only closeout.
The review has 70 references because its 20-consumer table repeats those already
in reviewed_inputs; duplicate hashes agree. No mismatch. The checkpoint digest
now denotes pre-closeout text; source/tests/proofs/reports/review/accepted policy
records remain unchanged. Neither review nor these default proofs accessed real
credentials, native services or application endpoints.

Offline handoff objective complete. Next is explicit operator authorization for
ONE bounded native V6i attempt. Exact reviewed command, NOT authorized here:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6i_20261027.execute_reviewed_v6i --execute-once
```

Authorization must cover private reuse of the existing internal service token,
four-original-app graceful stop/four-prepared-app start, required checks and one
frozen cited query, with all success/failure/budget/side-effect boundaries above.
No token read, execution, retry/reset or service change occurred in this work.
Runtime remains INCOMPLETE; preparation consumed and cutover not invoked.
