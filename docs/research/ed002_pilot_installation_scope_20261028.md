# ED-002: bounded pilot installation scope

2026-10-28. Active role DIRECTOR. Risk HIGH (scheduler/configuration operation).
Installation proposal READY_FOR_INDEPENDENT_REVIEW; operations INCOMPLETE.
Submitted wrapper: operator ACCEPTED_WITH_RISK, not independently reviewed.

## Current Decision And Proof

The operator's "approve. carry out the next steps" follows the submitted wrapper,
disabled policy and template. Record human acceptance of that exact submitted
scope, without claiming source inspection or independent review. The explicit
earlier boundary still separates code acceptance from installation/collection.

SHOWN at 09:59:08 UTC on October 28: all 17 submitted bindings match; neither
`~/Library/LaunchAgents/com.cryptkeep.ed002.public-inputs.plist` nor
`research/ed002_public_inputs/pilots/mac_pilot_v1` exists. No network request.
Do not repeat the 200-test run without a changed source or contradictory evidence.
The generic Mac monitor installer was inspected but is NOT reused: it starts an
unrelated monitor immediately with a shell profile and a five-minute interval.

## Proposed One-Action Authority

Authorize one installation of the reviewed native job, bound to:

- This Mac/current user 501; label `com.cryptkeep.ed002.public-inputs` only.
- The exact reviewed wrapper, capture source/plan, universe and dependency pins.
  Preserve the disabled policy and template unchanged as historical artifacts.
- Start at the first UTC :05/:35 opportunity at least 15 minutes after the
  installation preflight. Fix end=start+24 hours, with at most 48 distinct slots,
  27 public GETs per slot and 1,296 GETs total. This start rule is proposed here,
  not previously authorized. It sets a collection pilot window, not study A/E/B.
- Generate one new dated policy/template from the reviewed disabled draft by
  changing only enabled, pilot_id, start_ms and end_ms. Retain all 10 source pins,
  max_slots=48, max_lateness_ms=120000, two-hour capture plan and no retry.
- Install only the new target file, preserving any pre-existing target, job or
  pilot namespace. No overwrite, unload-to-replace, forced wake, power change,
  immediate kickstart, historical catch-up or second installation attempt.
- Child execution stays public-only and collection-only. No private credentials,
  accounts, orders, strategy/portfolio/return calculations, fee/risk/capital edits,
  server/Docker, other schedules, git commit/push or study activation.

This permits repeated public acquisition only inside that explicit pilot budget.
It does not authorize long-term collection or a new AI task per observation.
No fixed calendar dates have been assigned before this authority is decided.

## Installation Checks And Bounded Failure Handling

Before changing anything, reverify all submitted hashes and interpreter/paths,
current-user loaded labels, exact target-file absence, and new pilot-namespace
absence. A failed label read is unknown, not absence. If a conflict exists, stop
without replacing it. No new discovery of unrelated private process arguments,
environment values, remote hosts or account state.

Prepare only the approved namespace and two local log paths; write the new
policy/template append-only and lint the plist. The policy hash in the native
command must match the dated file. Run the isolated CLI without --execute first;
it must produce a preview without a worker. Preserve that receipt.

Use exclusive creation for the user LaunchAgent file, mode 0600. Record the new
file's content hash and filesystem identity, then bootstrap only that file into
gui/501. RunAtLoad/KeepAlive stay false, with only the two calendar-minute keys.
Verify the label registration and unchanged file/source identity afterward.
Registration is not proof of the effective command or successful data delivery;
the first actual slot receipt supplies that separate evidence.

Propose at most 60 seconds of native-command budget, reserving 20 for owned
recovery; individual launchctl checks at most 8 seconds and plist lint at most
5 seconds. No automatic command retry. Local file operations and final receipt
writes are not represented as hard-interruptible; report their actual outcome.

On failure before bootstrap: preserve generated data/log evidence and identify
whether the exclusively created target is still owned by this attempt. Remove
only that new target if its identity/hash still match; do not delete capture data
or any pre-existing file. On confirmed successful bootstrap followed by failed
verification: boot out only the job demonstrably loaded by this attempt, then
recheck labels/target identity. If bootstrap times out or ownership is ambiguous,
do not blindly stop a matching label or overwrite/remove uncertain artifacts;
report INCOMPLETE and preserve evidence for an operator decision.

The future start margin is intended to keep the first data opportunity outside
installation/recovery, not guarantee the OS cannot stall. Do not silently move
the window, reset a receipt or force a capture after a failed installation.

## Success, Expiry And Acceptance

Success means the exact file is newly installed and its label registered, with
source/policy bindings and a receipt. It does not mean the first unattended slot
ran. Check actual raw capture/RESULT receipts afterward, without rerunning that
slot or scoring strategies. Missing opportunities remain missing.

At expiry the reviewed wrapper refuses further capture. The native job may
remain loaded and write refusal/log metadata; automatic unloading is not built
or implied. Any later removal must be scoped to this owned job, preserving data.
Failure or ambiguous cleanup keeps later collection held, not automatically reset.

## Other Agent Handoff, Not Additional Authority

Read the full direction note, four-fix handoff and October 24 handoff including
all four addenda. Their recommendations are reference evidence, not operator
authorization. Acknowledge them in the work log and queue their requested reviews
without implementing the reported live-safety changes in this pilot task.

The recommendation for an always-on shared server is preserved as an alternative;
it does not override the operator's explicit local Mac pilot choice. E1, backups,
the prior multi-symbol results, delisting/held-position contract and alert concerns
remain visible pending work. No new delisting exit, account access, dependency
upgrade, push/private-repo change or research pause is adopted from these notes.

Next decision is authorization for this single installation/pilot scope, not a
second implementation or another broad audit. Until then, the reviewed disabled
artifacts stay unchanged, no pilot dates are assigned, and nothing is installed
or collected. Study/statistics remain INCOMPLETE; no trading-readiness claim.
