# Actual V6h Baseline Capture, October 26

Implementation role: ENGINEER. Risk: HIGH.
Separate GATE outcome: ACCEPTED_WITH_RISK, saved baseline/input recipe only.
Runtime INCOMPLETE; no preparation action authorized.

## Authorization and operation

The operator approved the preceding request for two sanitized read-only metadata
inspections of the seven original research containers. This did not authorize
preparation, credential reads, application queries or service changes.

Before invocation, 54 nonhistorical source-plan review bindings matched and the
V6h actual_baseline output directory was absent. The review's checkpoint hash
was explicitly historical pre-closeout text, not a current equality claim.

Exactly one invocation, tool execution exit zero:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6h_20261026.capture_baseline --capture-once
```

SHOWN: native_inspections 2, selected_observations_equal true,
metadata_complete_for_selected_fields true, elapsed_seconds 0.5286767920479178,
state READY_FOR_INDEPENDENT_REVIEW and no failure category. Capture window:
2026-10-26 22:03:32.167142 to 22:03:32.695798 UTC. There was no repeat.
The wrapper checked the pinned CLI file before inspection. Its two native
calls were read-only, not CLI image/build/start/query operations.

Both saved raw sanitized files have SHA256
476ac56111ba2e54d4fdad8de3c1e82a1a03fec923cc0a00c6528bae824e9a2a.
baseline_observation.json has SHA256
685af8cea00eec5d7026afbf585d7e588620e0c69eb70a56a3393decf443d129.
Exact bytes were saved before parsing and independently checked against each
embedded observation and raw hash during local reconciliation.

## What the saved evidence establishes

All seven original IDs/images/names matched the historical manifest and were
running in both reads, with restart policy no and restart count zero.
Existing network/configuration/snapshot helpers reproduce the same selected
configuration fingerprints, foundation, network evidence and mount metadata.
Only four Snapshot fields differ from the V6g pre-attempt baseline:

- audit-log started: 2026-10-26T20:37:05.615888964Z.
- risk-stub started: 2026-10-26T20:37:06.534901839Z.
- memory started: 2026-10-26T20:37:07.442325506Z.
- orchestrator started: 2026-10-26T20:37:08.46605384Z.

All storage Snapshot fields match unchanged. The four start-time changes are
consistent with the earlier receipt's four restart_original_intended events;
that receipt has no fresh timestamps, so precise causal attribution is not
claimed. Docker restart counts of zero do not establish no manual restarts.

This is selected-field equality at two sequential instants, not atomic or
continuous state proof, full configuration capture, mount-content identity,
current application health/connectivity or a working explanation query.
It narrows the prior recovery uncertainty without relabelling the old rollback
as exact restoration. The old verifier failure remains UNVERIFIED.

## Offline reconciliation and candidate

Reused V6g derive_inputs.py with only its source-plan review path/hash and output
schema label changed for V6h. Original validation logic, model hash, Snapshot
projection and drift refusals remain unchanged. It requires both raw hashes,
pair equality, complete metadata, timing/CLI/source-refresh bindings, exact
historical identity/configuration and only app started-field changes. Other
drift or a storage timestamp change refuses; no unobserved fields are inferred.

Generated candidate_manifest.json and provenance.json from the saved capture.
Candidate keeps decision INCOMPLETE and empty reviewer. Provenance records the
three accepted host-consumer deltas and no new container/image IDs, with all
operation-authorization fields false. It is not an approved preparation input.
The source-only proposal and all historical V6g artifacts remain unchanged.

VERIFIED_ENV local offline verification:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6h_current_inputs.py
```

SHOWN: 11 passed in 0.38 seconds. Actual candidate/provenance reproduce byte
exactly; synthetic ID/state/command/restart/storage/pair/hash/CLI/timing/source
drift refuses. Accepted decision/reviewer exists only in a temporary synthetic
test fixture to exercise the real Plan loader, never in the published candidate.
No full suite or stale historical packet rerun.

## Next boundary

Separate GATE verified raw pair/reconciliation, exact derivation delta and
original selected identity/configuration, accepting only the limited app
timestamp disposition. It reproduced candidate/provenance and all 11 tests in
0.36 seconds. Review: actual_input_review.json. Parent verified all 63 bound
hashes and compared all seven accepted Snapshot records to the candidate before
this documentation-only closeout. Review-bound checkpoint digest identifies
the pre-closeout text; source/tests/candidate/provenance/observations are frozen.

The review expressly permits exporting reviewed_preparation_manifest.json with
only decision/reviewer changed to its exact supplied values. Exported manifest
SHA256 d11fccb5e4f7c46e7d726704c9b75c400a1482eab5d1b840027d876a5837f047
matches the review's expected digest and loads through the real Plan parser.
manifest_export.json binds the independent review by finalized external SHA256,
preserving the original INCOMPLETE candidate. No self-issued policy approval.

Reused the existing validate_default.py byte-for-byte in the V6h artifact folder.
Under backend/native/socket/subprocess/reservation/lock/pipe tripwires the actual
companion_prepare.main default exited zero, opened only the reviewed manifest
read-only, made zero external-operation calls and left both markers absent.
inert_validation_receipt.json records actions_executed false/startup false and
the existing 300-second controller/120-second recovery reserve. This is parent
default-path proof, not an independent runtime result or preparation execution.

Capture/reconciliation/input review objective complete. Next is separate
operator authorization for one stopped-preparation action using the accepted
inputs; current preflights remain mandatory and can refuse subsequent drift.
No stopped replacements were created or services started by this work. No token values
were accessed/exported, no application query was sent, no service/image/volume/
trading/risk/schedule/account operation occurred. The only native actions were
the two authorized metadata inspections. No marker was reserved, reset or reused.
