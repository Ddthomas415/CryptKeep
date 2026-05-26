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
`review-stabilized` is the current accepted audit/integration branch, but `master`
is not caught up. Do not treat `review-stabilized` being clean as meaning `master`
is updated.

SHOWN on 2026-05-25:
- `origin/master...origin/review-stabilized = 59 / 65`
- `review-stabilized` is not an ancestor of `master` or `origin/master`
- a no-commit test merge of `origin/review-stabilized` into `origin/master` produced 25 conflicted files

Next action:
- Create a dedicated integration branch from `origin/master`
- Merge `origin/review-stabilized`
- Resolve conflicts under independent review because the conflicts include live execution, paper execution, queue storage, dashboard settings, and tests
- Run the relevant execution/storage/dashboard test slices before updating `master`

Known conflicted files from the 2026-05-25 test merge:
- `dashboard/services/views/_shared_settings.py`
- `dashboard/services/views/settings_view.py`
- `docs/CURRENT_RUNTIME_TRUTH.md`
- `scripts/SCRIPTS.md`
- `scripts/compat/run_bot_runner.py`
- `services/execution/intent_consumer.py`
- `services/execution/intent_lifecycle.py`
- `services/execution/intent_reconciler.py`
- `services/execution/intent_store.py`
- `services/execution/intent_writer.py`
- `services/execution/live_arming.py`
- `services/execution/live_executor.py`
- `services/execution/live_intent_consumer.py`
- `services/execution/live_reconciler.py`
- `services/execution/paper_engine.py`
- `services/execution/paper_runner.py`
- `services/execution/state_authority.py`
- `storage/intent_queue_sqlite.py`
- `storage/live_intent_queue_sqlite.py`
- `tests/test_backtest_leaderboard.py`
- `tests/test_intent_queue_integrity.py`
- `tests/test_live_execution_wiring.py`
- `tests/test_live_intent_queue_integrity.py`
- `tests/test_paper_engine_integration.py`
- `tests/test_run_bot_runner.py`

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
