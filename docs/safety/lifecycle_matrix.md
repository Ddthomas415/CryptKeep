# Lifecycle Matrix

| File | Function | Action Type | Uses Final Submit Boundary? | Direct Exchange Call? | Legacy? | Reviewed? | Notes |
|---|---|---|---|---|---|---|---|
| `services/execution/live_exchange_adapter.py` | `submit_order` | submit | Yes | No | No | Yes | Calls `place_order(...)` |
| `services/execution/lifecycle_boundary.py` | `cancel_order_via_boundary` | cancel | No | Yes | No | Yes | Governed lifecycle cancel boundary for active paths |
| `services/execution/lifecycle_boundary.py` | `fetch_order_via_boundary` | fetch | No | Yes | No | Yes | Governed lifecycle fetch boundary for active paths |
| `services/execution/lifecycle_boundary.py` | `fetch_my_trades_via_boundary` | fetch | No | Yes | No | Yes | Governed lifecycle trade-reconcile boundary for active paths |
| `services/execution/live_exchange_adapter.py` | `cancel_order` | cancel | No | No | No | Yes | Routes through `lifecycle_boundary.cancel_order_via_boundary(...)` |
| `services/execution/live_exchange_adapter.py` | `fetch_order` | fetch | No | No | No | Yes | Routes through `lifecycle_boundary.fetch_order_via_boundary(...)` |
| `services/execution/live_exchange_adapter.py` | `fetch_my_trades` | fetch | No | No | No | Yes | Routes through `lifecycle_boundary.fetch_my_trades_via_boundary(...)` |
| `services/execution/order_manager.py` | async submit helper | submit | Yes | No | No | Yes | Uses `place_order_async(...)` |
| `services/execution/order_manager.py` | cancel helper | cancel | No | No | No | Yes | Routes through `lifecycle_boundary.cancel_order_async_via_boundary(...)` |
| `services/execution/order_manager.py` | `cancel_and_replace` | cancel/replace | Partial | No | No | Yes | Cancel leg routes through lifecycle boundary; replace leg re-enters submit boundary via `submit_limit(...)` |
| `services/execution/live_executor.py` | `reconcile_live` | reconcile/fetch | No | Yes | No | Yes | Uses `ExchangeClient.fetch_order(...)` and `fetch_my_trades(...)` directly |
| `services/execution/live_executor.py` | `reconcile_open_orders` | reconcile/fetch | No | Yes | No | Yes | Uses `ExchangeClient.fetch_open_orders(...)` directly |
| `services/execution/exchange_client.py` | `submit_order` | submit | Yes | No | Yes | Yes | Legacy/non-preferred helper; uses `place_order(...)` |
| `services/execution/exchange_client.py` | `cancel_intent` | cancel | No | Yes | Yes | Yes | Direct `ex.cancel_order(...)`; lifecycle path separate from submit authority |
| `services/execution/exchange_client.py` | `fetch_order` | fetch | No | Yes | Yes | Yes | Direct `ex.fetch_order(...)` |
| `services/execution/exchange_client.py` | `fetch_open_orders` | fetch | No | Yes | Yes | Yes | Direct `ex.fetch_open_orders(...)` |
| `services/execution/exchange_client.py` | `fetch_my_trades` | fetch | No | Yes | Yes | Yes | Direct `ex.fetch_my_trades(...)` |
| `services/execution/live_reconciler.py` | reconcile loop | reconcile | No | No | No | Yes | Best-effort polling/reconcile worker using adapter-governed lifecycle fetch paths |
| `services/execution/reconciliation.py` | `reconcile_spot_position` | reconcile | No | Yes | No | Yes | Balance-based reconcile path |
| `services/execution/fill_confirmation.py` | `wait_for_order_final` | reconcile/fetch | No | Yes | No | Yes | Poll helper around `fetch_order(...)` |
| `services/execution/place_order.py` | `place_order` | submit authority | Yes | N/A | No | Yes | Final raw-order boundary |
| `services/execution/place_order.py` | `place_order_async` | submit authority | Yes | N/A | No | Yes | Final async raw-order boundary |

## Summary

- Raw order submission is centralized behind `services/execution/place_order.py`.
- Active adapter and order-manager cancel/fetch paths now funnel through `services/execution/lifecycle_boundary.py`.
- `services/execution/live_executor.py` still performs reconcile fetches through `services/execution/exchange_client.py`.
- `cancel_and_replace` is still a mixed lifecycle path: lifecycle-boundary cancel followed by boundary-governed resubmit.
- Fetch/reconcile paths remain separate operational surfaces and are not yet fully governed by the lifecycle boundary.
- `services/execution/exchange_client.py` remains a legacy/non-preferred lifecycle helper.
- Submit safety is stronger and better proven than cancel/reconcile lifecycle safety.
- No dedicated exchange-native amend/edit path was found in `services/execution`; replace behavior is currently cancel-then-resubmit.
