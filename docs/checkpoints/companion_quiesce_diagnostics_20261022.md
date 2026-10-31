# Offline Quiesce Diagnostics

ENGINEER / HIGH, October22 2026 21:02EDT (2026-10-23T01:02:32Z).
Objective: replay saved state and expose fixed, bounded quiesce substeps without
changing lifecycle policy or running another operational attempt.

## Replay Result

SHOWN offline: actual saved original rows and reviewed staged metadata pass
inventory and original-observation checks with and without the four prepared
rows. Default extra_ids and explicit prepared IDs select equivalent snapshots.
Older unrelated staged rows remain excluded by the existing selection. No
deterministic metadata-selection refusal was reproduced.

Evidence runtime_packet/quiesce_saved_state_replay.json; repeatable tests
test_saved_precleanup_state_replay[False/True] bind all three input hashes.
This does not execute Go templates or establish original timing, acknowledgement
or causality. The prior quiesce cause remains UNKNOWN, not "shell forwarding".

## Minimal Implementation

companion_install_docker.py adds optional internal phase markers to the existing
transition and quiesce_report(), which returns only a fixed schema:
schema,stage,command_attempted,command_acknowledged,confirmed. It catches normal
exceptions without including class names, exception payloads, stderr, response
bodies, environment, credentials, arbitrary IDs or timing values in reports.

Stage meanings:
- target_validation: target guard did not complete.
- pre_observation: initial guarded inventory did not complete.
- pre_state: observed state was not the required running state.
- signal_command: command path invoked but did not acknowledge successfully.
- post_observation: command acknowledged but subsequent guarded observation failed.
- exit_timeout: command acknowledged; no verified exit before the shared deadline.
- exit_verified: acknowledged command followed by verified exit.

command_attempted means entry into the command operation, not proof Docker
dispatched a signal. command_acknowledged means command returned successfully,
not proof a worker handled the signal. Only verified exit confirms transition.
If the child is killed/cancelled or cannot return its JSON result, the existing
generic failure remains; no report is invented or accepted as success.

No signal, recipient, deadline, polling, restart policy or force-kill behavior
changes. Direct legacy quiesce()/restart_original() behavior remains tested.

companion_installer.py validates exact report keys, schema, boolean types and
per-stage flag combinations before recording it. The concrete report path is
called once; legacy synthetic backends retain their existing boolean interface.
Invalid reports never become receipt payloads. A failed or unacknowledged report
cannot clear pending ownership, restart an unowned original or permit execution.
Successful child reports still require the existing parent fresh-state checks.
Verified ownership is recorded in parent memory before a new diagnostic receipt
write, so failure of that write still reaches existing owned recovery. Query and
forward progress remain blocked on receipt failure.

## Verification

VERIFIED_ENV: final frozen source, Python3.12, synthetic commands/clock/native
state only; subprocess/network calls forbidden in the new tests. One test uses
the real bounded child JSON channel with only a synthetic failure/payload.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_quiesce_diagnostics.py tests/test_companion_running_backend.py tests/test_companion_running_storage.py tests/test_companion_reviewed_continuation_handoff.py tests/test_companion_staged_update.py tests/test_companion_running_update.py
```

305passed1.90s. Covers every report stage, lost acknowledgements after actual
fixture state change, no extra signal/SIGKILL/retry, exact deadline retention,
malformed/secret-bearing/numeric-boolean report refusal, parent fresh-state
drift, unresolved ownership, write-failure owned recovery and saved-row replay.
Earlier212/271-pass development runs were not the final frozen source proof.
No full suite or live runtime tests.

The old exact continuation/handoff bindings are stale after these two consumer
changes. Tests now explicitly require rejection when consumers differ instead
of assuming an old accepted packet remains executable forever; a separate
synthetic test covers default inert dispatch. Original artifacts/records and
historical positive proofs are unchanged. No new accepted operational inputs,
preparation, reservation or handoff is generated to make validation pass.

| Frozen Artifact | SHA256 |
| --- | --- |
| scripts/research/companion_install_docker.py | 68d94d9f3f47fc5e45a8f3e1a9e28b691a8374a385dcf90d54926554879380a1 |
| scripts/research/companion_installer.py | 4e9b4a723b589cc161213c110591a1040fd18941f2a3de1ecc1fe49ead3ee453 |
| tests/test_companion_quiesce_diagnostics.py | 2906db39492425c5c622828896576dc470f0df2b3e46bffe6745f69eb38860bc |
| tests/test_companion_reviewed_continuation_handoff.py | b6ce02bc941502926090278178a06883e3520759f8d06845fa4ea59f0833dc4b |

Implementation READY_FOR_INDEPENDENT_REVIEW. No native commands, real token,
new signal, preparation, restart, cleanup, collector, account or trading action
this step. Original consumed receipts and historical evidence remain unchanged.
Runtime remains INCOMPLETE. Diagnostic coverage is not a shutdown-policy fix or
evidence that another attempt will succeed; do not recreate and retry blindly.
