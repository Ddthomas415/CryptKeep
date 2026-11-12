# Integrated one-shot SSH preflight

Bot relation: BOT_RULES; runtime trading configuration not checked.

## Outcome and scope

The previously accepted stage reducer now has an execution-path integration:
`instrumented_ssh_preflight_20261111.py`. It is a standalone opt-in wrapper,
not a new service or scheduler. The default CLI and API start no connection.
No live connection was authorized or opened during implementation or review.
Host access and full GroupA/R3 remain INCOMPLETE.

This closes the offline integration gap recorded in SSH_STAGE_DIAGNOSTICS_20261111.md;
that earlier document is preserved unchanged as the reviewed historical recipe.
The separate gate and hashes are recorded in the work log and review artifact.

## End-to-end path

1. Load the accepted stage kit from the exact hash-checked bytes. Capture the
   unchanged remote command, verify its hash, and retain those same bytes for
   stdin. Build the accepted DEBUG1-only argv and validate actual local ssh-G
   fields. This preparation opens no connection.
2. Create a new0600 regular receipt with O_EXCL/O_NOFOLLOW in the existing
   artifact directory. An existing receipt, including an incomplete one,
   prevents another launch at that path. Never reset or overwrite an attempt.
3. Launch exactly one child, no shell, with a clean environment and new
   session/group. Start the watchdog and save its PID before a possible
   owner-link handoff. No connection retry, alternate host or policy repair.
4. Nonblocking selectors feed stdin and drain stdout/stderr concurrently.
   Raw DEBUG1 stderr never reaches the durable receipt or terminal. Only fixed
   client-marker labels are printed/stored. Combined stderr and stdout each
   have their own128KiB cap; pending stderr lines are capped by the stage kit.
5. URL display is OFF by default. Explicit owner handoff checks that the SAME
   child has not exited and the work deadline remains. Display never waits for
   owner interaction. Chat/tool history can retain the URL; no genuinely
   non-recorded display is claimed. Receipt projection never stores it.
6. Keep the unreaped leader as the PID/PGID ownership fence: Mac kqueue
   NOTE_EXIT, or Linux waitid WNOWAIT. Do not call poll/wait before disabling
   all process-group signalling. Kill only this owned group, close the signal
   fence, then reap the owned leader. Descendant reaping is not claimed.
7. A complete stdin write/closure, complete bounded stdout, zero exit and
   confirmed leader cleanup are prerequisites to parsing inventory. Duplicate
   JSON keys, trailing values, nonfinite constants and unknown top-level keys
   are refused. Identity must match the fixed host/user, with valid typed
   platform/version/source metadata. A marker or JSON prefix is insufficient.
8. Persist only an identity-bound PARTIAL inventory: host/user/UID, OS/arch,
   normalized version numbers, checkout commit and fixed source digests/status.
   Other approved inventory sections receive digest-only summaries, not raw
   values or error strings. This intentionally does not prove unit-policy,
   namespace, permissions, capacity or deployment compatibility. Even an exit0
   result retains acceptance status INCOMPLETE pending substantive review.

## Deadline and cleanup details

The existing child invocation retains alarm300, ConnectTimeout210,
ServerAliveInterval0, remote70 and strict host-key/no-forwarding controls.
The new parent work/watchdog deadline is295 seconds, with cleanup using ONLY
the remainder of the same300-second target. This is an earlier cutoff, not
an equivalent approval window. Initial local checks/receipt creation and final
validation/receipt writes are outside the child lifetime budget. The parent
watchdog can kill its owned group while a display or receipt call is blocked.
Uninterruptible OS I/O, controller SIGKILL, reboot and clock/process scheduling
can still defeat a strict overall elapsed-time/cleanup guarantee.

