# Walk-Forward Validation

CryptKeep now includes a research-only anchored walk-forward utility for strategy evaluation.

Code:

- `<your-repo-path>/services/backtest/walk_forward.py`
- `<your-repo-path>/tests/test_backtest_walk_forward.py`

Current scope:

- anchored windows only
- deterministic reuse of the existing parity backtest
- descriptive train/test summaries
- surfaced in persisted strategy evidence and strategy-lab reporting as research-only metadata
- no promotion or live-execution authority

Current non-goals:

- no automatic parameter search
- no auto-promotion
- no use as a promotion gate or live-routing control

This module is intended to answer one narrow question:

- does the current strategy keep producing acceptable test-window behavior after the training window expands?
