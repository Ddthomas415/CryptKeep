# V6h Restoration Plan, October 26

Implementation role: ENGINEER. Risk: HIGH.
Separate GATE outcome: ACCEPTED_WITH_RISK, source-only plan/capture wrapper only.
Runtime INCOMPLETE. This is an offline plan and source/capture wrapper, not
authorization to inspect Docker or change services.

## Objective and evidence

Restore the existing explanation path and verify one genuine cited-evidence
request, without redesigning the platform or changing trading. The next action
is a separately authorized sanitized baseline capture, not a blind cutover.

SHOWN from local files: the accepted diagnostic repair changes only three host
consumers relative to V6g: companion_evidence_checks.py, companion_installer.py,
and companion_runtime_adapter.py. Two are in the 13 preparation consumers; all
three are in the 20 runtime consumers. All 43 application source entries and
application recipes match the historical manifest. This does not establish
current installed source, image availability, compatibility or service health.

The saved V6g receipt failed verification and reports configuration recovery,
not exact restoration. Its first verifier failure remains UNVERIFIED. Local
V6g preparation/cutover consumption markers exist; proposed V6h markers do not.
These are local ownership checks, not daemon observations. Removed replacement
IDs reported by that receipt are not reused. No current baseline is invented.

Artifacts: docs/review_artifacts/companion_integration_inputs_v6h_20261026/.
refresh_sources.py binds the accepted repair review, preserved report and V6g
source/manifest/failure records. It verifies every unchanged source and permits
only the three exact reviewed deltas. source_refresh.json is an INCOMPLETE
source-only proposal: baseline, new IDs and images remain null; all operation
authorization fields are false. It is deliberately not an installer Plan.

The existing V6g source/capture helpers cannot simply be rerun: their old pins
are stale and their output directories are historical. The new capture wrapper
retains the old capture function's AST except its temporary-directory prefix;
its package-local source proposal/output path now points to V6h. Existing
metadata projection/runner, Docker transport, installer and all historical
packets are unchanged. No new service-control mechanism is introduced.

## Staged execution proposal

1. Baseline, requiring separate operator authorization. Run exactly two
   sanitized metadata inspections of the seven original IDs in the historical
   manifest: timescaledb, qdrant, minio, audit-log, risk-stub, memory and
   orchestrator. Verify the CLI file digest before any command. Use the existing
   capture format, explicit socket, temporary empty CLI configuration and a
   PATH-only child environment. No environment values, credential reads, logs,
   application queries, network repair, start/stop, builds or deletion.
2. Offline reconciliation. Preserve both raw sanitized observations and their
   hashes before parsing. Equal complete selected fields are only evidence
   READY_FOR_INDEPENDENT_REVIEW, not acceptance of current identities or health.
   Compare names/IDs/images, state, configuration, mounts, network projections
   and restart fields with the historical constraints. Review app start-time
   changes attributable to rollback; any other material drift needs explicit
   disposition. Do not turn missing fields or fallback rows into a baseline.
3. Stopped preparation, not authorized here. Adapt the existing input derivation
   and preparation recipes to an accepted fresh baseline/current consumers.
   Separately authorize one preparation action for four stopped replacements;
   retain original apps/storage and do not start replacements. Reuse images only
   if the existing controller verifies them; no availability is assumed. Review
   actual created IDs and at-creation source/configuration evidence afterward.
4. Offline packet/handoff. Reuse current loaders, policy meanings and original
   image/SDK provenance without upgrading inherited evidence to fresh capture.
   Bind actual new IDs, the three reviewed consumer hashes and the unchanged
   question/archive/witnesses. Obtain independent applicability review and
   default-inert verification. No policy approval or runnable handoff is
   manufactured from this source-only proposal.
5. Runtime, not authorized here. Only after the above evidence and explicit
   approval, run one reviewed handoff with its existing 600-second controller
   (180 reserved for recovery), separate ten-second CLI/token-source checks,
   no automatic retry/reset and existing fail-closed checks. Reuse the internal
   token privately in memory; no display, persistence or new credentials.

The proposed future label is workerprep20261026v6h. It is not reserved by this
work and must be checked again immediately before any authorized action. No
old marker, receipt or consumed attempt may be reset or overwritten.

## Exact next command, NOT authorized or run

UNKNOWN_ENV for daemon state; VERIFIED_ENV only for offline file bindings and
synthetic tests. Following independent review and explicit two-read approval:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6h_20261026.capture_baseline --capture-once
```

Two inspections maximum, each at most ten seconds and limited by the remaining
30-second capture budget measured from function entry. No automatic repeat on
error, timeout, missing target or differing payload. The metadata-phase alarm
does not bound initial offline file preflight or final receipt persistence;
this is not a whole-process 30-second guarantee. Default invocation without
the exact action flag performs no capture, CLI read or source refresh.

Expected local effects of an authorized capture: a temporary empty CLI-config
directory and a new actual_baseline/ containing sanitized capture_1.jsonl,
capture_2.jsonl if reached, and baseline_observation.json. Failed parsing keeps
the raw bytes. An existing output directory is refused, never reused. No live
capture or actual_baseline directory was created while preparing this plan.

## Acceptance, recovery and limits

Health, connectivity, retrieval identity/body hashes, citation traceability,
topical support, causal limits and usable dashboard response remain separate
checks. Complete success requires the normal dashboard/companion transport,
normalizer and asset guard; non-static provider, execution disabled, no fallback
substitution and all five evidence checks true. Diagnostic stage/code cannot
override false checks. Do not change the question or witnesses to pass.

A metadata read has no service rollback; retain failure evidence and stop.
Future preparation/cutover retain existing owned cleanup/original restoration,
not guaranteed exact recovery. Only full success permits leaving replacements
running. Persistent logs/audit writes can survive rollback. Storage volumes,
data, trading, risk, schedules and accounts remain untouched. No migrations,
recreation of storage, document ingestion or external recipient is added.

No material assumption substitutes for current runtime evidence. Current
original status, exact configuration, image availability and health are unknown.
No profitability or trading-readiness claim follows from restoration.

## Offline proof and handoff

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6h_restoration_plan.py
```

SHOWN parent result: 22 passed in 0.51 seconds, no warnings. The first run also
passed all 22 but exposed a runpy test-harness warning; removing the already
imported test target from sys.modules before its default-path test removed that
warning. No production behavior changed for it. Tests use
synthetic CLI/metadata in temporary directories under operation tripwires.
The actual module default also exited zero with exactly actions_executed false
and state INCOMPLETE, saved in inert_default.json. This is default-path proof,
not permission or installed-runtime verification. No full suite ran.
No baseline, stopped replacement, token reuse, startup or query is performed.
Separate GATE reviewed the exact source refresh/capture delta and accepted it
with risk and no implementation blockers. It independently reproduced all 22
tests in 0.51 seconds without warnings, source proposal byte equality and wrapper
AST parity. Parent read the complete independent_review.json and checked all
55 bound hashes before this documentation-only closeout. Reviewed source/tests,
proposal/report and earlier evidence remain unchanged; the checkpoint digest
in the review identifies the pre-closeout document, not this status update.

The offline objective is complete. Next is explicit authorization for the two
read-only baseline inspections, not startup or preparation. All later stages
remain unimplemented/unverified in V6h; this is not a completed runtime packet.
