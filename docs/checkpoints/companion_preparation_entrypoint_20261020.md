# Preparation-Only Entry Point

Date: 2026-10-20. Active role ENGINEER. Risk HIGH.
Offline review: two blockers closed, ACCEPTED_WITH_RISK by separate GATE.
Actual preparation and runtime restoration INCOMPLETE.

## Scope

`scripts/research/companion_prepare.py` wraps the independently accepted staged
API. It does not change the accepted installer CLI or introduce a cutover path.
Default behavior reads and validates a separately reviewed v5 manifest only.
No backend, lock, attempt directory, credentials or Docker calls are needed for
default validation. There is no start, query, service-token or cutover option.

This is offline code and synthetic verification, not permission to operate the
running research stack. No actual preparation was executed in this scope.

## Inputs and Packet Boundary

The input packet is the existing `companion-staged-update-v5` reviewed manifest,
not a new approval format. It must bind a new attempt, exact original seven
snapshots, frozen sources, create/network options and reviewed CLI checksum.
The externally supplied SHA256 must match its actual bytes. This command never
generates the reviewer, acceptance state or replacement-ID review itself.

A fresh operational packet has NOT been generated from current native state.
Do not convert the old consumed all-stopped manifest or relabel stale observations
as current. The manifest needs independent review before operational use. Actual
baseline equality is checked again by the accepted API before any build/create.
The existing strict engine pin remains unchanged; compatibility is UNVERIFIED.

## Inert Validation

From the repository root, the following is a template, not a command containing
currently verified input values. Substitute only the separately reviewed packet
and its known hash. Validation does not reserve an attempt or contact Docker.

```sh
./.venv/bin/python -B -m scripts.research.companion_prepare \
  --manifest /absolute/path/to/reviewed-v5-manifest.json \
  --reviewed-manifest-sha256 REVIEWED_SHA256
```

To perform preparation after separate authorization, the same invocation adds
`--execute-preparation`. That flag is an explicit action selector, not a substitute
for the operator's authorization. Do not execute that form merely because this
code passes tests or its default validation succeeds.

## One Preparation Attempt

The command takes the existing nonblocking global install lock. Busy/invalid
locks refuse; do not delete another process's lock. It then reserves the fixed
directory `.cbp_state/runtime/companion_preparations/<attempt>/` exclusively.
The directory is a durable consumption marker even after failure; changing the
manifest hash or invoking from a new shell cannot bypass it for the same attempt.
Do not delete a failed marker to retry. A new attempt requires a new reviewed
packet and operational authority. This is a CLI guarantee, not a restriction
against an operator manually editing local state or invoking lower-level APIs.

Directory traversal is descriptor-relative and rejects symlinks, foreign owners
and group/world-writable state directories. The new attempt directory is0700;
`receipt.jsonl` and `evidence.json` are0600, exclusive, no-follow artifacts.
The receipt uses the existing flush/fsync writer; evidence is canonical public
preparation JSON whose exact SHA256 is reported. Failed/partial files are retained,
not overwritten or presented as accepted evidence.
Every newly created ancestor entry is fsynced through its parent before descent
and before backend construction. A failed barrier prevents native work. Failure
summaries and the final receipt expose allowlisted stage/phase names and unresolved
creation/cleanup targets without raw exception text; an unknown creation is not
mistaken for successful cleanup.

The API retains its300second controller budget with120seconds reserved for
recovery. Local manifest validation/lock/reservation occurs before this native
controller budget; no total CLI wall-time bound is claimed for that local I/O.
Evidence publication and its receipt confirmation use the remaining controller
work budget. A publication failure attempts cleanup only of unchanged acknowledged
created replacements, within the same recovery deadline. Unknown creation or
cleanup outcomes remain unresolved. No automatic retry is added.

## Expected Effects After Authorization

Preparation builds four local source-only images and creates four stopped
replacements with unique staging aliases; those artifacts consume disk space.
The accepted backend copies existing research-service environment values only
transiently in bounded children. It does not print or persist them. Build images
may remain after a failed attempt; no image prune is authorized.

Original seven containers stay untouched by this phase. No application starts,
original interruptions, storage lifecycle, migrations, ingestion or explanation
query is part of this command. Output contains actual stopped replacement IDs,
not permission to use them. Independent actual-ID/policy review and a separately
authorized cutover remain necessary.

## Verification and Handoff

SHOWN: isolated module `--help` exits0 and exposes only the three documented
arguments. This is not execution proof. Synthetic entry-point tests and separate
GATE review are pending. Prior accepted v5 proof remains intact; no source in
that accepted component was edited for this entry point.

Frozen targeted proof:198passed1.69seconds, exit0, across new entry-point tests
and three accepted dependency slices. The new file contains26 cases using the real
accepted staged API, temporary filesystem and a synthetic backend; native command,
socket and startup paths are forbidden. Diff-check passed. Exact command and two
new file hashes are in
`../review_artifacts/companion_continuation_20261020/preparation_entrypoint_verification.json`.
Separate GATE reviewing the frozen entry point; no acceptance inferred yet.

The first GATE rejected two gaps despite passing tests: incomplete failure
summaries and missing parent fsync for new ancestor directories. Retained review:
`../review_artifacts/companion_continuation_20261020/preparation_entrypoint_review_r1.json`.
Both received bounded corrections and eight new regressions. Corrected final
four-file slice206passed1.85seconds, exit0, diff-check clean. Exact command and
new hashes are in `preparation_entrypoint_verification_v2.json` in the same folder.
Corrected implementation READY_FOR_INDEPENDENT_REVIEW; accepted dependencies are
unchanged and no actual operation has been executed.

## Final Bounded Re-Review

Separate GATE closed both initial findings ACCEPTED_WITH_RISK, independently
confirmed both corrections with synthetic repros, reproduced206passed1.60seconds,
matched both hashes and passed targeted diff-check. No remaining blocker in the
bounded re-review. Receipt: `preparation_entrypoint_review_r2.json` in the same
review folder. The first rejection and198-test proof remain preserved.

The new command is implemented; actual preparation is not performed or authorized.
Next is a read-only current-state capture to assemble the actual reviewed v5 input
packet. Do not repeat this offline implementation without changed or contradictory
evidence. Native engine/build/durability behavior and real cited delivery remain
UNVERIFIED; service restoration remains INCOMPLETE.

Subsequent read-only capture is complete in `companion_fresh_packet_20261020.md`.
The actual engine differs from the existing strict pin; the fresh draft remains
INCOMPLETE. Do not repeat capture/command implementation merely because no build
was authorized. Existing environment overrides already address the legacy flags;
no additional environment repair was demonstrated.

UNVERIFIED: actual fresh manifest, engine/builder compatibility, real builds,
filesystem durability under host failure, native metadata transitions, lifecycle
recovery, storage preservation and cited explanation delivery. No Docker/socket,
HTTP, credentials, containers/volumes, scheduler, account or trading operation
was performed during this implementation. Do not call restoration complete.
