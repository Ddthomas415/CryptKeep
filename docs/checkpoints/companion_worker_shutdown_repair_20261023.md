# Offline Graceful-Shutdown Repair

Active role: ENGINEER. Risk: HIGH (lifecycle/concurrency).
Objective: close the demonstrated shell/main-process shutdown mismatch without
forced stops, changing current services or reusing consumed operational inputs.
Implementation: READY_FOR_INDEPENDENT_REVIEW. Runtime: INCOMPLETE.

## Chosen Contract

New explicit manifest schema `companion-worker-staged-update-v6` opts into
verified original-worker shutdown and direct replacement launch. v1-v5 remain
unchanged, including their existing signal path. No actual manifest, prepared
container, approval record or operation is produced by this implementation.

For v6, all four replacements must use the exact per-service
`python -m uvicorn <module>:app --host 0.0.0.0 --port <port>` command. Shell
commands, wrong modules/ports and explicit entrypoint overrides are refused.
Image inspection requires an empty inherited entrypoint before creation or
credential collection. Metadata capture recognizes these fixed commands as well
as legacy commands; arbitrary command text remains unexported.

For originals, the same parent baseline checks precede a single fixed isolated
Python exec inside the exact container ID. The program validates the known PID1
shell command, exactly one direct child, expected worker/module/port command,
PPid, TERM handler/masks and start time. It opens a Linux pidfd, revalidates
identity, then sends only SIGTERM through that handle. PID7 is not hardcoded.
There is no numeric kill fallback, process-group signal, SIGKILL or retry.
Missing pidfd APIs/support, malformed identity or ambiguity refuse the operation.

The backend uses its unchanged ten-second monotonic lifecycle budget. The
embedded program also checks the remaining absolute wall-clock deadline and a
derived local monotonic deadline before signaling. Launch/inspection time is
not intentionally refunded. Expired or backward-clock observations refuse.

Only a fixed acknowledgement crosses the exec boundary; errors produce exit1
without exception text, arguments, proc contents or environment output. A lost
ack remains a failure even if a worker exited. The parent still needs fresh
inventory/storage/stopped-original verification before confirming ownership.
Existing pending ownership, recovery, receipt rules and restart path remain.

v6 continuation records must bind the new worker source as an additional exact
consumer. Old actual handoffs/records are unchanged and stale, not regenerated
or made eligible. A new operational packet must review all changed consumers,
replacement fingerprints, capability evidence and fresh preparation separately.

## Offline Verification

VERIFIED_ENV command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_worker_shutdown.py tests/test_companion_quiesce_diagnostics.py tests/test_companion_running_backend.py tests/test_companion_running_storage.py tests/test_companion_staged_update.py tests/test_companion_staged_cli_boundary.py tests/test_companion_installer.py tests/test_collect_companion_recreation_metadata.py tests/test_companion_cutover_continuation.py tests/test_companion_reviewed_continuation_handoff.py tests/test_companion_running_update.py
```

Final result: 509 passed in 3.66s. Native subprocess/network/process signals
are forbidden in the new tests; procfs, pidfds, state and clocks are synthetic.
The new tests compile/use the embedded worker source, not an alternative model.
No full-suite, installed-image capability, service startup or shutdown proof.
An earlier development run had two failing new entrypoint tests because their
fixture had no applications; the fixture was corrected before the final run.
No production change was made to satisfy those fixture failures.

`git diff --check` passed on changed tracked sources. The checkout has substantial
prior changes; its full git diff is not attributed to this repair.

## Material Assumptions And Remaining Risks

1. The exact pinned image/process tree is trusted, not an adversary deliberately
   spoofing argv or executing different code between validation and signal.
   pidfds prevent numeric PID reuse from redirecting the signal; they do not
   atomically freeze executable identity. If this assumption fails, refuse this
   route and design a different ownership boundary rather than claiming safety.
2. Host/container wall clocks are coherent during a bounded operation. Their
   compatibility is UNVERIFIED here. Clock skew can cause refusal or deadline
   misalignment; current read-only capability/time evidence is required before
   approving a runtime packet. Local monotonic checks do not prove clock sync.

Installed Linux/Python pidfd capability, exact original-worker argv on every
app, successful worker shutdown and shell/container exit within ten seconds
remain UNVERIFIED. The in-container exec may itself be terminated when PID1
exits before its acknowledgement is delivered; this intentionally remains an
unresolved owned-intent failure, not success inferred from later state. No live
retry is authorized to resolve that uncertainty.

The program reads only bounded proc status/stat/children and command-line files
for identity validation. It never reads environment or credentials and never
returns process arguments. This differs from the earlier read-only observation,
which did not inspect command lines; no such live inspection occurred here.
Controller cancellation/transport loss still requires pending ownership and
fail-closed handling. No source patch can establish the historical failure's
precise substep after the fact.

## Frozen Sources For Independent Review

| File | SHA256 |
| --- | --- |
| scripts/research/companion_worker_shutdown.py | 2666d12f37b178a42e2f04fd869bc2a6768b4b070bcfd83bc70298d43a0cb659 |
| scripts/research/companion_install_docker.py | 470783aa8f126bb5c73b0dc8f7373a00069050ceb89ec08bc95cd66c15199f84 |
| scripts/research/companion_installer.py | de1a969fdd522b069cc0bca03c4d714e7b80e8842ac167ec9d4ffcb8f8a1b334 |
| scripts/research/companion_cutover_continuation.py | b9e0a01c7770156475fd764446aede4c45adebaada4b21a2820946399cfb1365 |
| scripts/research/collect_companion_recreation_metadata.py | 8105974ae7ad02f8c90bc0e0a1827a4a58b40838236b5125638785ada80daf9a |
| tests/test_companion_worker_shutdown.py | edb49030f0cfc9883f03d192fd99fb15c67c1982cfd16dff8d60c0c0fa707f23 |

No native commands, credentials, service requests, signals, builds, preparation,
containers, schedules, accounts or trading operations were used in this step.
Separate review is the next gate for implementation only, not permission to run.
