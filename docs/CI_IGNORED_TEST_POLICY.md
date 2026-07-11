# CI Ignored Test Policy

Date: 2026-07-03

## Current State

The GitHub Actions core pytest job and `make test-fast` / `make test-full`
currently ignore:

- `tests/test_symbol_scanner.py`
- `tests/test_dashboard_view_data.py`
- `tests/test_dashboard_page_runtime.py`
- `tests/test_dashboard_home_digest.py`

This policy records the state. It does not change required CI.

An optional GitHub Actions workflow,
`.github/workflows/ci-ignored-tests.yml`, can run the same slice manually via
`workflow_dispatch`. It is intentionally not triggered on `pull_request` or
`push`, so required CI behavior remains unchanged until the ignored tests are
made CI-safe or split into smaller required regressions.

## Risk

Ignored tests are a drift channel. Dashboard and symbol-scanner behavior can
break without blocking CI.

## Policy

Each ignored test file must eventually be one of:

- made CI-safe and returned to the normal suite
- moved to a named optional job with documented prerequisites
- split into smaller CI-covered regression slices
- retired if it no longer tests a supported surface

## Required Next Step

Before changing dashboard runtime behavior or symbol-scanner behavior, either:

- run the relevant ignored test locally and record the result, or
- add a smaller targeted CI-safe regression test for the behavior being changed.

## Command For Manual Local Check

Do not run this automatically in Codex sessions if the user has asked to avoid
long tests:

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
symbol-scanner changes need a repository-hosted check but should not block the
normal required CI suite.
