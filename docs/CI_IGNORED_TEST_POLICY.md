# CI Ignored Test Policy

Date: 2026-07-03

## Current State

As of 2026-07-15, the GitHub Actions core pytest job and `make test-fast` /
`make test-full` no longer ignore the dashboard and symbol-scanner tests.
These files are required in the normal suite:

- `tests/test_symbol_scanner.py`
- `tests/test_dashboard_view_data.py`
- `tests/test_dashboard_page_runtime.py`
- `tests/test_dashboard_home_digest.py`

This policy records the former drift channel and the guard against
reintroducing it.

An optional GitHub Actions workflow,
`.github/workflows/ci-ignored-tests.yml`, can run the same slice manually via
`workflow_dispatch` for focused dashboard/symbol-scanner triage. It is
intentionally not triggered on `pull_request` or `push`; required CI already
runs the files through the normal core pytest job.

## Risk

Ignored tests are a drift channel. Dashboard and symbol-scanner behavior must
not be excluded from required CI without a new reviewed policy update.

## Policy

The files listed above are back in the normal suite. Future dashboard or
symbol-scanner tests should stay in required CI unless they are explicitly
classified with a reviewed reason and a smaller required regression slice.

## Required Next Step

Do not add permanent `--ignore` entries for the files listed above. The
regression `tests/test_ci_ignored_tests_policy.py` checks that required CI and
the local fast/full targets do not reintroduce those ignores.

## Command For Focused Local Check

The former ignored-test slice remains available as a focused diagnostic:

```bash
make test-ci-ignored
```

The target expands to:

```bash
./.venv/bin/python -m pytest -q \
  tests/test_symbol_scanner.py \
  tests/test_dashboard_view_data.py \
  tests/test_dashboard_page_runtime.py \
  tests/test_dashboard_home_digest.py
```

## Optional GitHub Check

Run **Optional Ignored Tests** from the GitHub Actions UI when dashboard or
symbol-scanner changes need an additional repository-hosted focused check.
