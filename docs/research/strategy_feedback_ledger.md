# Strategy Feedback Ledger

CryptKeep now includes a research-only strategy feedback ledger derived from persisted paper fills.

Code:

- `/Users/baitus/Downloads/crypto-bot-pro/services/analytics/strategy_feedback.py`
- `/Users/baitus/Downloads/crypto-bot-pro/tests/test_strategy_feedback.py`

Current scope:

- loads persisted paper fills from `journal_fills`
- normalizes fills to known strategy IDs
- computes realized closed-trade feedback by strategy
- derives conservative research-only leaderboard adjustments
- surfaces those summaries in evidence-cycle and strategy-lab reporting

Current non-goals:

- no live position-sizing changes
- no promotion authority
- no auto-enablement of live trading
- no claim that persisted paper feedback alone proves a profitable edge

This module is intended to answer one narrow question:

- does persisted paper-trade behavior provide enough strategy-specific evidence to slightly reweight research ranking without changing live risk controls?
