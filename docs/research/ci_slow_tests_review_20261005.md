# CI test coverage: independent review (structure item 22)

Date: 2026-10-05. Reviewer: Claude (AUDITOR then ENGINEER).
Status: READY_FOR_INDEPENDENT_REVIEW. Changes required CI. Patch 0061
(`ad7b13e7`), bundle rev72, folder `69_ci_runs_slow_tests`. Not pushed, not
applied to this checkout. The workflow has not been run on GitHub.

## What holds

The four files item 22 names are no longer ignored by required CI or by
`make test-fast` / `make test-full`.

## Finding (P3)

A second local-only slice exists that the item does not name. The required
CI core step sets `CBP_SKIP_SLOW=1`, which skips every test marked `slow`:
31 tests in 9 files, among them the paper runner lifecycle, the live
reconciler loop, the strategy runner loop and the crypto-edge collector. No
workflow runs `-m slow`. Two patches in this series change code those tests
cover (0054, 0057).

## Correction

Required CI gets a `Pytest slow loop tests` step after the core suite, with a
five-minute timeout. The policy document records the slice and
`tests/test_ci_slow_tests_policy.py` guards the step. `make test-fast` still
skips them.

## Not done

Not run on GitHub. The slow tests were run on Python 3.12 in the review
environment (31 passed in about 16 s, three runs in a row), not CI's 3.11.

## Facts, not changed

- A pull request touching only `docs/**` or `*.md` skips validate, lint and
  both pytest steps, while many tests pin documentation text.
- The 19 tests that fail in every full run of this series also fail on master
  in the review environment; they shell out to `make`. Whether they pass in
  GitHub CI was not checked.
- mypy is advisory; ruff runs on four files.

## Verification

4 new tests, 3 fail on the previous code. Full suite at the code of 0061:
4777 passed, 33 skipped, 19 failed (the same 19 as master).
