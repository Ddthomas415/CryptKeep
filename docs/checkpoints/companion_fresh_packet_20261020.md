# Fresh Preparation Packet Capture

Date:2026-10-20. Active role AUDITOR. Packet INCOMPLETE.

## What Was Captured

SHOWN at22:50:27UTC: all seven original research targets running, restart
policy `no`, restart counts0, same IDs as the prior recipe. Two sanitized metadata
reads matched exactly. Existing install-attempt labels were absent. The43 local
application source entries still match their frozen recipe hashes. This does not
show that the currently installed application sources are the reviewed new code.

Docker CLI SHA256 remains
`678271184175b40dfc4bd6f4582be00ae1538b0d1e031181f52ceedfae9af5fb`;
native signature verification passed outside the sandbox. Six read-only Docker
commands collected public engine version/commit, names/IDs, sanitized metadata,
attempt-label presence, verified network names/IDs and a final metadata read.
An empty temporary Docker config prevented use of the user's default credential
config. No raw environment values, tokens or labels were exported.

Evidence and reproducible dated recipe:
`../review_artifacts/companion_continuation_20261020/fresh_v5_capture_20261020/`
and sibling `capture_v5_readonly_20261020.py`. Capture SHA256
`0fa450f65997a8ace714babc6b514270eab308cd22f623a6e06177ab3c09fa1b`.
The recipe was independently checked ACCEPTED_WITH_RISK for read-only scope.
Its60second bound covers subprocess calls, not all local filesystem wall time.

## Why Preparation Is Not Ready

The actual engine reports **29.9.1 / b26fb77**. The existing backend permits
**29.8.2 / 8af9fe3** only. Its exact equality check would refuse this engine.
This is not proof that29.9.1 is incompatible, broken or unsafe; compatibility has
not been established. There is no evidence here that a recent update caused the
mismatch. No pin was weakened and no Docker repair/downgrade is recommended.

The new draft uses current baseline observations and a new attempt ID, but retains
`decision: INCOMPLETE` and an empty reviewer. It cannot pass the approved-packet
loader. Candidate SHA256:
`0ed18df8e95da122d2f00e31badeb17122fee2049609369c1dd819a832c6c108`.
Create options, source entries and expected replacement metadata were carried
forward from the prior recipe, not freshly certified from actual replacements.
Those actual metadata/identity checks remain due after authorized staging.

## Correction To Initial Interpretation

The capture shows legacy applications do not match `REQUEST_TIMEOUT_SECONDS=2`,
and memory lacks the reviewed read-only-startup flag. My initial claim that
preparation would preserve these defects was incorrect. The existing
`encode_environment()` applies its already-reviewed nonsecret overrides, including
both settings, while retaining credential values. Replacement creation already
uses that encoder. No new environment patch or scope decision is required.

SHOWN local proof: the existing exact-overrides/preservation test passed1/1 in
0.18seconds under isolated pytest. No credentials were read for that test.
The separate reviewer withdrew the same environment-blocker inference and kept
the actual engine mismatch as the concrete unresolved prerequisite. Disposition
and limitations are in the capture folder's `review.json`.

## Next Bounded Action

Verify the existing source-only, no-pull, network-disabled builder behavior on
the observed engine before considering a pin update. An actual build probe writes
a disposable local image and therefore needs separate operational authorization;
it must not start containers or alter the running seven services. Do not simply
replace the version literal with the observed value to make preparation pass.
Any pin/code change still requires targeted verification and independent review.

Current capture/packet assembly is complete for this read-only scope. Preparation,
native compatibility, actual replacement metadata, cutover, storage-preservation
and cited explanation delivery remain UNVERIFIED/INCOMPLETE. No image build,
container/service start/stop/recreation, storage change, migration, account,
scheduler, credential use or trading action occurred. No full test suite or
backtest was run; the single existing encoder test was the only test rerun.

Subsequent operator-approved single local COPY-only build probe succeeded and its
saved result was separately accepted WITH_RISK. See `companion_builder_probe_20261020.md`.
This adds minimal builder evidence, not automatic approval of the current engine
for the installer. Existing pin and INCOMPLETE draft remain unchanged; do not
repeat capture or the consumed probe merely because preparation has not run.
