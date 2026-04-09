# Private Connectivity and Read-Only Lifecycle Evidence

Status: PARTIAL

## Venue
- coinbase

## Environment
- repo venv: `./.venv/bin/python`
- credentials source: OS keyring
- credential presence: confirmed

## Private connectivity
Confirmed successful private authenticated connectivity and permission-style probes for:
- balance access
- open orders access
- trade history access

## Read-only lifecycle probe
Confirmed:
- authenticated `fetch_open_orders(symbol=...)` succeeded
- authenticated `fetch_my_trades(...)` via lifecycle boundary succeeded

Observed results during probe:
- `open_orders_count: 0`
- `trade_count: 0`

## Interpretation
This proves authenticated read-only lifecycle access for the chosen venue.
It does not yet prove the full lifecycle runtime flow because no fresh order was placed, fetched by id, cancelled, and post-cancel verified.
For the current operator environment, this is also the maximum reachable proof currently available without a supported reachable sandbox/testnet venue.

## Current venue constraints
- Coinbase:
  - authenticated read-only proof is complete
  - the current repo/client combination does not expose a working CCXT sandbox URL, so this proof used `sandbox=False`
- Binance:
  - credentials were made visible through the approved keyring path
  - the Binance testnet/private endpoint returned HTTP `451` from the current location on April 8, 2026
- Gate.io:
  - not currently usable from the operator environment, so no authenticated proof was attempted

## Remaining proof required
- sandbox/private order placement
- order fetch/status reconciliation for the placed order
- cancellation
- post-cancel verification
