# Strategy Feedback Ledger

CryptKeep now includes a research-only strategy feedback ledger derived from persisted paper fills.

Code:

- `<your-repo-path>/services/analytics/strategy_feedback.py`
- `<your-repo-path>/tests/test_strategy_feedback.py`

Current scope:

- loads persisted paper fills from `journal_fills`
- normalizes fills to known strategy IDs
- computes realized closed-trade feedback by strategy
- derives conservative research-only leaderboard adjustments
- surfaces those summaries in evidence-cycle and strategy-lab reporting

Boundary:

- strategy feedback is descriptive metadata derived from persisted paper fills
- feedback weighting may adjust research leaderboard scores only
- feedback weighting is not promotion authority
- feedback weighting is not strategy configuration authority
- feedback weighting is not position-sizing authority
- feedback weighting is not campaign, live-routing, or execution authority
- any use beyond research ranking requires a separate reviewed config, campaign,
  gate, or execution change with its own proof

Current non-goals:

- no live position-sizing changes
- no promotion authority
- no auto-enablement of live trading
- no claim that persisted paper feedback alone proves a profitable edge

This module is intended to answer one narrow question:

- does persisted paper-trade behavior provide enough strategy-specific evidence to slightly reweight research ranking without changing live risk controls?
