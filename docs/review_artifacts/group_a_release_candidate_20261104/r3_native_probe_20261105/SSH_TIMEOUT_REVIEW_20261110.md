# Independent GATE: corrected live SSH invocation

Bot relation: BOT_RULES; runtime trading configuration not checked.

Reviewer: Harvey, separate agent `01a1c8d5-b1f9-7062-b5c6-1d0a886aa443`.
Git/newest work log checked through 2026-11-11T04:20:59Z UTC (November 10 New York).
This records the returned separate review, not implementation-author approval.

**ACCEPTED_WITH_RISK for the next invocation design only.** No blocking issue or
unintended security/operational change found. This does not authorize a retry.

SHOWN: the builder removes the short server-alive probes while retaining the
300-second outer alarm, ConnectTimeout210, strict host keys, one connection,
disabled forwarding/control reuse and unchanged 70-second remote command
(`9c241fd5...`). No authentication-policy or service change is introduced.

VERIFIED_ENV: reviewer independently ran the offline tests with bytecode writes
and plugin autoload disabled, using `python -B -m pytest -q -p no:cacheprovider
--noconftest -o addopts=`: **7 passed**. Includes actual local `ssh -G` old-option
rejection/new-option acceptance. No SSH connection, network request or file edit.

Limits: ConnectTimeout210 is not a guaranteed human approval window; the outer
alarm is the overall client cap. Tests check construction/effective options,
not live enforcement or browser handoff. The installed binary's exact internal
exit cause and actual host access/configuration/inventory remain UNVERIFIED.

What do I know that could change the owner's decision that I have not yet said?
Only the offline invocation design is accepted; live host proof remains INCOMPLETE.
