# Live Lifecycle Gap Note

Status: READY_FOR_INDEPENDENT_REVIEW

## Objective
Record the remaining live lifecycle authority state on the root runtime path after the active open-order reconcile path was boundary-routed.

## Confirmed landed change
The previously remaining active open-order reconcile bypass on the canonical root-runtime path has been boundary-routed.

Updated `services/execution/live_executor.py`:

- `reconcile_open_orders(...)` -> `_fetch_open_orders_for_reconcile(...)`
- owned reconcile sessions now route through:
  - `fetch_open_orders_via_boundary(...)`

Current active live reconcile helpers that are already boundary-routed:

- `_fetch_order_for_reconcile(...)` -> `fetch_order_via_boundary(...)`
- `_fetch_trades_for_reconcile(...)` -> `fetch_my_trades_via_boundary(...)`
- `_fetch_open_orders_for_reconcile(...)` -> `fetch_open_orders_via_boundary(...)`

## Boundary surface
The active lifecycle boundary now covers:

- `fetch_order_via_boundary(...)`
- `fetch_my_trades_via_boundary(...)`
- `fetch_open_orders_via_boundary(...)`
- `cancel_order_via_boundary(...)`

## Updated status
Active live-executor lifecycle reads are now boundary-routed for:
- fetch_order
- fetch_my_trades
- fetch_open_orders

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
The repo's lifecycle documentation now describes the canonical active live fetch/reconcile path as lifecycle-boundary governed:

- `docs/safety/lifecycle_matrix.md:15`
- `docs/safety/lifecycle_matrix.md:16`
- `docs/safety/lifecycle_matrix.md:19`
- `docs/safety/lifecycle_matrix.md:20`
- `docs/safety/lifecycle_matrix.md:21`
- `docs/safety/lifecycle_matrix.md:32`

## Remaining caution
Lifecycle authority and submit authority are still separate operational surfaces.
This note no longer records an active open-order reconcile bypass on the canonical root-runtime path; it records that the active path has been narrowed onto the governed lifecycle boundary.

## Review evidence
- `services/execution/live_executor.py`
- `services/execution/lifecycle_boundary.py`
- `docs/safety/lifecycle_matrix.md`
- `tests/test_execution_boundary_regression.py`
- `tests/test_live_executor_latency_safety_integration.py`
- `tests/test_lifecycle_matrix_doc.py`

## Risk
High

## Review lane
READY_FOR_INDEPENDENT_REVIEW
