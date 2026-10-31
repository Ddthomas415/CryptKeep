# Preparation Packet Reconciliation

Date: 2026-10-20. Active role: AUDITOR. Scope: offline packet review only.
Packet disposition: READY_FOR_INDEPENDENT_REVIEW; no operational approval.

## Shown Locally

Read-only verification with the local `.venv` interpreter completed with exit0:

- Original capture, candidate and source-recipe SHA256 values match their saved pins.
- All43 application source entries still match; source paths resolve without symlinks.
- Candidate baseline equals the seven snapshots in the saved capture.
- Network bindings and CLI digest equal that capture; application options, source
  entries, commands and policies equal the previously reviewed source recipe.
- Captured engine29.9.1/b26fb77 is now in the independently accepted exact-pair gate.
- The local attempt marker was absent at the time of this check. Reservation must
  still be exclusive at execution; this observation does not reserve the attempt.

VERIFIED_ENV applies to these offline checks only. Capture timestamp is
2026-10-20T22:50:27.663567+00:00, not a fresh claim about running services. The
accepted preparation API must recheck the exact baseline before any build/create.

Original artifacts remain unchanged in
`docs/review_artifacts/companion_continuation_20261020/fresh_v5_capture_20261020/`:

| Artifact | SHA256 |
| --- | --- |
| candidate_manifest.json | 0ed18df8e95da122d2f00e31badeb17122fee2049609369c1dd819a832c6c108 |
| capture.json | 0fa450f65997a8ace714babc6b514270eab308cd22f623a6e06177ab3c09fa1b |
| earlier configured recipe | f5b044858c3d40881239b77745d0b404c4ac05d2f35a6d043fed8f6ba934bf5f |

The original candidate remains INCOMPLETE with no reviewer. Independent review
may publish a separate accepted manifest; the dated original must not be relabeled.

## Preparation Boundary

Only the preparation-only entry point is proposed. If separately authorized, one
attempt builds four source-only local images and creates four never-started
replacements with unique staging names/aliases. It does not start applications,
interrupt originals, migrate schemas, query services or change storage resources.
Existing service environment values are copied transiently by the reviewed
encoder, not printed or persisted in receipts. This is credential handling and
must be included explicitly in operational authorization.

The controller has300seconds with120seconds reserved for recovery. Local input,
lock and reservation I/O precedes that controller budget; no total CLI wall-time
guarantee is made. The shared lock and durable per-attempt marker forbid automatic
retry. Recovery may remove only unchanged acknowledged stopped replacements owned
by this attempt. Unknown creation/cleanup is reported, not retried or called clean.
Images/cache may remain; pruning and removal of the prior proof image are excluded.

Actual stopped IDs, copied-source verification and metadata are output evidence
for the next independent review, not evidence that replacements already work.
Startup policies remain deferred, network connectivity unverified, and expected
replacement metadata is a prediction from the prior recipe. Neither packet review
nor inert validation establishes native readiness, restored explanation delivery
or profitability. Cutover requires a separate reviewed actual-ID packet and approval.

## Handoff

Separate GATE is reviewing the existing packet against the accepted compatibility
delta. No new runtime capture, build, Docker call, credential access, reservation,
service operation, scheduler, account or trading change occurred in this scope.
After packet review, run only default inert CLI validation with the independently
reviewed hash. Obtain explicit authority before adding `--execute-preparation`.

## Independent Review and Inert Validation

Separate GATE: ACCEPTED_WITH_RISK for the preparation recipe only; no blocker.
The reviewer recomputed all seven baseline projections and four modeled
replacement fingerprints, checked43 source entries (22 unique files), source
archive provenance and unchanged create/network options and deferred policies.
Receipt: `docs/review_artifacts/companion_continuation_20261020/preparation_packet_review.json`.

Separate reviewed manifest:
`docs/review_artifacts/companion_continuation_20261020/reviewed_preparation_manifest.json`.
SHA256: `3b6f785ca1dd732e307aa83b30dcea2a5d2d9379d57af06a4afaa3774df94635`.
Only decision/reviewer JSON values differ from the preserved candidate (plus a
terminating newline). No source, policy, option, original observation or threshold
was changed to obtain acceptance. The review supersedes the pending disposition
above for this separate recipe, not for actual replacements or runtime.

Parent default validation completed exit0 with this exact command:

```sh
./.venv/bin/python -B -m scripts.research.companion_prepare \
  --manifest docs/review_artifacts/companion_continuation_20261020/reviewed_preparation_manifest.json \
  --reviewed-manifest-sha256 3b6f785ca1dd732e307aa83b30dcea2a5d2d9379d57af06a4afaa3774df94635
```

SHOWN output: actions_executed=false, startup_authorized=false, controller budget
300seconds, recovery reserve120seconds, attempt `f4e189b78ccc48acb8b92f20c4627f51`.
CLI output uses READY_FOR_INDEPENDENT_REVIEW because actual stopped replacements
would require subsequent review; it is not a claim of preparation completion.
Parent rechecked the reviewed-manifest, original-candidate and capture hashes;
unchanged. No new pytest or full-suite run was necessary for this artifact-only
step. Runtime restoration remains INCOMPLETE.

Next operator decision: authorize exactly one preparation attempt with this
manifest/hash and the effects/recovery limits above. No startup or cutover is
included, and no automatic retry or additional native probe is proposed.
