# SSH stage-diagnostic kit

Bot relation: BOT_RULES; runtime trading configuration not checked.

## Question and evidence boundary

Which client progress markers would distinguish transport establishment, an SSH
check prompt, client-reported authentication, a remote command request and a
reported remote exit in one future explicitly authorized preflight?

SHOWN: session70737 returned the check prompt and no inventory before its overall
timeout. The owner confirmed approval but does not know the browser status.
That is not evidence of an owner mistake, server outage, or effective policy.
The saved receipt cannot establish why authentication did not complete.

This kit prepares an invocation and reduces stderr. It does NOT implement a new
process controller, launch SSH, repair authorization, validate stdout inventory,
or authorize an operation. The unchanged prior connection contract and remote
command remain separate reviewed inputs. A future live integration is not yet
tested. No claim of profitability, full R3 completion or operational readiness.

## Smallest change

`ssh_stage_diagnostics_20261111.py` derives the exact prior invocation from
hash-checked source bytes, allowing only `LogLevel=VERBOSE` to become
`LogLevel=DEBUG1`. Strict keys, one connection, no forwarding/reuse,
outer300/connect210 and the unchanged remote70 command stay intact.
`validate_diagnostic` rejects complete-argv drift and unexpected effective
logging before applying the prior guard to a copy. Installed `ssh -G` renders
DEBUG1 as DEBUG; this is tested offline, not assumed to authorize access.

The streaming reducer accepts bytes, caps a pending line at4096 bytes, discards
an oversized line until newline, and drops incomplete final lines. It emits
fixed event labels once in observed order. Unknown lines, paths, fingerprints,
control-character-bearing URLs and free-form errors are not echoed. Missing
markers mean unknown, not that a stage failed. Server banner text can resemble
client logging: these labels are observations, not independent identity proof.
The copied receipt projection never contains a URL or raw line, never infers
causation, and always says inventory validation has not occurred.

## Approval-link handling

By default the CLI suppresses links. Only the exact HTTPS
`login.tailscale.com/a/<alphanumeric>` form, after the check marker, can be
offered once. `--show-owner-approval-url` enables direct owner handoff, not a
secret-free transcript. Chat/tool history MAY retain it. Do not describe this
as genuinely non-recorded or redirect opt-in output to a repository receipt.
For durable evidence, use only `receipt()` or the fixed SSH_STAGE lines.
Never offer a link after its same originating SSH session has ended.
The filter cannot verify session liveness; the invoking executor must do so.

## Recipe for a later separately authorized attempt

1. Review this kit and record its hashes. Obtain fresh authorization for the
   single connection, including the DEBUG1 delta and owner-link disclosure.
2. Capture and hash the unchanged remote source into memory; use those same
   bytes for stdin. Build `diagnostic_argv()`; resolve its actual options using
   local `ssh -G` and call `validate_diagnostic` before network execution.
3. Use the existing bounded native execution path, not another controller.
   Capture stderr separately and feed the reducer; never write raw DEBUG1
   output to a durable file. Keep stdout separate for the approved bounded
   inventory protocol. Persist only allowlisted markers and validated results.
4. Preserve the originating session ID before presenting its valid link;
   continue ONLY that session. Stop at the existing outer deadline or error.
   No new connection, automatic retry, policy change or service action.
5. Classify authentication, command request, identity, inventory completeness
   and R3 readiness separately. A marker or exit0 is not inventory acceptance.

This is a recipe, NOT an implemented integration or permission to run it. The
native executor's streaming, duration, stdout validation and cleanup still need
to be checked for this invocation before any live proposal. No raw source,
configuration or credential reading is added to the remote command.

## Verification and assumptions

Tests use synthetic banners and subprocesses of the filter, plus installed
`ssh -G` (no connection). They cover fragmented/oversized input, secret-bearing
unknown lines, URL domain/control-character rejection, marker independence,
source-hash drift, exact argv drift, receipt order/isolation, and default versus
explicit link output. Existing seven contract tests remain unchanged.

Assumption1: a future client emits the tested debug forms. If false, those
stages remain unknown; do not infer failure or success from their absence.
Assumption2: the invoking executor can separate and filter stderr before durable
storage. If false, do not enable DEBUG1 in a live attempt through that executor.

Acceptance: READY_FOR_INDEPENDENT_REVIEW for the offline kit; host proof and R3
INCOMPLETE. Separate review outcome, exact hashes and test result follow in the
existing work log/queue. This does not reopen the passed local Linux fixtures.

What do I know that could change the owner's decision that I have not yet said?
This kit makes a future failure more observable; it does not supply the missing
approval/control-plane evidence or a working host connection. Its streaming
integration is not implemented or live-proven, so another attempt is not yet
justified merely because these offline tests pass.
