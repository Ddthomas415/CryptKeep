# Walk-Forward Validation

CryptKeep now includes a research-only anchored walk-forward utility for strategy evaluation.

Code:

- `/Users/baitus/Downloads/crypto-bot-pro/services/backtest/walk_forward.py`
- `/Users/baitus/Downloads/crypto-bot-pro/tests/test_backtest_walk_forward.py`

Current scope:

- anchored windows only
- deterministic reuse of the existing parity backtest
- descriptive train/test summaries
- no promotion or live-execution authority

Current non-goals:

- no automatic parameter search
- no auto-promotion
- no direct evidence-cycle wiring yet

This module is intended to answer one narrow question:

- does the current strategy keep producing acceptable test-window behavior after the training window expands?
