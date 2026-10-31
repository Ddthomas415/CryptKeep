# V6b Execution Handoff

Active role: ENGINEER. Risk: HIGH (credential handoff/runtime operations).
Objective: prepare the smallest reviewed handoff to the accepted v6b controller
inputs. This turn is offline only. State: READY_FOR_INDEPENDENT_REVIEW.
Runtime/explanation remains INCOMPLETE. No execution authorization inferred.

## Implementation

New wrapper:
docs/review_artifacts/companion_worker_preparation_20261023/execute_reviewed_v6b.py
SHA256 f9362e808538fa9d3fdbe7dc29b8bb947283bbd2ae720771963df1b8d4b37dfe.
Tests: tests/test_companion_v6b_handoff.py
SHA256 6a6f31ef11cbaaaf28f1a927cb29ab42bbd6b9f5612744770cc26f98d55915d7.

It reuses the old hash-pinned helper's exact token-source format, token parser,
argument parser and anonymous-pipe handoff. It never calls that old launcher's
inputs()/execute(), never adopts removed IDs or resets any consumed marker.
All existing controller, transport, policy and preparation source/records stay
unchanged. No general new credential or container-control mechanism is added.

Default mode validates the exact accepted v6b receipt/review/scope/runtime hashes,
all13 current consumers, seven exact subjects and132 pins, and delegates to the
existing inert controller. It never reads a token, constructs a native backend,
reserves an attempt or changes a service.

Explicit --execute-once is for a separately authorized future command only.
It repeats all validation before any credential read, refuses an existing
cutover reservation (including dangling symlink), verifies the pinned native CLI,
then reads only SERVICE_TOKEN from the exact original running orchestrator ID/
image. Existing parser refuses absent, duplicate, malformed or nonprintable data.
The token remains process memory/private-pipe only: no argv/env/file/log/hash
export, no fallback and no retry. Arbitrary exception/source payloads are not
printed. Core dumps are disabled. Existing controller owns the consumed pipe,
exclusive lock/reservation, runtime deadline and recovery.

## Verification

VERIFIED_ENV: repository virtualenv, empty environment, no bytecode/cache writes.

env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
./.venv/bin/python -B -m pytest -q -o addopts= -p no:cacheprovider
tests/test_companion_v6b_handoff.py tests/test_companion_reviewed_cutover_handoff.py
tests/test_companion_cutover_inputs.py

Actual command used the above as one shell invocation:52 passed in0.71s.
Includes18 new v6b cases; actual accepted input validation/default mode plus
synthetic CLI/token/pipe/status failures. Native and network entrypoints are
forbidden in these tests except explicitly fake token-source responses.
Existing pipe tests use only owned local descriptors and synthetic tokens.
No full suite or real credential/runtime test was run.

Default CLI:

env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B
-m docs.review_artifacts.companion_worker_preparation_20261023.execute_reviewed_v6b

One actual host invocation, exit0; input_bindings_validated=true,
actions_executed=false, startup_authorized=false. Saved exact command/output:
runtime_packet_v6b_launcher/handoff_inert_validation.json. No execute flag.

## Future Operation Boundary For Review, Not Authorization

- One invocation for preparation/cutover identity workerprep20261023v6b; do not
  repeat an invocation or reset any receipt after an uncertain result.
- Current accepted four stopped IDs are reused, no build/recreate/adopt-old-ID.
- Three existing storage containers remain running; no migration, resource
  initialization, volume removal, ingestion, scheduler or trading operation.
- After fresh preflight, four original application workers may be gracefully
  stopped, renamed for rollback and detached; the four prepared replacements
  may take their names/aliases, start and undergo existing bounded checks.
- Read existing internal service token privately; no account/exchange keys.
  Existing health/storage/source/lineage checks and one archived-evidence cited
  explanation probe remain required. Health alone is not explanation acceptance.
- Controller budget600s includes180s recovery reserve. Before controller entry,
  native CLI verification is bounded10s and token-source command10s; this is not
  a claim that the entire wrapper including those phases has one600s deadline.
- Disclosed effects: application startup/log/client-initialization reads, Docker
  names/network/state and persistent audit writes from the bounded query. Stop
  or rollback cannot undo all logs/audit effects.
- Failure: existing controller captures sanitized stage diagnostics and attempts
  only owned cleanup/known-original restoration under its budget. No force kill,
  numeric-PID fallback or retry. Lost acknowledgements and rollback-health
  verification remain explicit risks; restoration success is not guaranteed.
- Success: leave the four replacements running only if every existing
  acceptance/receipt/query check passes; retain stopped original application
  objects for rollback. No profitability or general model-readiness conclusion.

Next proof: independent review of this frozen wrapper, tests, helper reuse and
actual accepted-input bindings. Only after acceptance may an explicit operator
decision authorize the one future --execute-once invocation. This checkpoint,
past approvals and default-mode success do not grant that authority.
