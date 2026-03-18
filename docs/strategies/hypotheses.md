# Strategy Hypothesis Templates

These baseline strategies are treated as falsifiable hypotheses, not proven edges.

Current covered strategies:

- `ema_cross`
- `mean_reversion_rsi`
- `breakout_donchian`

Each hypothesis declares:

- market assumption
- required data
- entry rules
- exit rules
- no-trade rules
- invalidation conditions
- expected failure regimes

Code authority:

- machine-readable declarations live in `/Users/baitus/Downloads/crypto-bot-pro/services/strategies/hypotheses.py`
- tests live in `/Users/baitus/Downloads/crypto-bot-pro/tests/test_strategy_hypotheses.py`

This is deliberately descriptive rather than promotional:

- no profitability claim
- no validated short-support claim
- no autonomous adaptation claim
