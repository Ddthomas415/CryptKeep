# Fixed Offline V6h Handoff, October 26

Implementation role: ENGINEER. Risk: HIGH.
Separate GATE outcome: ACCEPTED_WITH_RISK, exact offline handoff only.
Runtime INCOMPLETE; no operational authorization or execution.

## Objective and exact delta

Complete the existing offline handoff so the next operator decision can concern
one bounded runtime attempt, not another source-binding step. New file:
docs/review_artifacts/companion_integration_inputs_v6h_20261026/execute_reviewed_v6h.py.

The source is byte-equivalent to reviewed V6g after only V6h labels/date and
four fixed receipt/review/scope/runtime hashes are substituted. No controller,
private pipe helper, transport, credential parsing, recipient or runtime logic
changed. Exact-delta regression pins the old launcher SHA. Existing helper SHA
5c319350681e2fb4fdac363e29b829947e0348678fdcc8ecabc84820713adf12
is unchanged and loaded without executing its old CLI.

The fixed handoff checks actual published records, accepted scope links, all
twenty current host consumers, seven subjects/132 pins, model/network contract,
receipt response bindings and attempt/manifest identity. It refuses execution
flags in recorded default argv. No fake legacy receipt fields are introduced.
All real V6h actual IDs and original baseline remain bound to accepted inputs.

## Execution boundary, NOT authorized or invoked

Default path only validates and prints the existing inert response. A future
explicit --execute-once path sets core dumps off, validates fixed inputs, checks
the cutover marker, verifies CLI and reads the existing service token privately
from the exact original orchestrator. Existing anonymous pipe passes it to the
existing cutover consumer. No printing/export/persistence or new credential.
Clearing Python references is not secure zeroization.

The future controller budget is 600 seconds including 180 for recovery. Separate
ten-second CLI and token-source checks precede it; this is not a whole-wrapper
600-second guarantee. No retry/fallback, new attempt reset or receipt overwrite.
Advisory marker check precedes token access; authoritative reservation remains
in the controller. Fresh identity/config/source/SDK/storage/namespace/recipient/
health/citation/evidence gates remain mandatory and can refuse.

A future approved action would gracefully stop only four original apps, start
only four reviewed replacements and perform required checks plus one frozen
cited query. Three storage services/volumes, trading, risk and schedules remain
untouched. Only all-checks success permits leaving replacements running; failure
attempts owned cleanup/original restoration, not guaranteed. Logs/audit effects
can persist. None of those operational actions occurred in this offline work.

## Synthetic and actual default proof

VERIFIED_ENV isolated local verification:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6h_handoff.py
```

SHOWN: 32 passed in 0.32 seconds. Retained 31 regression cases passed first;
added explicit current runtime-adapter drift refusal, then all 32 passed. Test
base is the pinned historical synthetic suite; no real token is used. Covers
exact old-launcher delta, records/consumer/output/receipt contradictions,
consumed marker/broken symlink, CLI rejection, one synthetic source read/pipe
handoff, malformed fake credentials and sanitized exceptions without retry.

Actual module default via runpy also exited zero. verify_handoff_default.py is
the existing verifier with only module/packet/attempt labels changed. Under exact
file allowlists and backend/native/socket/subprocess/token/reservation/lock/pipe/
temporary-config/core-limit tripwires: response matches prior inert receipt,
stderr empty, 26 read-only os.open calls, zero external-operation calls and
cutover marker absent before/after. handoff_default_proof.json binds actual module,
verification script and source receipt. No full suite or SDK initialization.

## Handoff

Separate GATE accepted the exact launcher/proof delta with risk and no blockers.
It ran 32 tests once (0.30 seconds) and independently reproduced the actual
inert-default proof object exactly: exit zero, matching response, empty stderr,
26 explicit loader opens, zero tripwire calls and unused cutover marker.
Read counts cover os.open loader calls, not every interpreter/Path read; initial
probe receipt/scope file reads precede its patch context and are local reads.

Review: handoff_independent_review.json, SHA256
7b008031d3cddc3c5edaafc4b43116714e0ccb7fe7190bce61678901c57d4779.
Parent checked all 103 current review hash bindings before docs-only closeout.
Packet review's separate pre-closeout checkpoint exception remains explicit;
source/test/proof/report/accepted records unchanged. The handoff checkpoint hash
in its review identifies this document before closeout.

The offline packet and fixed-handoff objectives are complete. The next decision
is explicit operator authorization for ONE bounded actual attempt, not another
binding step. If separately authorized, the exact reviewed command is:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6h_20261026.execute_reviewed_v6h --execute-once
```

No such execution occurred in this work. Review acceptance is not permission
to run it. Runtime remains INCOMPLETE and current health/installed state unknown.
Preparation remains consumed; cutover unused. Old V6g records remain historical.
