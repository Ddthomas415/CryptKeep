# Companion Metadata Failure Diagnostics

Active role GATE, recording separate review; risk HIGH (installer failure/rollback
and diagnostic confidentiality). State ACCEPTED_WITH_RISK for offline scope.
Runtime installation remains
INCOMPLETE; no further installation, startup or query was performed/authorized.

## Objective And Evidence

The approved offline task is to capture sanitized field-level evidence before
cleanup when the existing replacement metadata gate fails. The consumed v3
attempt retained only aggregate fingerprints. Its specific differing field and
cause remain UNVERIFIED; they cannot be recovered from those hashes alone.

Changes:

- New `scripts/research/companion_metadata_diagnostics.py`: derive an optional
  public expectations profile from saved observations, bound to the exact
  reviewed plan and all four existing replacement fingerprints. Fixed-field
  comparisons call the unchanged fingerprint functions in both substitution
  directions; output contains only fixed field names, booleans and a fixed schema.
- `companion_installer.py`: on metadata failure only, request a bounded diagnostic
  when the other replacement/ownership checks passed. Strictly validate output
  before recording it, before rejection and rollback. Absent profile, errors,
  timeouts or invalid payloads produce only `available:false`. No error text or
  arbitrary backend field enters the receipt. The original gate still decides.
- `companion_install_docker.py`: optional in-memory expectations and one existing
  inspect-format read of the owned replacement in the bounded child. It checks
  identity/ownership/stopped state and binds the observed fingerprint to the
  previous controller snapshot; a changed snapshot is unavailable, not guessed.
- Optional paired CLI arguments: `--metadata-expectations` and
  `--reviewed-metadata-expectations-sha256`. Without `--apply-install`, CLI remains
  validation-only. These arguments are not operational authorization.
- Thirty new offline tests in `tests/test_companion_metadata_diagnostics.py`.

Neither preservation algorithm, network normalization, existing replacement
comparison nor rollback ownership policy was changed. No raw environment,
credential value, credential hash, raw metadata or exception text is added to
operational receipts. The public profile uses only already-saved selected
metadata; flags contain only known key names and booleans, never environment
values. Flag ordering is reported, not normalized away. Field differences do
not by themselves establish causation; interactions can remain unresolved.

## Verification

VERIFIED_ENV, offline command:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider tests/test_companion_metadata_diagnostics.py tests/test_companion_installer.py tests/test_companion_network_configuration.py tests/test_companion_stopped_recipe.py
```

Result: **163 passed, 2 failed**, exit 1, in 1.37s. All 30 new tests pass.
The two stopped-recipe tests fail at `reconciliation_fingerprint_mismatch`:
`test_legacy_evidence_not_upgraded_to_paired_proof` and
`test_paired_payload_can_be_verified_offline`. They were reproduced against
the preserved pre-change source with no edits to fixtures or frozen artifacts.
That isolated baseline pytest returned 1, two failures in 0.19s; its wrapper
printed the result and exited 0, not a passing pytest result. This is not a green
full suite. These failures are outside the diagnostic delta and remain recorded.

The baseline run used the same interpreter and the trusted earlier recovery's
source-only scripts under `screened_recovery_20261018T190049Z_r2/restored` from
`/private/tmp`, clean environment, PYTHONPATH to that root and importlib pytest
mode. Module paths in its output confirm the preserved source was used. No
market-data study or application service was executed.

## Bindings And Generated Artifact

| File | SHA256 |
| --- | --- |
| companion_metadata_diagnostics.py | 63fff7cbc5b9f977c53efddca5e40ef8f2bd49606efc1bde82263a4fb860ce66 |
| companion_installer.py | 427fa60328438157255dda2e2a83c6a406e0b2fc90699315fa66da3f374c271d |
| companion_install_docker.py | f599dff66e5c3770a1659cdae945bbfa4a4aa7f0f72b50118cad35886503569e |
| test_companion_metadata_diagnostics.py | 011f38f0b602e9ae39acd447d91221892f6ba859b9131427646ba52c78f5f90a |

Unchanged fingerprint sources: runtime adapter
`83645cc36a345fcd55d1d2bd79dca982141e009456209a031c6e8513f9f03e9c`;
network projection `c3824743fb08098a35af6966ee9e3345a63e6500f18a5fdd84a02d1114bf39d7`.

An inert offline generator created
`docs/review_artifacts/companion_install_candidate_20261018/configured_v3/metadata_expectations_20261018.json`,
SHA256 `4a04bd1ab084711f88d1fd117dca68a5482d4ce065e7bee9ab7d47863e978277`.
It matches all four reviewed plan replacement digests. The plan remains unchanged
at `f5b044858c3d40881239b77745d0b404c4ac05d2f35a6d043fed8f6ba934bf5f`.
Old attempt/rollback records and source versions in the recovery copy are intact.
Changed source invalidates old operational code bindings; this is not a new
executable approval bundle and must not reuse the consumed attempt's authority.

## Remaining Boundary

Independent code/profile review completed. No Docker, native inspect, install,
credential read, image build, service start/stop, network request, schedule,
account, Git lock, commit/push or trading change occurred. Actual mismatch field,
operational compatibility and restoration remain UNVERIFIED. Later operational
work requires its own bounded authorization; no retry follows from these tests.

## Independent Disposition

Separate GATE `01a150b2-8681-7c80-9268-57b8387922bd` accepted the pinned offline
delta WITH_RISK, no blockers. Review:
`docs/review_artifacts/companion_install_candidate_20261018/configured_v3/metadata_diagnostics_review.json`,
SHA256 `6b08dabe8badca663af6fa337f4a8b74a9f907e60679c6ae555c1b6170f9ff65`.
It independently reproduced the four-app public profile byte-for-byte, matched
the pins and reran the focused selection: 163 passed, 2 failed in 1.00s, all 30
new tests passing. Baseline failure reproduction remains parent proof; reviewer
verified the saved source hashes and matching failure signatures, not a second
baseline run. No fixtures were changed to obtain acceptance.

Accepted limits: diagnostic failure-path tests use an inline fake executor;
the unchanged child timeout containment was inspected, not newly exercised.
Actual native inspect compatibility, rollback and historical root cause remain
UNVERIFIED. Evidence may be unavailable or show interacting fields rather than
a single cause. This closes the offline implementation/review objective only.

Current proof receipt:
`docs/review_artifacts/companion_install_candidate_20261018/configured_v3/metadata_diagnostics_verification.json`.
Historical installation/rollback receipt and post-state hashes still match;
HEAD and the zero-byte October 4 Git lock are unchanged. No new executable
approval bundle was produced and no consumed attempt was revived.
