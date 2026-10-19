# Accounting treatment full-suite checkpoint

Active role AUDITOR. Acceptance INCOMPLETE for release readiness.

## Results

| Snapshot | Passed | Failed | Skipped | Duration |
| --- | ---: | ---: | ---: | ---: |
| Controlled pre-treatment comparison | 3,822 | 33 | 38 | 76.77 seconds |
| Corrected current working source | 3,854 | 33 | 38 | 77.15 seconds |

Exact failure identity comparison: 33 shared, zero new failures, zero resolved
failures. The corrected snapshot includes 32 additional accounting tests.
This is not a green suite and does not establish production readiness.

The comparison preserves unrelated current working-tree changes; it restores
only the three accounting production files and three affected compatibility
test files from HEAD 620bc8dbeee71cca327042902759e219e18f30b6, removing the two
new treatment test files. It is not a pristine-master baseline or a historical
comparison with the previously reported 19-failure cloud run.

## Corrections during verification

An initial disposable run produced 3,850 passed / 37 failed / 38 skipped.
The snapshot had no commit metadata, affecting Git-dependent tests; its three
latency/session reconciliation fixtures lacked the new durable store methods.
Added synthetic local snapshot Git metadata (no remote, no source-repo commit)
and upgraded these fixtures to real temporary SQLite tracking stores. Existing
latency/session assertions remain, and that 17-test file passed separately.
No additional financial behavior changed during this verification checkpoint.

## Safety and reproducibility

VERIFIED_ENV: current source copied to disposable directories, inventory hashes,
clean subprocess environment, temporary HOME/state/database paths, real keyring
backend disabled, read-only original virtual environment. macOS sandbox denies
network operations, operator home-file contents except dependency reads, and
all operator-home writes. Separate probes confirmed PermissionError for an
external connection and reading the original AGENTS.md. Directory metadata is
allowed so Python can resolve its executable. Operator state/config/credentials
were not copied; no real Git remote or original history was included.

Command: .venv/bin/python -B docs/review_artifacts/run_isolated_treatment_suite.py
and the same command with --pre-treatment. Each invokes pytest tests -q without
forcing slow-test skips, with a 900-second timeout and disposable JUnit output.
The 38 skips are reported by pytest, not suppressed by this runner. Optional
companion packages/source not in the snapshot are not integration proof.

Durable evidence:
docs/review_artifacts/treatment_full_suite_20261007/pre_treatment/{results.xml,run_summary.json,inventory.json}
docs/review_artifacts/treatment_full_suite_20261007/corrected/{results.xml,run_summary.json,inventory.json}

Full logs remain in /private/tmp/cryptkeep-full-suite-3oebyjeb and
/private/tmp/cryptkeep-full-suite-ad0dt35o. Financial source and changed latency
test hashes matched the final tested snapshot at checkpoint.

## Remaining blocker

Repo Doctor reports research/ as non-canonical and fails strict validation;
alignment/Make/validation tests propagate this refusal in both snapshots.
The current research directory is part of the preserved research work, not
evidence that intelligence capability should be deleted. Address the explicit
layout classification in a bounded follow-up, retaining unknown-directory
detection; do not erase research to obtain a passing result.

No CI, remote-host, genuine exchange or deployment proof. No accounts, configs,
collectors, orders, live authorization, publication or deployment changed.

## Follow-up: intentional research root corrected

The bounded research-layout correction explicitly allows research/ without
making it required or disabling unknown-directory checks. Final full-suite
snapshot: 3,889 passed, 38 skipped, zero failures (exit 0, 286.24 seconds).
This supersedes the 33-failure result for current tested local source, not for
CI or deployed runtime. See research_layout_treatment_20261007.md and the
research_layout_corrected evidence subdirectory. No deployment authorized.
