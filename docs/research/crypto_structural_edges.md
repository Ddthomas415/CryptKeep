# Crypto Structural Edge Research Modules

These modules are research-only analytics.

Current scope:

- funding-rate carry summaries
- perp/spot basis summaries
- cross-venue dislocation summaries

Code:

- `/Users/baitus/Downloads/crypto-bot-pro/services/analytics/crypto_edges.py`
- `/Users/baitus/Downloads/crypto-bot-pro/tests/test_crypto_edge_analytics.py`

Intent:

- explore differentiated crypto-native signals
- support later evaluation and data collection work
- avoid routing any of this directly into live execution

Explicit non-goals:

- no automatic live trading
- no direct execution hooks
- no profitability claim
- no assumption that any single edge is durable

The current module accepts deterministic input rows and produces descriptive summaries only.
