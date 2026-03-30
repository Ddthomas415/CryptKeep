# Live Lifecycle Gap Note

Status: OPEN

## Objective
Record the currently active live lifecycle authority gap on the root runtime path without changing runtime behavior.

## Confirmed active bypass callers
The active live reconcile path still performs direct lifecycle reads from `services/execution/live_executor.py`:

- `live_executor.py:617` -> `client.fetch_order(...)`
- `live_executor.py:634` -> `fetch_my_trades(...)`
- `live_executor.py:773` -> `client.fetch_open_orders(...)`

## Direct venue methods behind those callers
Those calls resolve to thin direct exchange methods in `services/execution/exchange_client.py`:

- `exchange_client.py:220` -> `def fetch_order(...)`
- `exchange_client.py:227` -> `def fetch_open_orders(...)`
- `exchange_client.py:234` -> `def fetch_my_trades(...)`

## Updated status
Active live-executor lifecycle reads have now been boundary-routed for:
- fetch_order
- fetch_open_orders
- fetch_my_trades

Current classification from repo reachability checks:
- `fill_confirmation.py` still contains a direct `fetch_order(...)` call
- but no active runtime callers were shown in the latest caller grep
- `live_exchange_adapter.py` fetch methods are boundary-routed wrappers

Additional interface cleanup landed:
- `services/execution/exchange_client.py` now implements `find_order_by_client_oid(...)`
- `services/execution/live_exchange_adapter.py` now implements `find_order_by_client_oid(...)`
- this closes the earlier visible interface mismatch where call sites existed without a visible implementation
- commit landed:
  - `0c7f40c` — `execution: add find_order_by_client_oid to client and adapter`

## Current repo truth
The repo's lifecycle documentation already describes this as partial lifecycle hardening rather than full closure:

- `docs/safety/lifecycle_matrix.md:15`
- `docs/safety/lifecycle_matrix.md:16`
- `docs/safety/lifecycle_matrix.md:19`
- `docs/safety/lifecycle_matrix.md:20`
- `docs/safety/lifecycle_matrix.md:21`
- `docs/safety/lifecycle_matrix.md:32`

## Why this is still a blocker
Submit-path authority and lifecycle-path authority are not yet equivalent.
The active live reconcile path still depends on direct exchange lifecycle reads instead of one fully governed lifecycle boundary.

## Close condition
One of the following must be true:

1. All active live fetch/reconcile/cancel lifecycle paths route through one governed lifecycle boundary.

or

2. The supported live path is explicitly narrowed and documented so the bypassed paths are out of scope.

## Risk
High

## Review lane
READY_FOR_INDEPENDENT_REVIEW
