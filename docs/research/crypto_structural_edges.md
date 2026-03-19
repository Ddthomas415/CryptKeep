# Crypto Structural Edge Research Modules

These modules are research-only analytics.

Current scope:

- funding-rate carry summaries
- perp/spot basis summaries
- cross-venue dislocation summaries
- bundled sample snapshot loader for local demo/review
- read-only live snapshot collector driven by a JSON collection plan

Code:

- `/Users/baitus/Downloads/crypto-bot-pro/services/analytics/crypto_edges.py`
- `/Users/baitus/Downloads/crypto-bot-pro/services/analytics/crypto_edge_collector.py`
- `/Users/baitus/Downloads/crypto-bot-pro/storage/crypto_edge_store_sqlite.py`
- `/Users/baitus/Downloads/crypto-bot-pro/scripts/record_crypto_edge_snapshot.py`
- `/Users/baitus/Downloads/crypto-bot-pro/scripts/load_sample_crypto_edge_data.py`
- `/Users/baitus/Downloads/crypto-bot-pro/scripts/collect_live_crypto_edge_snapshot.py`
- `/Users/baitus/Downloads/crypto-bot-pro/scripts/run_crypto_edge_collector_loop.py`
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

## Read-only live collection workflow

To collect live public funding, basis, and quote snapshots with the bundled example plan:

```bash
make collect-live-crypto-edges
```

This reads the collection plan from:

- `/Users/baitus/Downloads/crypto-bot-pro/sample_data/crypto_edges/live_collector_plan.json`

The collector remains read-only:

- it uses public market-data methods only
- it writes research snapshots into the local store
- it does not call any execution service
- it does not place, edit, or cancel orders

If a venue does not support a requested read-only method, the collector reports that in its check list and skips the affected rows.

## Repeating collection workflow

To keep the research store refreshed on a loop with the bundled plan:

```bash
make collect-live-crypto-edges-loop
```

To change the polling interval:

```bash
make collect-live-crypto-edges-loop CRYPTO_EDGE_INTERVAL_SEC=900
```

To request stop for the running loop:

```bash
make stop-live-crypto-edges-loop
```

The loop remains read-only:

- it repeatedly runs the public-data collector
- it writes status to the local runtime state
- it does not place, edit, or cancel orders
