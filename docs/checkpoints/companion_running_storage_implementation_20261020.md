# Running-storage installer component

Date: October20,2026. Active role: ENGINEER. Risk HIGH.
State: ACCEPTED_WITH_RISK by separate GATE for the offline component only.
Full running-stack update/startup/query integration remains INCOMPLETE.

## Scope and actual implementation

Implements the installation/rollback portion of the separately reviewed
`companion_running_update_plan_20261020.md`, in the existing installer/backend.
The new explicit `companion-running-storage-install-v4` contract requires seven
initially running original containers and a configured-network contract. Old
schemas still require exited originals. The existing SDK/startup deferrals,
source hashes, CLI/engine checks, metadata gates and diagnostics remain intact.

All image preparation precedes application interruption. Only the four original
research applications may be quiesced, in reverse dependency order. Storage
snapshots must remain identical at every inventory. Replacements remain created
and never started by this component. No new controller or application rewrite.

On failure, only known attempt-owned created replacements can be removed.
Original names/network configuration are restored using existing checks, and
only acknowledged original interruptions are restarted in dependency order.
Unacknowledged quiesce outcomes remain unresolved; no ownership is invented.
Unacknowledged restarts report unknown start status and block dependent starts.
Restored running-state/configuration is distinct from service-health proof;
StartedAt cannot be restored exactly. A changed storage snapshot aborts mutation.

The v4 component has one600second installation/recovery budget with180seconds
reserved. It does not establish the future combined installation/startup/query
deadline. CLI `--apply-install` explicitly refuses v4 before backend construction
or receipt creation until that integration is implemented and separately reviewed.
It is not an executable deployment packet, even if its synthetic tests pass.

## Verification and handoff

Use the root venv with clean environment, bytecode/cache disabled and no root
conftest to exercise synthetic backends only. No Docker, endpoint, credentials,
service lifecycle, builds, migration, account, scheduler or trading operation is
part of this verification. Exact final command, result, hashes and independent
review will be retained in the matching review-artifact folder before handoff.

First focused run:167passed in0.97s across running-storage state-machine,
existing installer and metadata-diagnostic files. This preceded the explicit
unacknowledged-restart regression; it is not the final combined result.

First frozen combined run: **308passed in2.81s, exit0**. Exact command and four
source/test SHA256 bindings are in
`../review_artifacts/companion_continuation_20261020/running_storage_verification.json`.
It includes the two new test files and existing installer, metadata diagnostic,
network configuration, controller and runtime-wiring regressions. `git diff
--check` passed. No full suite, native lifecycle or deployment proof is claimed.

Native command construction uses only SIGTERM for quiescence; it never escalates
to SIGKILL or timed Docker stop. Each transition rechecks the exact original app
and unchanged storage within one bounded native transition deadline, with no
automatic second mutation after a command acknowledgment error. An error now
always leaves ownership unresolved, even if later state matches. This is synthetic
command/state proof, not a guarantee of actual graceful application termination.

Independent GATE reproduced308passes but REJECTED the first frozen delta for two
additional shown gaps: false interruption ownership after an unacknowledged
command, and rollback starting dependents after a prerequisite drifted. Original
review is retained as `running_storage_review_r1.json`. The bounded correction
refuses ownership on command error and compares all prerequisite snapshots before
each restart. Added external-actor and prerequisite-drift regressions.

Corrected frozen combined run: **316passed in2.41s, exit0**. Current hashes and
exact command are in `running_storage_verification_v2.json` in the same review
folder. This does not erase the first rejection or establish runtime readiness.

Separate GATE Hegel re-reviewed the frozen correction, reproduced both blocker
probes and independently ran the same seven-file slice:316passed in2.14s, exit0.
No remaining blocker found in that bounded re-review. Disposition and verified
four-file hashes: `running_storage_review_r2.json` in the review folder. Acceptance
requires retaining the CLI apply refusal; no native lifecycle, engine/builder,
service-health or full startup/query acceptance follows.

Remaining integration is explicit: namespace/SDK compatibility for actual
replacement images, current engine/builder proof, one shared deadline covering
startup plus the single guarded request, fresh runtime/source/policy bindings,
and independent citation/relevance verification. The earlier replacement
metadata-failure cause remains UNVERIFIED. No current engine pin, source hash,
saved manifest or frozen artifact is silently changed to make installation pass.
