# Repo Alignment Workflow

## Goal
Keep the repo in canonical shape and prevent drift from returning.

## Primary commands

1. Fast alignment gate:
`python scripts/check_repo_alignment.py`

List guard tests:
`python scripts/check_repo_alignment.py --list-tests`

JSON status:
`python scripts/check_repo_alignment.py --json`
: includes `schema_version`, `mode`, `started_at`, `finished_at`, and `duration_seconds`.
: `mode` values: `full` (default) or `full_skip_guards` (when `CBP_ALIGNMENT_SKIP_GUARDS=1`).

List-tests JSON status:
`python scripts/check_repo_alignment.py --list-tests --json`
: includes `schema_version`, `mode`, `started_at`, `finished_at`, and `duration_seconds`.
: `mode` value: `list-tests`.

Fast JSON status (skip guard test execution):
`CBP_ALIGNMENT_SKIP_GUARDS=1 python scripts/check_repo_alignment.py --json`

2. Quick validation (includes alignment gate):
`python scripts/validate.py --quick`

Quick JSON validation:
`python scripts/validate.py --quick --json`
: includes `schema_version`, `mode`, `started_at`, `finished_at`, and `duration_seconds`.
: `mode` values: `quick` or `full`.

3. Full validation:
`python scripts/validate.py`

Full JSON validation without running inner pytest:
`CBP_VALIDATE_SKIP_PYTEST=1 python scripts/validate.py --json`
: payload keeps `mode=full` and sets the `pytest` step as skipped.

4. Pre-release quick JSON sanity:
`python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy --skip-pytest --skip-config --skip-imports`
: includes `schema_version`, `mode`, `started_at`, `finished_at`, and `duration_seconds`.
: `mode` values: `quick`, `full`, or `custom` (when a subset of skip flags is used).

Pre-release full JSON without running inner pytest:
`CBP_PRE_RELEASE_SKIP_PYTEST=1 python scripts/pre_release_sanity.py --json --skip-ruff --skip-mypy`
: payload uses `mode=custom` and sets the `pytest` step as skipped.

## Make targets

Use these wrappers when running from repo root:

- `make doctor-strict`
- `make alignment` (alias of `make check-alignment`)
- `make check-alignment`
- `make check-alignment-list`
- `make check-alignment-list-json`
- `make check-alignment-json`
- `make check-alignment-json-fast`
- `make validate-quick`
- `make validate-json-quick`
- `make validate-json-fast`
- `make validate-json`
- `make validate`
- `make pre-release-sanity`
- `make pre-release-sanity-quick`
- `make pre-release-sanity-json-quick`
- `make pre-release-sanity-json-fast`
- `make test`
- `make test-runtime`
- `make test-checkpoints`

## What each command enforces

`scripts/check_repo_alignment.py`
- `tools/repo_doctor.py --strict`
- Alignment guard tests from `GUARD_TESTS` (inspect with `--list-tests`)

`scripts/validate.py --quick`
- Runs `scripts/check_repo_alignment.py`
- Runs a quick pytest subset for validation wiring/smoke

`scripts/validate.py`
- Runs `scripts/check_repo_alignment.py`
- Runs `scripts/preflight_check.py`
- Runs full `pytest`
  - `scripts/preflight_check.py` now treats merged runtime config availability as valid, not just legacy `config/trading.yaml`

`make test-runtime`
- Runs top-level `tests/` excluding files named `test_checkpoints*`
- Use this when you want runtime/product-facing validation without the checkpoint-formatting lane

`make test-checkpoints`
- Runs only `tests/test_checkpoints*.py`
- Use this when you want the checkpoint/repo-hygiene lane explicitly

## Drift policy

- If `repo_doctor --strict` fails, stop and fix alignment first.
- Do not add non-canonical top-level dirs/files.
- Keep script bootstrap centralized via `scripts/_bootstrap.py`.
- Keep tool bootstrap centralized via `tools/_bootstrap.py`.
