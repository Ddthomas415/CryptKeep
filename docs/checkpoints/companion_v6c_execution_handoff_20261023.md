# V6c One-Shot Handoff

Active role: ENGINEER. Risk: HIGH (credential/runtime handoff).
Objective: fixed handoff to the accepted V6c V2 packet, offline only.
Implementation READY_FOR_INDEPENDENT_REVIEW; runtime INCOMPLETE.

## Change

Added execute_reviewed_v6c.py in the existing worker-preparation review folder
and tests/test_companion_v6c_handoff.py. Production sources, accepted packet
records, consumed receipts and old wrappers are unchanged. The consumed V6b
wrapper is not invoked or rebound.

Hash-pinned earlier generic helpers supply JSON hash checking, argument parsing,
exact-original SERVICE_TOKEN formatting, strict token parsing and anonymous-pipe
handoff. Import uses a non-main module name; old inputs()/execute() never run.

Default validates the accepted receipt/review/scope/runtime, hash-referenced
seven-subject table, thirteen current consumers, V2 network contract, worker-mode
plan and132pins. All child/runtime reviewers must bind the exact scope hash.
Recorded executable/continuation argv is refused. Existing default CLI stays inert.

Only separately authorized future --execute-once may validate again, refuse an
existing cutover reservation (including dangling symlink), verify the pinned CLI,
read one existing SERVICE_TOKEN from the exact original running orchestrator
ID/image and pass it through the private pipe. No account/exchange credentials,
fallback, retry, token persistence/logging/hash export. Exceptions/source payloads
are not printed; core dumps disabled. Reference clearing is not zeroization.

## Verification

VERIFIED_ENV, isolated local synthetic tests; real native/network access forbidden:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6c_handoff.py
```

SHOWN:23passed in0.31s. Actual accepted-input/default validation, helper/consumer/
record hash drift, contradictory scope/subjects/network/receipt/argv, consumed
paths, single synthetic source/private-pipe handoff, bad tokens/sanitized errors.
No broad suite, live credential or runtime verification.

Actual default module command, exit0, no execution flag:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_worker_preparation_20261023.execute_reviewed_v6c
```

SHOWN: input_bindings_validated=true,actions_executed=false,startup_authorized=false.
Saved stdout runtime_packet_v6c/handoff_inert_validation.json.

| Artifact | SHA256 |
| --- | --- |
| execute_reviewed_v6c.py | 6908501b0cf0c0c26c70f72b6d8e14ef8492cd6536a8bf2ef3822360e0eb2393 |
| tests/test_companion_v6c_handoff.py | 81785505e39f40c9b36fa7c98ebc0bbafcd3957b0516387ca7f72d9e7defe958 |
| runtime_packet_v6c/handoff_inert_validation.json | 91c6e302b2e2480eb28b939c8f40fcec03cf787b56ca4757f5e94cd4945dceaa |

Artifacts except the test are under the existing worker-preparation review folder.
Earlier generic-helper SHA5c319350...df12 unchanged; four accepted packet constants
and original v6c identity remain exact in the new wrapper.

## Future Boundary, Not Authorization

One future invocation reuses four accepted V6c stopped IDs: no preparation/build/
recreate, old-stage adoption, scheduler/account/strategy/risk/trading changes.
Three storage services and volumes remain untouched. After fresh preflight, four
original research apps may be gracefully quiesced/renamed/detached for rollback;
replacements may activate/start, pass existing source/storage/namespace/recipient/
health/citation checks and run one archived-evidence query. No health-only success.

Controller600seconds includes180recovery. Before it, CLI verification10seconds
and token-source inspect10seconds are separately bounded; validation file I/O has
no whole-wrapper deadline. Do not call600seconds a total wrapper wall limit.
Failure records sanitized diagnostics and attempts only owned cleanup/known-
original restoration within budget; healthy rollback is not guaranteed. No force
kill, numeric-PID fallback, reset or retry. Logs/audit/client initialization reads
may persist; stopping cannot undo all effects. Full success leaves replacements
running and original app objects stopped for rollback.

Retained limits: pre-token lexists is not atomic (controller locked reservation
controls actual once-only execution); handoff-entered is not mutation proof;
source formatting/live imports/SDK/startup/clock/pidfd/worker ownership/acknowledgment/
cancellation/recovery remain unverified. Final aliases stay MODELLED until actual
fail-closed activation checks. No profitability or general model-readiness claim.

Next: separate frozen-handoff review, then explicit operator decision on ONE
future runtime attempt. No live token, native capture, receipt reservation,
startup/cutover/query, or execution authorization in this implementation step.
