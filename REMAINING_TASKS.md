# Remaining Tasks

This file is a lightweight index only.

## Current state
The frozen canonical root-runtime path is hardened enough on the repo side.
The remaining critical path is external environment proof or a human launch decision.

## Canonical blocker list
See:

- docs/checkpoints/launch_blockers_root_runtime.md

Strategy-evaluation work is tracked separately:

- docs/checkpoints/strategy_signal_quality_plan_2026_05_22.md

## Master integration TODO
`review-stabilized` is the current accepted audit/integration branch. Draft PR
[#49](https://github.com/Ddthomas415/CryptKeep/pull/49) tracks the remaining
master update.

SHOWN on 2026-06-06:
- `origin/master...origin/review-stabilized = 0 / 19`
- `origin/master` is an ancestor of `origin/review-stabilized`
- the prior 25-file conflict plan is obsolete for the current branch tips
- the aggregate diff is clean under `git diff --check`
- the latest full suite reports `2113 passed, 33 skipped, 13 warnings`

Next action:
- Independently review PR #49 as a HIGH-risk aggregate integration
- Confirm required GitHub checks pass on the current head
- Merge only after the aggregate review is accepted
- Verify `origin/master` reaches the accepted `review-stabilized` head

## Interpretation
The critical path is:

1. use the frozen canonical root-runtime path recorded in `docs/checkpoints/root_runtime_scope_record.md`
2. obtain one reachable supported sandbox/testnet venue from the operator environment
3. prove private lifecycle runtime flow on that reachable venue
4. or make an explicit human launch decision accepting the current environment-blocked exception

Already completed on the frozen canonical path:
- private authenticated connectivity for one supported venue
- singular live-mode source of truth
- boundary-governed live lifecycle authority
- hidden-default fencing for the chosen launch path

## Notes
Do not mix:
- launch blockers
- strategy signal-quality / paper-evaluation work
- conditional broader-scope controls
- non-blocking architectural debt
