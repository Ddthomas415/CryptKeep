# Independent gate: integrated SSH diagnostic wrapper

Bot relation: BOT_RULES; runtime trading configuration not checked.

Reviewer Rawls:01a1c9d6-7c8d-7c12-86ce-08152156ac6d. This record is
transcribed from separate reviewer responses; author tests are distinguished.

## Initial frozen source: REJECTED

Review checked2026-11-11T11:15:40Z. Wrapper7b66f1e8... / tests49234e9b...
matched submission. Reviewer independently reproduced64 passed/4 failed in
restricted execution and68 passed in1.64s with host permissions. A further
probe foundP1: a first interrupt during cleanup could bypass group signalling,
reaping and terminal bookkeeping after watchdog cancellation. Reviewer cleaned
its fixture. No other blocking finding was identified. That result invalidated
the initial candidate despite passing the initial68 tests; no live run occurred.

## Corrected diff: ACCEPTED_WITH_RISK

Diff-only review checked2026-11-11T11:20:32Z. P1 closed; no blocking findings
in the correction. Unchanged findings were not reopened.

- instrumented_ssh_preflight_20261111.py:5ef1b78ab179d5808bd95d6c3453ff665030e78cf1fe902bed36eafc2fcc3389
- test_instrumented_ssh_preflight_20261111.py:0e9eb6fd0330c98b8e12375843de24aa22a51b110965da5b58978c3eca81634c
- SSH_INTEGRATION_20261111.md:f6b35fab91f960aba5f160d4c33f610bc25380e54f786635ab75235cd211292b

SHOWN by separate reviewer response: all hashes match. The temporary SIGINT
handler is installed before spawn and stays active through group signalling,
fence closure, leader reaping and bookkeeping. Cleanup uncertainty takes
precedence over interruption; the previous handler is restored.

Reviewer independently ran the two actual SIGINT regressions with host test
permissions, python-B, plugin autoload/cache disabled:2 passed/40 deselected
in0.28s. Cases include normal cleanup and a live descendant with closed stdio.
Reviewer did NOT rerun the full corrected70-test suite. The author's final
70 passed in1.79s is separate self-checked evidence. Author before/after
regression runs were2 failed on pre-fix source and2 passed after correction.

No reviewer repository edits, SSH connection, network or service action.

## Disposition and remaining questions

ACCEPTED_WITH_RISK applies only to the corrected offline integration, not host
access, deployment readiness or runtime authorization. Main-thread execution,
OS/controller-failure limits, the observational own-group ps fallback and
partial inventory remain explicit. All prior single-connection authorizations
are spent. No new live attempt is permitted by this review record.

What could change the disposition: a new failure of owned cleanup/deadlines,
changed reviewed bytes, an incompatible execution environment, unexpected
protocol/identity, or new evidence that raw sensitive output can persist.
Only a separately authorized real attempt can establish the live access path;
transport success would still not close the remaining R3 operational gates.

What do I know that could change the owner's decision that I have not yet said?
Independent review caught a genuine bug that68 initial tests missed. The
correction has independent two-case confirmation, not an independently rerun
70-case result or a successful host connection.
