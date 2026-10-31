# Preparation Failure And Bounded Correction

Active role: ENGINEER for offline correction following AUDITOR operation checks.
Risk: HIGH. Runtime/preparation INCOMPLETE. No retry authorization inferred.

## Actual Approved Attempt

The user approved ONE preparation-only run under reviewed manifest SHA
35032e02db1bf1d569d7918ef9127562abc205154d68908455c3ec5bf3201d42.
Existing `companion_prepare --execute-preparation` ran once, exit1. Attempt
`workerprep20261023v6a` is consumed. The result reports preparation_build failure,
cleanup_verified=true and empty unresolved creation/cleanup lists. Three receipt
events: reserved, preparation failed, entrypoint failed. No create intent or new
ID was recorded. There is no actual-ID evidence to approve.

Read-only postcheck found no stages named for the new attempt. All seven original
and four older-stage selected metadata rows match the precheck byte-equivalent
JSON values. No startup, signal, query, cutover, manual cleanup or retry followed.
This is metadata preservation, not a volume-content or image-cache audit.

`preparation_build` includes the prerequisite prepare call, so the stage name
does not prove any image build command ran. The actual child does not expose a
complete native command trace. Do not claim zero image/cache effects solely from
that label or infer credential-access details not recorded by the receipt.

## Reproduced Defect And One-Line Repair

SHOWN in a bounded read-only diagnostic: engine29.9.1/b26fb77 matches the reviewed
pair; the reviewed first-parent image query exits1 because the optional Config
map has no `Entrypoint` key. Replacing `not .Config.Entrypoint` with
`not (index .Config "Entrypoint")` succeeds on all four parent images and shows
empty entrypoints, no OnBuild and expected IDs/layer-list shapes. This query is
before build and environment copying in source order. It is a reproduced blocker
consistent with the failed stage, not a recovered historical command trace.

The defect was introduced by this thread's v6 check. Earlier synthetic tests
supplied decoded JSON and did not exercise native Go-template optional-key
behavior. The fix changes exactly that expression in WORKER_IMAGE_FORMAT, with
no weakening of the empty-entrypoint check. The old backend bytes reconstruct
exactly by reversing the expression. No signal/budget/ownership policy changes.

VERIFIED_ENV isolated checks:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_worker_image_format.py tests/test_companion_worker_shutdown.py tests/test_companion_running_backend.py
```

194passed1.44s. New tests pin the safe expression and exact one-expression delta;
native read-only equivalence, not those string tests alone, shows Go-template
compatibility on these four images. No broad suite or preparation rerun.

## Prospective Refreshed Inputs, Not A Retry

To avoid another partial handoff, this same bounded correction includes an
offline proposed attempt `workerprep20261023v6b`. New recipe changes only attempt,
cleared decision and reviewer from the previous manifest. All app sources,
commands, modeled fingerprints, baseline and options remain unchanged. Support
bindings change only the backend hash to the exact one-line repair. Both new
attempt markers are absent; no reservation/receipt is created. Old records stay
unchanged, and old IDs/evidence cannot be adopted.

The proposed source delta is not treated as accepted: both repair and refreshed
inputs require one independent combined review. Draft decision INCOMPLETE/blank
reviewer is refused by the loader. Any accepted derivative must be separately
authored by the reviewer changing only decision/reviewer. Nothing auto-executes.

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_worker_template_refresh.py tests/test_companion_worker_image_format.py
```

7passed0.32s; hash drift, occupied attempt, draft/old-evidence refusal, exact
scope and deterministic generated JSON. Generator created draft/provenance only.
Preparation-only300/120 controller/recovery budgets, private credential copy,
four local build invocations/four new never-started containers, owned-new-only
cleanup and actual-ID review before cutover remain the prospective limits.
Another preparation requires explicit approval; no runtime retry occurred.

## Frozen Proof

Artifact folder: `docs/review_artifacts/companion_worker_preparation_20261023/`.

| File | SHA256 |
| --- | --- |
| actual/before_inventory.json | f494a090ed856dcded0f97d2d969f831de1d081e73724a0402fede15b20d67e3 |
| actual/post_inventory.json | 2db7e158c5ba7e51e8102fae38d816aeef90158b94830694866cde5affbfc8f3 |
| actual/readonly_diagnosis.json | e8839d41019b3fdc7d8f0171ee9828f86bcfc3476324ff2e5bd0620ed612c01d |
| actual/preparation_receipt.jsonl | cdd014f97777e42b7251fc4d8f1b899a368764ff843602160da3906f3889c3d5 |
| actual/operation_outcome.json | 150ccdde9fa78e9a340966e9f0ab1f7d7665544f48299c08cf6dba1b153f51f9 |
| scripts/research/companion_install_docker.py | fbe5c0abe9be35cd0765d98b6d31b29f0e075cf7ece2e4d541283bce2755b28c |
| tests/test_companion_worker_image_format.py | 7bd7ce3a1b73f14353d5f053a8fd93ec210996dcb0ea16db309030c765dd6ab1 |
| derive_template_refresh.py | d9f542b30eb8f5cb164f4eedf32c790e8e364beb5a64208b881a90b5b15eb85c |
| tests/test_companion_worker_template_refresh.py | 0c9885ee061d9c0b2150fbbf2dcd69f9763e92331dc153379650db139f1ac0f1 |
| refresh_inputs/candidate_manifest.json | 7928e17e98eb63cd5e28933ddc16071c8de9b728e2df8cb2f456990fe7953047 |
| refresh_inputs/provenance.json | c4bd70588ee5d695cd76fdec3f9380814edc2e833979f67418e60c5964a190ce |

The public receipt is byte-identical to the private controller receipt. Saved
before/post raw rows permit independent comparison; errors/credentials were not
exported. Diagnostic native reads total9 (1before/2after/6diagnosis), separate
from the controller's untraced internal native calls. No assumption of full
system recovery, successful shutdown, working explanation or profitability.

Correction and refreshed inputs READY_FOR_INDEPENDENT_REVIEW. Failed preparation
remains INCOMPLETE; prior accepted inputs are stale for changed source and the
attempt remains consumed. Never edit them, reset their markers or rerun them.
