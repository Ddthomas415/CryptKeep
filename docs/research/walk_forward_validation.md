# Walk-Forward Validation

CryptKeep now includes a research-only anchored walk-forward utility for strategy evaluation.

Code:

- `<your-repo-path>/services/backtest/walk_forward.py`
- `<your-repo-path>/services/backtest/parameter_sweep.py`
- `<your-repo-path>/services/analytics/archive_parameter_sweep_triage.py`
- `<your-repo-path>/tests/test_backtest_walk_forward.py`

Current scope:

- anchored windows only
- deterministic reuse of the existing parity backtest
- descriptive train/test summaries
- bounded archive-backed parameter sweeps with deterministic ranking
- manual-review triage over stored sweep artifacts
- surfaced in persisted strategy evidence and strategy-lab reporting as research-only metadata
- no promotion or live-execution authority

Current non-goals:

- no auto-promotion
- no use as a promotion gate or live-routing control

This module is intended to answer one narrow question:

- does the current strategy keep producing acceptable test-window behavior after the training window expands?

The parameter-sweep triage layer only ranks existing sweep variants as
`candidate_for_manual_review` or `not_candidate`. It does not rerun backtests,
change strategy configuration, start campaigns, or produce promotion evidence.
