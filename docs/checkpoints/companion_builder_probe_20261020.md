# Approved Local Builder Probe

Date:2026-10-20. Independent GATE: ACCEPTED_WITH_RISK for this saved probe only.

## Result

SHOWN: the one approved COPY-only build succeeded on engine29.9.1/b26fb77 in
5.715seconds. The local audit-service base had no OnBuild triggers. The new image
retained the exact base layer prefix and added one layer. All seven selected
research-container metadata records matched before and after; engine identity
also matched before and after. No application startup or cutover was performed.

Retained untagged image:
`sha256:99e59b439903f0148e3d781467631fdea82a033c7d68e52572a87a064c2b0cac`.
It is not an application replacement and was not started or removed. Docker may
retain build cache/internal artifacts; no prune or existing-image removal ran.

## Scope and Evidence

Operator approved this single60second probe explicitly. The dated recipe was
independently checked ACCEPTED_WITH_RISK before execution. It checked CLI and
capture hashes, used an empty temporary Docker config and the shared install
lock, verified an existing local base, rejected OnBuild triggers, then invoked
one legacy-builder `build --quiet --pull=false --network=none -` with FROM/COPY
only. The context contains a public nonce text file, not research/private data.

Recipe SHA256:
`2c0f26d52cfdf5e7e3109d4f4183fd0bd5b7bad22a36876ad45330d92927a3ac`.
Output folder: `../review_artifacts/companion_continuation_20261020/engine_build_probe_20261020/`.

Artifact hashes:

| Artifact | SHA256 |
| --- | --- |
| report.json | df295bbeee773f6b951e3c0bde6aab2405ae191ef56bfa1dd6045abc5e50a810 |
| context.tar | e2fb1c2bd96a80c46bcea4884c87a9ccb9533ca53d6faf58f04882794f6ecac6 |
| events.jsonl | 643beab175df5ecd03e7386036133010fa9c0d316cb9bdc9fd39c40785656811 |

The source recipe, actual context and receipt are preserved for independent
review. The output directory is exclusive; do not repeat this consumed probe.
No automated retry occurred.

## Limits and Next Step

This proves the minimal local COPY-only builder path, not complete installer,
SDK/import, application configuration, stopped-container metadata, cutover,
storage-data preservation, health or cited explanation delivery. The selected
container metadata comparison is not a database-content comparison.

`--pull=false` with a verified local full-ID base requests no image pull;
`--network=none` is not host-wide daemon egress isolation. No network-traffic
telemetry was collected. Timeout bounds client execution and cannot guarantee
daemon-side cancellation; unknown outcomes would require inspection, not retry.

The existing installer version pin remains29.8.2/8af9fe3. It was NOT changed or
bypassed within the installer. The standalone compatibility experiment used only
the separately authorized build. Next is a narrowly scoped pin/compatibility
change with targeted verification and separate review, rather than reinstalling
Docker or treating this probe as deployment approval. Actual preparation and
cutover remain unperformed and require their existing separate authorization.

No credentials, accounts, scheduler, trading rules or risk settings were accessed
or changed. Only the approved image build and local public proof artifacts were
created. No full test suite or backtest ran. Actual-evidence review is pending;
no same-thread acceptance is inferred.

## Independent Result Review

Separate GATE accepted the saved minimal COPY-only result ACCEPTED_WITH_RISK,
recomputed all artifact hashes, inspected the tar and verified the layer prefix
and8-to-9 layer count, unchanged seven-target snapshots and engine, absent OnBuild
and one acknowledged build. Receipt: `review.json` in the output folder.
No rerun or native call was made by the reviewer.

Retained limits: the pre-build image-ID inventory was not saved, so the new-ID
claim relies on the recipe's executed guard. Endpoint snapshots cannot prove
absence of all transient changes. Neither limit warrants repeating the consumed
probe. The result does not approve installer compatibility, SDK behavior,
preparation, cutover or a pin update. The next code step must be separately scoped
and reviewed; no additional native operation is authorized by this result.
