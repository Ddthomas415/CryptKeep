# Stopped installer: canonical temporary path and failure stages

Date: 2026-10-18. Active role: ENGINEER. Risk: HIGH.
Implementation READY_FOR_INDEPENDENT_REVIEW; restoration INCOMPLETE.

## Preserved failed attempt

User authorized one new stopped-only installation attempt following independent
Healthcheck repair review. All 30 combined original/supplemental bindings matched
before execution. Ran the same hash-bound installer once, with a new exclusive
receipt `installation_receipt_repaired_20261018.jsonl` under
`docs/review_artifacts/companion_install_candidate_20261018/`.
Exit 1, installed_stopped=false, services_started=false, no installation evidence.
The receipt contains reserved/failed only and has SHA256
87a69ba8bfcbfae057f388b6e52c4c415f80b59428a6669b23661394b8f66c97.
Its bytes happen to equal the previous generic receipt; the files remain separate.
No retry or later container mutation was performed.

## Diagnosis correction and evidence

The Healthcheck template defect was real and separately reproduced, but the
previous receipts did not prove it caused the failed installer calls. A further
local-only probe under the exact clean environment showed:

```json
{"path_is_canonical":false,"unresolved_cli_check":false,"canonical_cli_check":true,"docker_executed":false}
```

SHOWN: Python creates its temporary directory through `/tmp` in this environment;
on this Mac that resolves through `/private/tmp`. The backend passed the
unresolved path to the transport, whose existing strict verifier refuses it
before calling Docker. This deterministically establishes a pre-transport
blocker; the old generic receipt still does not provide its actual exception.
Do not retroactively label the Healthcheck reproduction as an actual failure
trace. Both defects are preserved in the correction history.

## Smallest correction and diagnostics

Resolve only the newly created private temporary directory once, then use the
same canonical path for verification and Docker argv. The existing verifier's
no-symlink, empty-directory and CLI-hash requirements remain unchanged. No
fallback, global environment inheritance or context override was added.

Installer now records a fixed stage code in a failed receipt and result, never
raw exception text, command output, environment or credentials. Codes identify
reservation, inventory/baseline preflight, prepare, build, inventory recheck,
replacement, postconditions and receipt commit. Replacement receipts still
identify the individual public intended operation. Deadlines, ownership,
rollback, stage-policy deferrals and one-attempt behavior are unchanged.

```text
scripts/research/companion_install_docker.py
0b482168d614c5c972b090f9a4dddd81b3b3173bf0ee4e34c56f3c2a246529c4
scripts/research/companion_installer.py
15fb60123ce1be1f26f276360b2ec82e54cbbfc6dce626a3f09da45916dd42e2
tests/test_companion_installer.py
8295cdf52da11af810b76eb85290f061c459450ef50abb6b6fea2b4edf8a3318
```

Six new cases: a symlinked temporary root with the real verifier and good/bad
synthetic CLI pins; four fixed-stage failure cases. Before source corrections:
5 failed, 1 passed. After:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
 ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null -p no:cacheprovider \
 tests/test_companion_installer.py tests/test_companion_install_env.py \
 tests/test_companion_docker_transport.py tests/test_companion_existing_controller.py \
 tests/test_companion_runtime_adapter.py
```

VERIFIED_ENV: 362 passed in 2.58s. Local/synthetic tests, not full-suite evidence.

## Actual read-only preflight

Using the corrected backend and existing bounded ProcessExecutor, a separately
permission-checked diagnostic called only inventory, engine identity and four
parent-image metadata checks. No prepare/private environment or labels, build,
rename, disconnect, create, source copy, startup or query. Actual output:

```json
{"stage":"read_only_preflight","native_backend_inventory_passed":true,"all_seven_original_snapshots_match":true,"reviewed_engine_matches":true,"local_parent_images_verified":4,"installation_executed":false,"private_configuration_accessed":false}
```

This proves the repaired path reaches the intended daemon read-only and the
selected originals still match. Private preparation, derivative builds,
replacements and runtime remain UNVERIFIED. Earlier review artifacts and failed
receipts are immutable. Separate review must bind these changed code hashes;
another install attempt still needs its own operational permission. No new
startup or trading authorization is inferred.
