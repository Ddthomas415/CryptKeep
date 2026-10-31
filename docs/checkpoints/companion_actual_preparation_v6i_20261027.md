# Actual V6i Stopped Preparation, October 27

Role: GATE closeout of separate review. Risk: HIGH. ACCEPTED_WITH_RISK
for saved preparation evidence and actual identities only.
Runtime INCOMPLETE. No startup, cutover or query authority.

## Approved Action and Result

Operator explicitly approved one stopped-preparation action: build/reuse four
local source-only images and create four stopped replacements, privately copying
existing configuration without displaying values. Originals and storage stay
untouched; no service startup, cutover, query or trading. Controller budget
300 seconds includes 120 recovery; cache/config/log effects may persist and
cleanup is not guaranteed. No automatic retry or reset.

Checked 67 current nonhistorical input-review bindings, exact review/manifest
hashes and current source maps. Both proposed markers were absent. The one
review-bound input checkpoint is historical pre-closeout text; no executable
exception. Native baseline/source/configuration checks remained the existing
reviewed controller's responsibility, not assumed from earlier observations.

Exactly one invocation, execution session 53316, exit zero:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m scripts.research.companion_prepare --manifest docs/review_artifacts/companion_integration_inputs_v6i_20261027/reviewed_preparation_manifest.json --reviewed-manifest-sha256 3c8066b43cf924374f2338907f306aadec25fdb599a2ef28a068ab0a21632a33 --execute-preparation
```

SHOWN tool result: preparation complete/actions true, startup authorized false,
services started false, originals interrupted false, attempt reserved true.
No repeat, marker reset or separate native postcheck performed.

## Saved Records and Actual Identities

Folder: docs/review_artifacts/companion_integration_inputs_v6i_20261027/actual_preparation/.

- receipt.jsonl: all seven events read, SHA256
  5bd4ff43665bfdbe9a0ece3cc4c91a9934501468e39ccfe7830674619a002533.
- preparation_evidence.json: SHA256
  6b307618be50d7e6179106fbcfc837ac5ec0695a12aaa9888b34fed54e8d2fcf.
- tool_result.json: exact returned tool output/exit metadata plus session ID;
  outcome.json parses that saved stdout, not independent runtime verification.

Receipt/evidence are byte-identical copies of the controller state files.
The published evidence lists four owned created-state replacements, never-started
timestamps, zero restarts and restart policy no:

| Application | Actual Container ID | Image Prefix |
| --- | --- | --- |
| Audit | c1b91732a755ba3dd0c6a449784df6a1b9c8d3ed600dd0e92800dddac7d30d10 | 27753fce |
| Risk | e94f1a3651ac49e9ccb3a0c876c475523c30451f9217fbdb71cf055b277a58a0 | b479fe20 |
| Memory | 50998076e44610503e9e72d5e9135541ebbfc0d0abd3980d8b90a6dc32f4a8e6 | 989471c8 |
| Orchestrator | 184db4ebae46f11b97cff8316ca11e7f7216a385f82ac99ccb620b15a768490d | c3059654 |

Memory image changed from V6h; the other three image digests match V6h. This does
not establish cache behavior or automatic SDK-policy inheritance for the changed
memory image. Controller source/identity/configuration checks are attestations,
not fresh independently captured image-parent/layer or SDK/source streams.
Configured-only network evidence is not connectivity. Original-preservation
claims come from the controller result/checks, not a separate native inspection.

## Verification, Preservation and Next Boundary

No code change or test rerun needed for the operation. Saved raw evidence hashes
match the controller output. A local export initially failed Python parsing from
shell newline quoting before any filesystem action; corrected the offline export
only. The preparation command was not repeated. Historical inputs, source repair,
reviews and INCOMPLETE candidate are preserved. No secret values were printed or
exported; the approved private configuration copy is distinct from token queries.

Request separate GATE review of saved receipt/evidence, ownership/IDs/stopped
state and pure manifest/model contracts. High-risk handoff state remains
READY_FOR_INDEPENDENT_REVIEW until separate review. Actual-ID acceptance must not
become installed SDK/source-policy acceptance or startup permission. New memory
image parent/layer/source evidence and applicability remain separately unverified.
Preparation is consumed. Runtime INCOMPLETE; no cutover/query authorization.

## Independent Review Closeout

Separate GATE accepted the saved evidence and four actual IDs with risk, no
blocking findings. It checked all seven receipt events, exact state-file copies,
tool-output consistency, manifest ownership/stopped-state contracts, current
43 application entries/13 preparation tools/20 runtime consumers, and four pure
configured-model predictions. Models and controller checks are not additional
native observations or independent source/SDK captures.

Review SHA256:
609100b858e95dafcc6953141790c17f700fc2e5519877f6ef639be92b764e7a.
Reviewer-authored five-field actual_id_review.json SHA256:
f50dc3ecdd7a6271138640c9ac7d873c20377edc0b98311fc63324d70d13efbb.
Both files are in actual_preparation/. All 79 nested review bindings matched
before this documentation-only closeout. The checkpoint binding now identifies
its pre-closeout text; saved controller and reviewer artifacts are unchanged.
Parent loaded the manifest and actual evidence through ReviewedPreparation.load
with the exact external actual-ID review hash, yielding four replacements.
No native calls or test suite rerun; no implementation change was needed.

The stopped-preparation action and saved-ID review are complete. Preparation
authorization is consumed; no retry/reset or startup follows. Runtime remains
INCOMPLETE. Next missing proof is actual new memory-image parent/layer linkage,
source-only overlay/source evidence and a separate SDK-policy applicability
judgment. Accepted identities do not fill that gap. Prepare that evidence scope
offline using the existing capture path; any new native capture still needs
explicit bounded authorization. No new infrastructure is indicated.
