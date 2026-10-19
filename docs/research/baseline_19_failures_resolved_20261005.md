# The "same 19 failures as master": resolved

Date: 2026-10-05. Reviewer: Claude. No patch; this corrects a statement
carried in every work-log entry and README of the unpushed series
(patches 0031 to 0061).

## What was reported

Each full test run of the series was reported as "N passed, 33 skipped, 19
failed (the same 19 as master)". The last review note said it had not been
established whether those 19 also fail in GitHub CI.

## What they are

SHOWN: an artifact of the review environment, not of the code.

- 18 of the 19 run `make` targets. The Makefile picks `./.venv/bin/python`
  if it exists, else `python3`. The review clone keeps its virtualenv outside
  the checkout, so `make` fell back to a system `python3` that has no pytest
  (`/usr/bin/python3: No module named pytest`).
- The 19th runs `scripts/manual_repo_audit.sh`, which chooses its interpreter
  the same way (`PYTHON_BIN`).

With `PYTHON` and `PYTHON_BIN` pointed at the virtualenv:

- the 19 tests: 19 passed;
- the full suite at the series head (`ad7b13e7`, patch 0061):
  **4796 passed, 33 skipped, 0 failed**.

## What this changes

- The series has no failing test when the tooling uses the right
  interpreter. Earlier counts read "X passed, 19 failed"; the 19 were never
  evidence about master or about a patch.
- It does not show GitHub CI is green on master: this session has no access
  to the repository's Actions runs. A checkout with `.venv` present, as on
  this machine and in CI (which installs into the runner's Python), does not
  hit this fallback.

## Not checked

The per-patch full-suite runs were not repeated with the corrected
interpreter; only the series head was. The 19 are `make`/audit smoke tests
that the patches do not touch, except that they run the whole tree's
validation.
