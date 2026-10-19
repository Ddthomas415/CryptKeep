# Companion repair installation and rollback proposal

Active role: DIRECTOR. Risk: HIGH. State: READY_FOR_INDEPENDENT_REVIEW.
Planning only. Installation and runtime retry are NOT AUTHORIZED.

## Decision and evidence

SHOWN: the21:26UTC read-only refresh found seven stopped targets with unchanged
IDs/images and five unchanged installed source samples. Four samples differ from
the repaired local source. See `companion_compatibility_refresh_20261016.json`.
The local `Dockerfile.service` uses `FROM python:3.11-slim`, upgrades pip,
reinstalls requirements, then `COPY . /app`. Requirements include an open-ended
OpenAI version. A normal Compose rebuild is therefore not the minimal
dependency-preserving repair. No build was executed to test that observation.

Chosen proposal: four source-only derivative application images, each based on
its own exact existing local image ID. Do not modify the existing containers in
place or use a blanket Compose rebuild. Do not install new dependencies, pull a
base image, or execute RUN instructions. Use a private minimal build context of
explicit reviewed files only, never the whole repo, `.env` or credential files.
UNKNOWN_ENV: actual builder behavior, cached-image accessibility and installed
dependency compatibility. If these cannot meet the restrictions, stop and revise
the proposal; do not silently substitute a networked rebuild.

## Exact replacement boundary

| Target | Proposed operation |
| --- | --- |
| phase1-audit-log | Source-only derivative of its recorded image; replacement kept stopped |
| phase1-risk-stub | Source-only derivative of its recorded image; replacement kept stopped |
| phase1-memory | Source-only derivative of its recorded image; replacement kept stopped |
| phase1-orchestrator | Source-only derivative of its recorded image; replacement kept stopped |
| phase1-timescaledb, phase1-qdrant, phase1-minio | Keep original containers, image IDs and all data mounts unchanged |

All four application targets need the reviewed common-source profile, not just
the two with changed sampled main modules. File selection must use the existing
offline source manifest plus the adapter's required source coverage. Unreviewed
recovery modules/SDK changes are not approved merely by inclusion in the working
tree. The two manifests are evidence inputs, not complete deployable bundles.

This changes the prior no-build/no-recreation boundary and requires explicit
permission. It does not grant startup permission. No parser, market, news,
archive or gateway container is added, replaced or started by this scope.

## Before any installation

1. Preserve reviewed source hashes and the original seven-target inventory.
   Verify Docker archive reads reflect image versus writable-layer provenance:
   a derivative starts from the image, not any unrecorded container-layer changes.
   Inventory differences must be resolved, never discarded as incidental.
2. Review installed SDK/startup helpers and required binary availability via
   separately authorized read-only evidence. No dummy review records. A missing
   MinIO curl/shell or incompatible SDK is a separate demonstrated gap, not
   permission to replace storage images or install packages.
3. Establish secret-safe recreation wiring and effective-config comparisons.
   Do not print/export raw inspect, rendered Compose configuration, `.env`,
   tokens or secret hashes. Do not rotate credentials. The existing anonymous
   token handoff is not a complete recreation/credential-wiring tool.
4. Freeze the exact application-file build context and its hashes, including
   normal-route dependencies. Confirm the read-only `/repo` mount and import
   precedence cannot substitute unreviewed dirty source. Preserve the mount's
   normal capabilities; do not remove it without a scoped decision.
5. Review the concrete installation commands/controller before executing them:
   one preparation attempt,300s overall limit,60s per operation, no retries.
   The existing query controller does NOT implement image/container replacement.
   No executable installer or safe-to-run shell sequence is supplied here.

## Installation sequence, only after separate approval

Prepare and inspect the four derivative images before changing container names.
Record parent/new image identities and installed source hashes; never infer
success from a tag or build exit status alone. Preserve old image references;
no prune, image deletion, volume removal, Compose down or orphan cleanup.

Require all seven original targets still stopped. Preserve each old application
container as a stopped rollback object under a collision-checked temporary name.
Renaming can retain network aliases: explicitly detach the retained applications
from their network only under installation authorization, after recording all
endpoint/alias metadata needed for rollback. Do not leave old aliases competing
with replacements. Do not delete the old application containers.

Create the four replacements under the original names, stopped, on the existing
network with the same required aliases, loopback ports, mounts, restart policy,
ownership and credential references. Apply the restricted probe configuration
explicitly: no trading/model, read-only memory startup, exact internal origins,
bounded requests and bytecode disabled. These are proposed configuration changes,
not facts about current settings. Do not use Compose up, which would start them.

Independent review identified a lifecycle gap: never-started replacements are
`created`, not `exited`. The current controller/adapter requires `exited` targets.
Before implementation approval, a separately reviewed offline correction must
define admission, ownership and cleanup for pinned `created` application targets,
while retaining the original storage-target requirements. Do not start/stop new
containers merely to manufacture an `exited` baseline, or loosen state checks
without tests. No such source correction is implemented by this plan.

