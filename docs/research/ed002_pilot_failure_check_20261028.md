# ED-002 pilot: first unattended check failed

2026-10-28, checked at approximately 08:40 New York (12:40 UTC).
Active role AUDITOR. Installation previously SHOWN; unattended collection
INCOMPLETE. No job, permission, source, schedule or pilot window changed.

## SHOWN

Read-only namespace inventory found only the two empty scheduler log files,
no slot claim, result or capture manifest. No successful collection is shown.

`/bin/launchctl print gui/501/com.cryptkeep.ed002.public-inputs` returned exit0:

```text
state = not running
runs = 5
last exit code = 78: EX_CONFIG
job state = spawn failed
```

The intended program, arguments, working directory and output paths match the
installed public-data job. No environment credential values were sought.
Read-only unified-log access first failed with `Cannot run while sandboxed`.
The same targeted read then ran through command approval, returned exit0 and
showed `service inactive` at 06:35:04, 07:05:03, 07:35:04, 08:05:04 and 08:35:04
New York. These are launchd events, not collector-start or HTTP-request receipts.

Commands inspected native metadata/logs only; no kickstart, collection CLI,
network request, service change or catch-up was invoked by this check.

## Immediate Spawn Cause SHOWN

A second targeted read of the eight-second 08:35 launchd window, including debug
entries, returned exit0 through command approval. At 08:35:04.025 New York:

```text
Service could not initialize: Unable to open stdout path
(.../mac_pilot_20261028t1035z/scheduler.stdout.log),
error 0x1 - Operation not permitted
```

This identifies the immediate initialization failure as denied stdout-path
access. It does not identify the underlying macOS policy or prove that the
interpreter, working directory, source or output namespace would be accessible
after that issue is removed. Do not label it a Python policy-validation failure
or claim a successful repair from the diagnosis alone.

## Remaining UNVERIFIED State

Collector execution, request delivery and subsequent filesystem/network access
remain unverified. Empty Python logs do not prove that the wrapper ran.

The failure concerns unattended data acquisition, not strategy performance.
Existing foreground captures and original installation receipts are preserved.
No timestamps were repaired or evidence backdated. No study was activated.

## Next Action And Boundaries

An offline replacement plist is prepared in
`../review_artifacts/ed002_pilot_log_repair_20261028/`: only stdout/stderr move
to a pilot-specific directory under `/Users/baitus/Library/Logs/CryptKeep/`.
No installed file or directory at that proposed path was created or changed.
This avoids the observed denied log destination; it is not proof that all other
Downloads access will work. Do not grant broad disk access or move the repo.

Proposed separately authorized operation: verify current installed file/job
identity and unchanged policy/source pins, preserve the original plist, create
only the new log directory, replace the two log paths for this exact job and
reload it once. Keep RunAtLoad/KeepAlive false, no kickstart, no capture retry,
no second job, and no deadline/source change. On reload failure attempt to
restore the saved original configuration; restoration is not guaranteed and
must be reported, not retried blindly. Inspect the next naturally scheduled
receipt; further path denials require diagnosis, not automatic broader access.

A changed job/path/permission or forced diagnostic execution requires its own
scoped operational authorization; none is inferred from this offline proposal.
Preserve the original pilot expiry of October29 06:35 New York. Missed slots
stay missed; no automatic retry, window extension, duplicate job or source-pin
rewrite. Once the pilot is read, propose removal of this exact owned job; removal
has not been authorized or executed here. Collection readiness remains INCOMPLETE.
