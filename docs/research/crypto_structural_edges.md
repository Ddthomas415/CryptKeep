# Crypto Structural Edge Research Modules

These modules are research-only analytics.

Current scope:

- funding-rate carry summaries
- perp/spot basis summaries
- cross-venue dislocation summaries
- bundled sample snapshot loader for local demo/review

Code:

- `/Users/baitus/Downloads/crypto-bot-pro/services/analytics/crypto_edges.py`
- `/Users/baitus/Downloads/crypto-bot-pro/storage/crypto_edge_store_sqlite.py`
- `/Users/baitus/Downloads/crypto-bot-pro/scripts/record_crypto_edge_snapshot.py`
- `/Users/baitus/Downloads/crypto-bot-pro/scripts/load_sample_crypto_edge_data.py`
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

## Local sample workflow

To load deterministic sample data into the local research store:

```bash
make load-sample-crypto-edges
```

This writes bundled sample snapshots from:

- `/Users/baitus/Downloads/crypto-bot-pro/sample_data/crypto_edges/funding.json`
- `/Users/baitus/Downloads/crypto-bot-pro/sample_data/crypto_edges/basis.json`
- `/Users/baitus/Downloads/crypto-bot-pro/sample_data/crypto_edges/quotes.json`

The loader is still research-only:

- it writes local snapshot rows
- it does not place orders
- it does not alter execution state