Inspect and independently review the new IDs/images/source/configuration and
network ownership. Reissue real installed-policy pins and topical witnesses for
the new identities; never reuse the old identity acceptance or synthetic fixtures.
End installation with all seven targets stopped. Startup/query needs a separate
decision under the existing600s controller contract; do not run it as an install
health check. Ordinary research routes remain present; read-only startup can
disable ingestion in this session, which must be disclosed, not made permanent
or called full research-platform restoration.

## Rollback and irreversible effects

Before the first rename, failure leaves original containers untouched. Afterwards,
remove only this attempt's stopped replacement containers, without volume flags;
restore original names and exact recorded network endpoints/aliases, then verify
the original seven IDs/images/stopped states/mounts. Never stop or remove an
unexpected running or ambiguously owned object. Partial rollback ends INCOMPLETE
with exact remaining objects recorded, not an automatic retry.

Image layers, build cache, daemon records and newly allocated container IDs may
remain. Rollback is not bit-for-bit daemon restoration. The later authorized
startup/query can write audit/storage metadata; restoring container names does
not reverse those writes. No data-volume snapshot or verified backup is claimed.

## Acceptance and limits

Plan proof: local Compose/Dockerfile/config/manifest/source-coverage inspection;
no Docker call, dependency install, tests, credentials or services in this stage.
Hashes of the inspected build inputs are recorded in the work log. Old evidence,
datasets, configurations and implementation source remain unchanged.

At most two assumptions: original images remain locally accessible; an approved
secure wiring mechanism can preserve existing credentials. Both must be verified
before installation. No operational commands are VERIFIED_ENV by this proposal.

Success of installation means four verified replacements stopped, three original
storage targets preserved, rollback objects retained, new pins independently
reviewed. It does not establish a working explanation or profitable trading.
Runtime remains INCOMPLETE. Stop here for independent plan review and the explicit
decision on this replacement scope; do not start another implementation cycle.

## Independent review disposition

Separate AUDITOR returned ACCEPTED_WITH_RISK for planning scope only, identifying
the created-versus-exited handoff above. It performed local reads, no tests or
runtime operations. This clarification retains the finding as a required
implementation prerequisite, not a resolved source defect. Plan handoff remains
READY_FOR_INDEPENDENT_REVIEW for any executable installation/lifecycle work;
the proposal is not an execution-ready runbook or installation approval.

## Authorized offline lifecycle correction, 21:31 UTC

Active role ENGINEER; risk HIGH. Implemented the separately approved correction
in `companion_existing_controller.py` and `companion_runtime_adapter.py` only.
The shared admission predicate keeps exited targets eligible as before, and
additionally permits created targets only among the four application names with
zero integer restart count and blank or exact Go-zero start timestamp. Restart
policy no, reviewed IDs/images/source/configuration, baseline recheck and explicit
runtime authorization remain required. Storage created state remains refused.

Start ownership now rejects a zero StartedAt even when it differs from a blank
baseline. Failed or ambiguous starts are not claimed as owned. Failure before
application startup leaves those created applications untouched; failure after a
confirmed start stops owned targets in reverse order. Their resulting exited
state is checked, not misrepresented as restoration of never-started state.
No removal/recreation, reset of start history or operational action was added.

Added controller/adapter regressions and expanded synthetic wiring across old
exited and new created application baselines. Prepatch selected tests:12 failed,
1 passed,118 deselected. Postpatch command:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q \
  -p no:cacheprovider tests/test_companion_existing_controller.py \
  tests/test_companion_runtime_adapter.py tests/test_companion_runtime_wiring.py
```

SHOWN:131 passed in1.30s. VERIFIED_ENV: local Python3.12.10, fake state/transport,
temporary receipts and local subprocess fixtures only. No Docker/network/service
request, real credentials, build, replacement, start/stop or full suite. This is
not installed compatibility or restoration proof. Changed-source hashes are in
`docs/review_artifacts/companion_created_lifecycle_20261016.json`; earlier manifests
are preserved as historical snapshots, not silently updated approvals.

Independent review requested for this narrow delta. Implementation handoff:
READY_FOR_INDEPENDENT_REVIEW. Executable installation/secret-safe recreation,
installed SDK/binary policy and new reviewed identity pins remain outstanding;
runtime INCOMPLETE and retry NOT GRANTED.

Independent lifecycle AUDITOR returned ACCEPTED for the specified offline delta,
with no concrete blockers, independently running the same131 tests in1.16s.
It confirmed restricted admission, unchanged storage requirements and retained
ownership/cleanup gates. It did not independently reproduce prepatch failures or
claim a Git-based old/new comparison of the untracked source. No source changed
after that review. This closes the demonstrated lifecycle source gap only; it
does not approve installation, actual startup or the explanation query.
