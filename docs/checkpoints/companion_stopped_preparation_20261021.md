# Stopped Replacement Preparation

Date: 2026-10-21. Active role: ENGINEER. Risk: HIGH.
Actual preparation: READY_FOR_INDEPENDENT_REVIEW. Runtime: INCOMPLETE.

## Result

SHOWN: one operator-authorized preparation invocation completed with exit0,
preparation_complete=true, services_started=false and originals_interrupted=false.
Four local source-only application images and four never-started replacements
were created. No application startup, original interruption, cutover, migration,
HTTP query, account, scheduler or trading operation was performed. This is not
restoration of the explanation service.

VERIFIED_ENV: six reviewed controller file hashes,43 application source entries
and the exact accepted manifest matched before execution; attempt was unconsumed.
The reviewed command performed its own native baseline, CLI/engine, image/source
and ownership checks. Existing service configuration was handled transiently by
the reviewed child transport/encoder; no secret values were printed or persisted
in the public receipt. New stopped containers retain their required configuration.

Executed once from the repo root with environment limited to PATH and bytecode
disablement:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B \
  -m scripts.research.companion_prepare \
  --manifest docs/review_artifacts/companion_continuation_20261020/reviewed_preparation_manifest.json \
  --reviewed-manifest-sha256 3b6f785ca1dd732e307aa83b30dcea2a5d2d9379d57af06a4afaa3774df94635 \
  --execute-preparation
```

This records the consumed invocation, not a command to repeat. The durable attempt
marker is retained. No automatic retry or image/cache pruning was performed.
The controller budget was300seconds including120seconds recovery reserve; local
pre-controller filesystem work is not covered by a total CLI wall-time claim.

## Actual IDs

All four state=created, started=0001-01-01T00:00:00Z, restarts=0, policy=no.
Names append `-staged-f4e189b78ccc48acb8b92f20c4627f51` to the logical name.

| Logical Name | Container ID |
| --- | --- |
| phase1-audit-log | bd12bc18068bc646b2726e047dc05166beba67c22b7b2afc03f0e791fed5111d |
| phase1-risk-stub | 6a4b4246e6abf66dc186505e4f2eb00c85d19cc14bb8e41d8b1389468fbbb3d9 |
| phase1-memory | 2db66f6e38719cc8f2a435d718b2d9f3cd9614fd83076a4fd09182a9cdd49462 |
| phase1-orchestrator | 05a288361742d9b3a26d6e0f69b7cf10d3e3e17672e01c61c9bfad072a7289ac |

The saved evidence binds full image IDs, source-verification completion,
attempt labels and actual stopped metadata. Configured-only network evidence
does not claim active connectivity. Staging-name/alias fingerprints are not
interchangeable with modeled final logical-name fingerprints.

## Verification and Evidence

One additional bounded read-only inventory through the reviewed backend and
30second child executor completed exit0. At2026-10-21 12:15:38UTC (08:15:38EDT),
all seven original snapshots equaled the reviewed baseline and all four stopped
replacement snapshots equaled the published preparation evidence. This is an
endpoint metadata comparison, not proof of unchanged database contents or absence
of all transient changes. No lifecycle or credential read was used for this check.

Private runner evidence directory:
`.cbp_state/runtime/companion_preparations/f4e189b78ccc48acb8b92f20c4627f51/`.

| Artifact | SHA256 |
| --- | --- |
| evidence.json | 78726c0b834778934368713e55a7496a91249d17323e3d43c9052895a5e4d8de |
| receipt.jsonl | a9efa72fe64838c4f273e3b4a37b34ffe06b9de00bc7c8cbba436db73af0404e |
| post_preparation_inventory.json | e33756cfec67a517aff01fcb0352181006be185ee487fb8fc9ab497bd7d4cc75 |

The public inventory is under
`docs/review_artifacts/companion_continuation_20261021/`.
The receipt ends with preparation_evidence_published bound to the evidence hash.
No source code changed and no new pytest/full-suite/backtest ran during this
operational attempt. Prior synthetic verification remains separate evidence.

## Remaining Boundary

Separate GATE is reviewing actual saved IDs, receipt and post-inventory. Until
that review completes, no actual-ID acceptance is inferred. SDK/import startup
policies, connectivity, health, storage contents and real cited explanation
delivery remain unverified. A separately reviewed and authorized bounded cutover
is required before originals may be interrupted or replacements started.

## Actual-ID Disposition and Diagnosed Gap

Separate GATE ACCEPTED_WITH_RISK for the stopped actual-ID bindings only. Review:
`docs/review_artifacts/companion_continuation_20261021/preparation_actual_id_review.json`,
SHA256 `66f0ec73f6362fc97270901a1b6f9b2723100548503e8c33c9c3453bcde88fc7`.
Its separate `preparation_actual_id_disposition.json` retains limitations and
explicitly does not approve runtime or cutover. Parent independently loaded the
exact review/evidence under the unchanged ReviewedPreparation contract: PASS,
four bound replacements, no operations. The pending-review statement above is
superseded for these stopped IDs only.

The reviewer confirmed all four actual configured digests differ from modeled
final digests and could not attribute the difference from Snapshot hashes alone.
Do not dismiss this as staging aliases without field-level evidence.

One sanitized read-only inspection then captured the four created IDs with the
existing fixed metadata formatter. It emits known environment comparisons as
booleans, not raw values. The initial inspection result could not cross the
ProcessExecutor's JSON channel as bytes; a corrected wrapper decoded public JSON
inside the bounded child. This repeated a read-only inspection, not preparation
or lifecycle work. Diagnostic succeeded at12:20:52UTC/08:20:52EDT; all four
configured digests still equal the published evidence.

Artifact: `docs/review_artifacts/companion_continuation_20261021/staged_metadata_diagnostic.json`.
SHA256: `03ffaa2dd4e4ee3c6d42383c41df4e04c3e797382416699134aa9661e3bf748e`.
SHOWN fields differing under the unchanged comparison are networks, dns and
extra_hosts. Actual dns/extra_hosts are null; the frozen models use empty lists.
Environment flag lists match, not merely their values or reordered equivalents.
Offline clones changing only those two empty fields to lists and staged aliases
to planned logical aliases reproduce all four exact modeled final fingerprints.
This is an offline explanatory projection, not actual final-state verification.

No gate, prediction, source, manifest, actual evidence or runtime pin was changed.
The unchanged strict gate does not yet accept the projected final metadata with
these representations. Separate review of the diagnostic is pending; the next
engineering scope is a narrow, backward-compatible representation treatment with
tests and independent review, preserving actual evidence and reusing these IDs.
Do not rebuild, recreate or start replacements to work around the mismatch.
The separate operational cutover entry point and final runtime pins also remain
to be completed/reviewed; accepted low-level APIs are not an execution command.

Separate GATE subsequently ACCEPTED_WITH_RISK for the diagnostic explanation,
independently reproducing4/4exact modeled fingerprints and exact flag order.
Receipt: `docs/review_artifacts/companion_continuation_20261021/metadata_diag_review.json`,
SHA256 `9458605823505985f2756c1a63fa4084508297d3c1f6cb48057f4cf4a8a9b50b`.
This closes the field-level cause question, not approval of normalization or
cutover. No native call or gate/evidence/pin change was made by the reviewer.