SHOWN in local synthetic tests: Darwin SIGKILL can be refused for an unreaped
zombie-only group even outside the sandbox. Permission denial is NOT treated
as success on that basis alone. After a denial and a known leader exit, one
bounded local `/bin/ps` probe of ONLY the owned PGID may inspect pid/pgid/stat.
It must include the fenced leader and show exclusively matching zombie rows;
otherwise cleanup remains unconfirmed and cannot yield inventory success.
Each probe has at most1 second within the same remaining budget. Raw ps
output is never retained. This metadata fallback is an addition to the
previous invocation scope and must be disclosed in any new runtime request.

Receipt-write/callback errors and CtrlC trigger owned cleanup. The saved
outcome distinguishes work deadline, nonzero exit, stdin failure, overflow,
validation failure and cleanup uncertainty. A failed final write can leave
an incomplete receipt; its existence still blocks reuse. No recovery/reset
or resume is automatic. Process-group absence/descendant reaping are not
guaranteed merely because a kill was sent.

## Verification and operational boundary

Fixtures run real local Python subprocesses, not mock-only transport. They
exercise default-no-launch, blocked stdin, retained pipes after leader exit,
stdout/stderr floods, stale links, saved PID before handoff, raw secret
suppression, malformed inventory, nonzero exit, receipt collision/failure,
interrupt, ownership fencing and cleanup uncertainty. Only ssh-G is used;
no SSH connection, credentials, account access or existing-service changes.

Consolidated author check:68 passed in1.60s (40 new integration tests plus
the prior28) with plugin autoload disabled, no bytecode/cache writes and
explicit host test permissions. The restricted run returned64 passed/4 failed:
the own-group metadata subprocess was denied with PermissionError/errno1;
cleanup correctly remained unconfirmed. Those failures are not erased by the
host-permission pass. Any live proposal must use a compatible authorized
execution environment, not suppress that check. Separate review is pending.

The only two material operational assumptions are:
- The authorized environment supports the tested non-reaping child monitor
  and ordinary process-group permissions. If not, refuse or remain INCOMPLETE.
- The authenticated host emits the unchanged approved protocol. If it differs,
  validation fails; missing markers do not establish a failure cause.

After separate source review, any live run still requires fresh owner
authorization: one known host/connection, DEBUG1 reduced before persistence,
optional owner-link disclosure,300-second child-lifetime target including
recovery, bounded own-group metadata fallback, no retries, and no policy,
deployment, service, database, schedule, account, risk, alert or trading change.
The wrapper does not infer authorization from earlier spent attempts.

What do I know that could change the owner's decision that I have not yet said?
The integration can now be tested end-to-end offline, but it has not completed
a real Tailscale check. It also deliberately saves only a partial inventory;
successful transport alone would not close the remaining R3 operational gates.

## Dated independent-review correction, 2026-11-11

The first frozen integration was REJECTED: a first SIGINT arriving after the
watchdog was cancelled, during group cleanup, could bypass signalling/reaping
and terminal bookkeeping. Existing interrupt fixtures covered the work/handoff
phase, not that boundary. The reviewer reproduced it; two author regressions
then failed on that same pre-fix source, including a live descendant with
closed stdio. Regression teardown explicitly cleaned its fixtures.

Correction: install a temporary record-only SIGINT handler BEFORE spawning.
Work loops turn the recorded request into cancellation; cleanup defers it
until group signalling/fence closure/reaping/bookkeeping finish, then restores
the prior handler and reports operator_interrupt (or cleanup_unconfirmed if
cleanup failed). It does not extend the absolute budget. This requires the
main thread; an unsupported signal context fails before child launch.
The two cleanup-interrupt regressions pass after the fix. A second interrupt
after handler restoration, SIGKILL or uninterruptible OS failure is not covered
by a guarantee. The later final review/result is recorded separately; the
initial68-pass result above did NOT establish this missing interrupt behavior.

What do I know that could change the owner's decision that I have not yet said?
Independent review found a genuine cancellation gap despite the initial passing
tests. It is corrected with before/after regression evidence, not dismissed as
an environment limitation; live host access remains untested.
