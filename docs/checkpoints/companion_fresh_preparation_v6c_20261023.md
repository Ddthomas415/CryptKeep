# Fresh Stopped-Preparation Proposal, October 23

Active role: ENGINEER. Risk: HIGH. Objective: fresh preparation inputs after the
accepted active-network correction, without restarting or retrying services.
Implementation state: READY_FOR_INDEPENDENT_REVIEW. Runtime: INCOMPLETE.

## Current Observation

SHOWN at 2026-10-23T19:23:45.869706+00:00: two selected sanitized inspect reads
returned identical full selected metadata for seven known original containers.
All seven were running with the expected IDs/images. No health or query test.
Docker CLI SHA256 remains `678271184175b40dfc4bd6f4582be00ae1538b0d1e031181f52ceedfae9af5fb`.
Native `/usr/bin/codesign --verify --strict` exited0 outside the sandbox.

Initial sandbox signature verification reported invalid and the collector hit
socket_permission_denied. Both are preserved as limitations, not relabelled as
service defects. The prior October20 checkpoint documents the same sandbox
signature false negative. No Docker repair or permission bypass was performed.
The bounded read-only signature/capture were repeated with tool-approved native
access; only metadata inspect ran, with 10-second per-read timeouts.

Collector report still says INCOMPLETE because its legacy reference expects all
seven containers exited. The report is not modified. New derivation explicitly
checks running state, IDs/images, restart counts, original foundation and
configured fingerprints against the prior accepted plan. No ignored drift:

- Storage three snapshots: no changes.
- Audit app: start timestamp changed.
- Risk, memory and orchestrator: start timestamp and raw preservation changed;
  configured fingerprints and non-network foundations remain unchanged.

Fresh observations do not establish liveness beyond Docker's running flag,
stored-volume integrity, healthy endpoints, or a functioning explanation path.

## Artifact Changes

Only new proposal artifacts/tests plus current work-log/queue/checkpoint updates.
No production implementation, frozen review, consumed receipt or old packet edits.

`derive_fresh_preparation.py` verifies five pinned inputs, the independent
correction's complete bound-hash list, 13 selected consumer hashes and 43 local
application source entries. It uses the accepted shared final-model helper,
checks original current configuration equivalence without rewriting observation,
and refuses occupied preparation/cutover markers for `workerprep20261023v6c`.

Candidate changes only attempt, cleared decision/reviewer and freshly observed
baseline. Four application specifications, commands, create/network options,
source pins, policies and modeled configured predictions are unchanged. Draft
has INCOMPLETE/empty reviewer; Plan.load refuses it. New image/container IDs are
unknown until separately authorized preparation. No old removed ID is adopted.

## Verification

VERIFIED_ENV, local isolated tests with socket/process access forbidden:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_fresh_preparation.py
```

SHOWN: 9 passed in0.25s; input/hash/consumed-marker/current-drift and default
non-approval regressions. No broad suite or already accepted correction rerun.
Inert generator executed once, producing only new proposal JSON files.

| Artifact | SHA256 |
| --- | --- |
| derive_fresh_preparation.py | bb5854132df93d2e055a98358e581fc4a8ab7c16db2f98e7048e51a29d63544e |
| tests/test_companion_fresh_preparation.py | 87559db1046343b45e90c2e93ee4c3e95d0e88afa2810254bf52c857d1af1d39 |
| fresh_preparation_v6c/candidate_manifest.json | 481de681cd6f667c03e54d48ebb262ccb9c6cc5a22b21dda68bac7d7f9d853af |
| fresh_preparation_v6c/provenance.json | b2d6496eff557543b3b7464bb0d0ebc044a502445a80c1d585f5e1c1e871ef1b |
| fresh_baseline_v6c_native/observation.json | 61ebef99a9053815450d1b2eab5e6f751b89c2a1f8d762f8210fe1b8ee8087b6 |

All artifact paths other than the test are under
`docs/review_artifacts/companion_worker_preparation_20261023/`.

## Separate Preparation Boundary

After independent input review and separate explicit operational approval, reuse
the existing `companion_prepare` entry point ONCE: reserve a new receipt, build
four local COPY-only images without pull/RUN/build network, privately copy the
existing service/storage credentials to configuration, and create four new
never-started application containers. This is not a runtime retry.

Existing 300-second controller budget includes120seconds recovery reserve;
pre-controller I/O is not a whole-command hard deadline. Originals and three
storage services/volumes remain untouched. Existing owned-new-stage cleanup on
failure only; cache/configuration/logs may persist. No old-stage/volume removal,
original stop, force kill, service startup, token query, database migration,
account/strategy/risk/trading change or automatic subsequent operation.

Success leaves four stopped new IDs for exact-ID/image/source/alias review. Their
alias set remains unverified now; it must not be silently inferred or normalized.
The used v6b receipt and all previous stages remain preserved. Runtime cutover
and one real cited query require their own subsequent bounded authorization.

Next proof: separate review may issue an accepted input derivative changing only
decision/reviewer. Parent then verifies hashes and runs default inert validation
with native/backend/reservation calls forbidden. No preparation is authorized by
this document, its tests, or any review acceptance.
