# Orchestrator Shutdown Diagnosis

Active role: AUDITOR. Scope: read-only current process observation and saved
source comparison. Runtime/explanation: INCOMPLETE. No operational approval.

## Result

SHOWN at 2026-10-23T01:12:15Z (October22 21:12 EDT): original orchestrator
container PID1 is `sh`, with no SIGTERM handler; its direct child PID7 is
`uvicorn`, with a SIGTERM handler. Neither main-thread mask blocks SIGTERM.
The container remained running, with the same ID, image, start time and restart
count before/after. Sanitized evidence is
`../review_artifacts/companion_continuation_20261021/runtime_packet/orchestrator_signal_observation.json`.

SHOWN in `companion_install_docker.py::_original_transition`: current quiesce
sends SIGTERM to the container's main process, not explicitly to its worker.
[Docker's kill documentation](https://docs.docker.com/reference/cli/docker/container/kill/)
describes the shell-wrapper forwarding limitation.
[Linux proc status documentation](https://man7.org/linux/man-pages/man5/proc_pid_status.5.html)
defines the caught, ignored and blocked masks; the
[Linux kill documentation](https://man7.org/linux/man-pages/man2/kill.2.html)
describes PID1's special handler requirement. These sources were opened in this
investigation, not inferred from search snippets.

UNVERIFIED: whether the prior failed attempt reached and acknowledged its signal
command, or failed at another observation/timeout boundary. Current evidence
supports a shutdown-target mismatch; it does not identify that attempt's exact
failure substep or prove a worker-targeted stop will complete within ten seconds.
No signal was sent to test the hypothesis.

## Concrete Repair Direction

The already-frozen preparation manifest also gives all four proposed replacements
the same `sh -c uvicorn ...` command. Reusing it unchanged would preserve this
shutdown weakness. This is a saved-manifest observation, not a live inspection
of all four original process trees. The failed attempt removed its replacements.

Recommended next scope is one offline lifecycle-contract repair, not another
blind cutover: give future replacements a reviewed `exec`-based worker launch;
for unchanged originals, specify a verified worker-targeted graceful shutdown
with exact container/image/process ownership and identity-race protection.
Do not hardcode observed PID7, signal every Python process, add SIGKILL, extend
deadlines silently, or recreate originals to work around the problem. Any worker
targeting must retain parent verification, pending ownership and bounded recovery.

This changes the reviewed lifecycle contract and replacement metadata. It is
not implemented or authorized by this read-only investigation. It needs a
separate bounded implementation/review scope before any fresh preparation or
operational authorization. Existing runtime bindings remain stale and the prior
attempt remains consumed; receipts and removed IDs are not reset or reused.

## Verification And Limits

Pinned CLI hash matched. Three native read-only command operations completed
successfully: sanitized inspect, fixed proc-status exec, identical inspect.
Each had a 15-second timeout, empty temporary Docker config and explicit socket.
The temporary exec process and Docker execution events are disclosed side effects.
No token, environment or process command line was read. No startup, service
query, signal, stop/restart, build, preparation or retry occurred.

No tests were rerun: no source code changed. The earlier diagnostic patch has
separate ACCEPTED_WITH_RISK review; this observation neither changes that patch
nor establishes a working explanation request, trading readiness or profitability.
