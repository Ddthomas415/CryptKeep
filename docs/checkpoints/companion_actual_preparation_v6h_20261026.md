# Actual V6h Stopped Preparation, October 26

Implementation role: ENGINEER. Risk: HIGH.
Separate GATE outcome: ACCEPTED_WITH_RISK, saved evidence/actual IDs only.
Runtime INCOMPLETE. No startup, cutover or query authority.

## Action and result

Operator explicitly approved one stopped-preparation action: build/reuse four
local source-only images and create four stopped replacements, privately copying
existing configuration without exposing values. Originals and storage stay
untouched; no service startup, cutover, query or trading. Controller budget
300 seconds includes 120 for recovery. Cache/config/log effects may persist;
cleanup is not guaranteed. No automatic retry or reset.

Offline preflight checked 62 current nonhistorical input-review bindings plus
manifest-export crossbindings. Both proposed state markers were absent. The
pre-closeout checkpoint digest is explicitly historical. Current native/source/
configuration/ownership checks remained the existing controller's responsibility.

Exactly one invocation, execution session 29014, exit zero:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m scripts.research.companion_prepare --manifest docs/review_artifacts/companion_integration_inputs_v6h_20261026/reviewed_preparation_manifest.json --reviewed-manifest-sha256 d11fccb5e4f7c46e7d726704c9b75c400a1482eab5d1b840027d876a5837f047 --execute-preparation
```

SHOWN tool result: preparation complete/actions true, startup authorized false,
services started false, originals interrupted false, attempt reserved true.
No repeat, cleanup/reset or separate native postcheck was performed.

## Saved records

Directory: docs/review_artifacts/companion_integration_inputs_v6h_20261026/actual_preparation/.

- receipt.jsonl: all seven events read; SHA256
  bc3e272960d0e5f001dae037b1066c19f7409dc9b93f07f419940e187bded250.
- preparation_evidence.json: SHA256
  950b09d049a7f6a01f91352cb8ff12e1edecedfcf523c13fc75d39e9f25b805d.
- outcome.json: explicitly attributed parent transcription of the tool result,
  not independently captured process output.

Receipt and evidence are byte-identical copies of the controller's state files.
Published evidence lists four new owned created-state replacements, never-started
timestamps, zero restarts and restart policy no:

| Application | New Container ID | Image Prefix |
| --- | --- | --- |
| Audit | 4f6534593e7bcbdca96d3cc72e30519e007731c2dab464d55fb804575d404d87 | 27753fce |
| Risk | 68145701924ebb7eab22c51542aeb80ab81b4cde5e054cd9b7ded3e10caafbfc | b479fe20 |
| Memory | 25a644f2ffe35ea87f994d01cc9af93dd9c8ed181ecedb437a1d0b6c9da4147d | 6dca2b97 |
| Orchestrator | 722e34f485fa1e17b73305d217cb1e8dd2f5369c16b474e9a027fb6a33d6193f | c3059654 |

All four image digests equal the previous V6g preparation. This does not prove
which builds reused cache. The three reviewed diagnostic changes are host-side
consumers, not application image/source changes. The 43 app entries are unchanged.

## Limits and next proof

The controller's at-creation source/identity/configuration checks are attestations,
not new independently captured file streams, complete SDK proof or current
health/connectivity. Stopped configured-network evidence is configured_only,
not connectivity. Original-preservation claims come from the controller's checks
and result, not a separate native inspection. No private configuration values
are exported in these records. No software change or new/full test run was needed
for the operation; pure saved-record validation is the next verification lane.

Separate GATE verified saved/state equality, all seven receipt events, actual
ownership/identity/manifest contracts, current source maps and all four model
predictions without native operations. It accepted the saved evidence and real
IDs with risk and no blockers. No tests or full suite were run by the reviewer;
this was saved-file/hash/pure-consumer proof, not an implementation change.

Independent review SHA256:
e3c97007d3ea3bd1fb6d2363c4989f226604b01457660c93e6da7e3c448dd9ca.
Reviewer-authored actual_id_review.json SHA256:
fc18b363eb94a324e3d91500b967a7709ad70fa6635a100b2ab2bb1fda30a79f.
Both are in actual_preparation/. The latter is the existing strict five-field
external-review contract, not startup or cutover permission.

Parent checked all 58 input/output hash bindings and loaded the actual evidence
and review through ReviewedPreparation.load, yielding four accepted replacements
without native calls. Reviewed data/source/review records remain frozen; the
checkpoint hash in the review identifies its pre-closeout text.

The approved preparation plus actual-ID review scope is complete. Preparation
is consumed; cutover unused. Originals/storage were not intentionally changed,
no query or trading action occurred. Runtime remains INCOMPLETE. Next is the
existing offline runtime-packet/handoff workflow, bound to these actual IDs and
three reviewed host-consumer changes. No runtime packet or startup authority
was produced in this bounded operation.
