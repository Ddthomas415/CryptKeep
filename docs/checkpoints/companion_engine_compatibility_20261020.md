# Exact Engine Compatibility Update

Date: 2026-10-20. Active role: ENGINEER. Risk: HIGH.
Implementation status: READY_FOR_INDEPENDENT_REVIEW.

## Scoped Change

SHOWN: the installer builder gate now permits exactly these version/commit pairs:

- 29.8.2 / 8af9fe3 (existing support retained).
- 29.9.1 / b26fb77 (the engine used by the approved minimal COPY-only probe).

The change is an exact dictionary allowlist, not a version range or automatic
trust of the currently installed engine. Mixed pairs, extra or missing fields,
development suffixes and unknown versions remain refused before private
environment inspection or builds. The existing singular constant is retained
for compatibility with dated recipes; it still identifies the original pair.

Changed implementation: `scripts/research/companion_install_docker.py`.
Changed tests: `tests/test_companion_installer.py`.
No other builder, source, image, transport, environment or authorization gate
was changed in this delta. Earlier dirty-worktree changes were preserved.

## Evidence and Verification

VERIFIED_ENV: local `.venv` interpreter ran synthetic tests only. Both commands
use `./.venv/bin/python -B -m pytest -q -p no:cacheprovider`:

1. `tests/test_companion_installer.py tests/test_companion_staged_backend.py tests/test_companion_running_backend.py`
   - 382 passed in 2.29s.
2. `tests/test_companion_prepare_entrypoint.py tests/test_companion_staged_composition.py tests/test_companion_staged_update.py tests/test_companion_install_env.py`
   - 170 passed in 1.26s.

An initial command named nonexistent `tests/test_companion_prepare.py` and
collected no tests; corrected commands above completed successfully. This is
targeted verification, not a full-suite result or new native Docker proof.

Frozen SHA256:

| Artifact | SHA256 |
| --- | --- |
| backend | ca2e74fcf9d3869f7c3ed27e69721cd12615f41cc2687ea0844b314250814220 |
| test file | a302a1136e4392bbd7cca3f33b10f936ca14ba5066d3f3c624361450a48b9ab2 |
| earlier actual probe report | df295bbeee773f6b951e3c0bde6aab2405ae191ef56bfa1dd6045abc5e50a810 |

The actual probe and its independent review remain in
`docs/review_artifacts/companion_continuation_20261020/engine_build_probe_20261020/`.
They were not rerun or rewritten. The probe covered one base and one COPY layer;
it is not full native installer, application or cutover validation.

## Remaining Boundary

Separate GATE review of this frozen code delta is pending. No native commands,
builds, credential access, replacement creation, service changes, schedulers,
accounts or trading operations ran in this scope. The fresh v5 candidate remains
INCOMPLETE; this code change does not grant operational authority or approve that
packet. After code review, the next step is bounded offline review/reconciliation
of the existing preparation packet, then separately authorized preparation of
stopped replacements. Cutover remains a later, separately bounded decision.

## Independent Disposition

Separate GATE: ACCEPTED_WITH_RISK for this offline exact-engine delta only.
No actionable finding. The reviewer independently ran 17 focused tests
(91 deselected) in 0.41s and confirmed the frozen source/test/probe hashes and
unchanged authorization guards. Removing only this delta reproduced the prior
reviewed backend hash. Parent rechecked source/test hashes after review; unchanged.
Receipt: `docs/review_artifacts/companion_continuation_20261020/engine_compatibility_review.json`.
The pending-review statements above record the implementation handoff; this
disposition supersedes them for the code delta, not for the operational packet.
All native and full-system limitations remain. The next boundary is offline
preparation-packet review, not deployment or another probe.
