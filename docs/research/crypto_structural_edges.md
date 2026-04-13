# Crypto Structural Edge Research Modules

These modules are research-only analytics.

Current scope:

- funding-rate carry summaries
- perp/spot basis summaries
- cross-venue dislocation summaries
- bundled sample snapshot loader for local demo/review
- read-only live snapshot collector driven by a JSON collection plan

Code:

- `<your-repo-path>/services/analytics/crypto_edges.py`
- `<your-repo-path>/services/analytics/crypto_edge_collector.py`
- `<your-repo-path>/storage/crypto_edge_store_sqlite.py`
- `<your-repo-path>/scripts/record_crypto_edge_snapshot.py`
- `<your-repo-path>/scripts/load_sample_crypto_edge_data.py`
- `<your-repo-path>/scripts/collect_live_crypto_edge_snapshot.py`
- `<your-repo-path>/scripts/run_crypto_edge_collector_loop.py`
- `<your-repo-path>/tests/test_crypto_edge_analytics.py`

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

- `<your-repo-path>/sample_data/crypto_edges/funding.json`
- `<your-repo-path>/sample_data/crypto_edges/basis.json`
- `<your-repo-path>/sample_data/crypto_edges/quotes.json`

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

- `<your-repo-path>/sample_data/crypto_edges/live_collector_plan.json`

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

To inspect the managed loop runtime:

```bash
make status-live-crypto-edges-loop
```

The loop remains read-only:

- it repeatedly runs the public-data collector
- it writes status to the local runtime state
- it writes managed PID/runtime metadata so the dashboard can detect dead or duplicate loops
- it does not place, edit, or cancel orders

The managed loop now refuses duplicate starts when an existing collector PID is still alive. If a prior loop dies unexpectedly, the runtime view marks that state explicitly instead of continuing to report a healthy running loop.
