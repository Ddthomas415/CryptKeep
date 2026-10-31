# Installed Worker Prerequisites

Active role: AUDITOR. Objective: current read-only checks required by the
accepted offline v6 shutdown repair. Runtime/explanation: INCOMPLETE.

## Result At October23 08:49 EDT

SHOWN: all four original applications passed the exact accepted worker identity
validator: known PID1 shell, single direct child, expected module/port/argv,
handler/masks/starttime checks and revalidation after opening a worker pidfd.
The signal operation was replaced by a read-only fdinfo callback; no real signal
API was called, including signal zero. API presence and actual kernel pidfd
opens succeeded on all four; Python is 3.11.17 in each image.

SHOWN: all seven originals were running at their pinned image/start/restart
values, identical before/after selected metadata. The native observation used
six bounded command operations: inspect, four isolated exec probes, inspect.
No credentials or environment were read; command-line bytes were validated
internally and not exported. Temporary processes, opened/closed kernel handles
and Docker execution events are the disclosed side effects.

| App | Identity/pidfd read-only check | Remote minus host clock interval (seconds) |
| --- | --- | --- |
| audit-log | pass | [-0.010483, +0.078738] |
| risk-stub | pass | [-0.009573, +0.080299] |
| memory | pass | [-0.008602, +0.074958] |
| orchestrator | pass | [-0.009681, +0.085181] |

The clock intervals bracket one remote epoch sample between local request and
response times. Every interval includes zero. Round trips were 0.083561 to
0.094863 seconds. This is evidence against gross current clock skew, not exact
synchronization, an ongoing bound, or an approved deadline tolerance. No new
threshold was selected from the results.

## Preserved Proof

`runtime_packet/worker_capabilities_observation.json` SHA256
`3d2e9f7556208861f2a419bdc2216dbf0acf6a09455da2a23e16d5bd21cf217a`.
This is a sanitized transcription of actual tool output with method/limits,
not an independently repeated observation.

The executed read-only program is reconstructible from the accepted
`companion_worker_shutdown.WORKER_SOURCE` plus the exact saved
`runtime_packet/worker_capability_probe_suffix.txt`. Reconstructed SHA256 matches
the executed probe: `8229704e4d9f7bf24e5ebee1449005363c929780ad48bd17c5e7da1c3cc768e6`.
The suffix replaces signal dispatch with fdinfo inspection. Its whole-program
source was checked to contain no real `signal.pidfd_send_signal(` or `os.kill(`
invocation. Source/checkpoint/review and pinned Docker CLI hashes matched first.

## Remaining Boundary

UNVERIFIED: actual pidfd signal permission/delivery, successful graceful worker
and shell exit, acknowledgement survival, cancellation/recovery behavior, future
clock compatibility and a real cited explanation response. The current snapshots
do not prove the historical failure substep or inspect persistent data contents.

Next is independent review of this bounded evidence before offline fresh-v6
manifest/packet planning. No actual v6 manifest, fingerprints, stopped replacements
or new operational attempt were created. Creation/preparation and a cutover need
their separately reviewed exact inputs and authorization. Existing receipts,
consumed attempt and removed replacement IDs stay untouched.

No source changed or tests repeated. Verification was native read-only observation,
JSON/source-hash checks and preservation checks, not a full-suite or live shutdown
test. Evidence READY_FOR_INDEPENDENT_REVIEW; runtime INCOMPLETE.
