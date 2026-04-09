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

## Direct network probes
Additional direct probe evidence captured on April 9, 2026:

- Binance testnet public ping:
  - `curl https://testnet.binance.vision/api/v3/ping`
  - returned HTTP `451`
  - response body: service unavailable from a restricted location
- Gate.io testnet futures contracts:
  - `curl https://fx-api-testnet.gateio.ws/api/v4/futures/usdt/contracts`
  - returned HTTP `502`
  - upstream server: `openresty`
- Traceroute to `testnet.binance.vision`:
  - resolved and routed beyond local/DNS layers
  - this strengthens the current classification that the Binance failure is upstream venue restriction, not a local name-resolution problem

Interpretation:
- Binance testnet is externally restricted from the current operator environment
- Gate.io testnet is currently not usable from the current operator environment
- this environment still lacks one reachable supported sandbox/testnet venue for lifecycle proof

## Remaining proof required
- sandbox/private order placement
- order fetch/status reconciliation for the placed order
- cancellation
- post-cancel verification
