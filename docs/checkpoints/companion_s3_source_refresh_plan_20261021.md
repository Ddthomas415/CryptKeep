# S3 Repair: Fresh Stopped-Replacement Plan

2026-10-21. Active role ENGINEER. Risk HIGH: future application preparation and
private configuration copying. Current scope is offline derivation/review only.
READY_FOR_INDEPENDENT_REVIEW. Preparation/startup/cutover not authorized here.

## Choice and Consequence

Reuse the existing unchanged v5 preparation command and four-application contract.
Only memory main.py changes, but existing Plan.load, preparation loops and
ReviewedPreparation require all four applications under one attempt. Adopting
three old staged IDs would need new ownership/label/review rules. Do not add that
workflow merely to save three stopped-container creations. Independent AUDITOR
Plato confirmed no supported one-application path was missed.

Consequence of a later authorized run: four build invocations and four NEW stopped
application containers. Unchanged source sets may reuse image cache; identical
image IDs are not promised. Preserve all seven originals and the old four staged
containers. Do not edit their files, replace old approvals, or erase consumption
markers. No extra storage services, published routes or running applications.
Creating stopped containers does retain their copied service/storage credentials
in Docker configuration, as in the already reviewed preparation path; no credential
values may be printed or exported to this public packet.

## Exact Offline Delta

Source manifest: preparation_reconciled_manifest.json, SHA256
b9594f55b7d409d5815ea318de68c0391943dcafe919326ebedb143821627b11.
New attempt: s3refresh20261021c1eaae5a. No reservation has been made.

The candidate changes only attempt, decision/reviewer (cleared pending review),
and memory's main.py source hash:
35fc51165e44dba1ab8d28e783285f51f392b01f814096f3950ce720995504a3
to c1eaae5a5e1712ad926f556fdaf3195442a2b6e354059542748a429945a36228.
All43 current source entries are checked;42 prior entry hashes remain unchanged.
Three application source sets, seven original ID/image/metadata bindings, CLI,
network contract, modeled final metadata and creation options remain unchanged.
Both deferred startup policies remain FALSE; no SDK/startup approval is inferred.

The baseline is the accepted saved observation2026-10-21T17:47:49Z, not today's
live inventory. Existing preparation must recheck exact originals, network,
CLI/engine, all source bytes and parent images before effects; any change refuses
the attempt, not automatic baseline refresh or retry. Backend selection excludes
the old four staged IDs from the new attempt; it never adopts or cleans them up.
Its preservation checks cover the original seven plus new owned stages, not an
independent before/after proof of the old staged set. Record that distinction in
the actual outcome rather than claiming more than the controller checks.

## Artifacts and Verification

Folder: docs/review_artifacts/companion_continuation_20261021/.
- derive_s3_refresh_plan.py:89c39687f307de4c2e040c253a491756af67bcaaa455a86592e4992217981ee3.
- tests/test_companion_s3_source_refresh_plan.py:d41a632162a7802a4cc8f26adfc2d43e884dc800b72ab06c7760b6b3456dd379.
- s3_source_refresh_plan/candidate_manifest.json:cebb77acd48856bcc3ff4bd9d2cf379e855cc020d7792ce68d40fb39993a3550.
- s3_source_refresh_plan/provenance.json:2347bab33543ae5ee4dba40003bb3b83f1cfc3e870d4db75528be444a48ac628.

VERIFIED_ENV offline only. Generator ran once with empty host environment, wrote
candidate/provenance only, native_operations=false, one changed source. Candidate
has decision INCOMPLETE and blank reviewer; the executable loader refuses it.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider \
 -q --tb=short tests/test_companion_s3_source_refresh_plan.py
```

SHOWN7passed0.23s, exit0. Exact delta and preservation, failed draft loading,
unchanged deferred policies, changed inputs/repair refusal, and rejection of old
preparation evidence under the new attempt are covered. An explicitly synthetic
in-memory approval copy checks loader shape only; no approval was written by the
generator or tests. Accepted S3 tests were not rerun. No full-suite/native result.

## Proposed Operational Boundary After Review and Authorization

Use scripts/research/companion_prepare.py unchanged with the new independently
reviewed manifest/hash. Default invocation is inert; --execute-preparation is
ONLY for a separately authorized one-time run. Existing shared lock, exclusive
per-attempt reservation and300second controller budget/120second recovery reserve
remain unchanged. Local pre-controller I/O has no absolute wall-time guarantee.

Preparation builds from pinned local original image IDs, source-only COPY, no
pull/RUN/network build work; privately copies existing environment/labels using
the reviewed encoder and creates the four application stages without starting
them. Original storage and applications stay running. Health checks do not run
on never-started stages. New IDs and image hashes are unknown until that run.

Failure: retain receipt/consumed marker and report exact failure stage. Existing
owned-only cleanup may remove NEW acknowledged unpromoted containers; never stop
originals or remove old stages/volumes. Images/cache, private temporary evidence
and logs may remain. Unresolved ownership/cleanup ends INCOMPLETE, not a retry or
forced deletion. Success: leave four new stages created/never-started, publish
actual-ID evidence and obtain independent review before runtime packet assembly.

No creation, build, lock/reservation, token/credential read, storage query, service
change or operation ran while preparing this plan. This is not authorization to
deploy, query the application, change a campaign or trade.

## Independent Disposition and Inert Validation

Separate GATE ACCEPTED_WITH_RISK prospective preparation inputs only, no findings.
Receipt: s3_source_refresh_plan/preparation_plan_review.json. Independently7tests
passed0.19s and all43 current source hashes/full7 saved baseline projections match.
The preserved candidate remains INCOMPLETE. Reviewer published a separate accepted
derivative changing only decision/reviewer:

s3_source_refresh_plan/reviewed_preparation_manifest.json
SHA256dd7b537aa39d2f5cbccebf41a20fadc7e2ae8e22ebe20063daf7417286dddb6d.

Parent read the full receipt and ran the unchanged command without execution:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B \
 -m scripts.research.companion_prepare \
 --manifest docs/review_artifacts/companion_continuation_20261021/s3_source_refresh_plan/reviewed_preparation_manifest.json \
 --reviewed-manifest-sha256 dd7b537aa39d2f5cbccebf41a20fadc7e2ae8e22ebe20063daf7417286dddb6d
```

SHOWN exit0, actions_executed=false, startup_authorized=false; exact fresh attempt
and300/120second budgets reported. No lock, reservation, backend or native call.
This closes the offline packet task. Existing prepare command hash remains
89b60b67a6204a83ad045edc91874b9e828c023fe0d094cda6d7c61c56e7bfd1.

Reviewer clarification: creation options do retain configured loopback publication
bindings; only active routes/listeners are absent while containers never start.
Neither this offline review nor the preparation controller independently measures
old-stage listener state. Do not replace this distinction with a broader claim.

The next operation needs explicit authorization: append --execute-preparation to
the exact command above for ONE fresh preparation-only run. Four builds/four new
stopped application IDs; no original interruption, startup, query or cutover.
Old preparation/capture consumption markers and old four stages remain preserved.
After that authorized run, independently review actual IDs and installed bytes.
