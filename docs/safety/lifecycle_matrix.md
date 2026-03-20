# Lifecycle Matrix

| File | Function | Action Type | Uses Final Submit Boundary? | Direct Exchange Call? | Legacy? | Reviewed? | Notes |
|---|---|---|---|---|---|---|---|
| `services/execution/live_exchange_adapter.py` | `submit_order` | submit | Yes | No | No | Yes | Calls `place_order(...)` |
| `services/execution/live_exchange_adapter.py` | `cancel_order` | cancel | No | Yes | No | Yes | Direct `self.ex.cancel_order(...)` |
| `services/execution/live_exchange_adapter.py` | `fetch_order` | fetch | No | Yes | No | Yes | Direct `self.ex.fetch_order(...)` |
| `services/execution/live_exchange_adapter.py` | `fetch_my_trades` | fetch | No | Yes | No | Yes | Direct `self.ex.fetch_my_trades(...)` |
| `services/execution/order_manager.py` | async submit helper | submit | Yes | No | No | Yes | Uses `place_order_async(...)` |
| `services/execution/order_manager.py` | cancel helper | cancel | No | Yes | No | Yes | Direct `ex.cancel_order(...)` |
| `services/execution/order_manager.py` | `cancel_and_replace` | cancel/replace | Partial | Yes | No | Yes | Cancel leg is direct `ex.cancel_order(...)`; replace leg re-enters submit boundary via `submit_limit(...)` |
| `services/execution/exchange_client.py` | `submit_order` | submit | Yes | No | Yes | Yes | Legacy/non-preferred helper; uses `place_order(...)` |
| `services/execution/exchange_client.py` | `cancel_intent` | cancel | No | Yes | Yes | Yes | Direct `ex.cancel_order(...)`; lifecycle path separate from submit authority |
| `services/execution/exchange_client.py` | `fetch_order` | fetch | No | Yes | Yes | Yes | Direct `ex.fetch_order(...)` |
| `services/execution/exchange_client.py` | `fetch_open_orders` | fetch | No | Yes | Yes | Yes | Direct `ex.fetch_open_orders(...)` |
| `services/execution/exchange_client.py` | `fetch_my_trades` | fetch | No | Yes | Yes | Yes | Direct `ex.fetch_my_trades(...)` |
| `services/execution/live_reconciler.py` | reconcile loop | reconcile | No | Yes | No | Yes | Best-effort polling/reconcile worker; not submit authority |
| `services/execution/reconciliation.py` | `reconcile_spot_position` | reconcile | No | Yes | No | Yes | Balance-based reconcile path |
| `services/execution/fill_confirmation.py` | `wait_for_order_final` | reconcile/fetch | No | Yes | No | Yes | Poll helper around `fetch_order(...)` |
| `services/execution/place_order.py` | `place_order` | submit authority | Yes | N/A | No | Yes | Final raw-order boundary |
| `services/execution/place_order.py` | `place_order_async` | submit authority | Yes | N/A | No | Yes | Final async raw-order boundary |

## Summary

- Raw order submission is centralized behind `services/execution/place_order.py`.
- Cancel paths are separate and use direct exchange calls.
- `cancel_and_replace` is a mixed lifecycle path: direct cancel followed by boundary-governed resubmit.
- Fetch/reconcile paths are separate operational surfaces and are not governed by the final submit authority.
- `services/execution/exchange_client.py` remains a legacy/non-preferred lifecycle helper.
- Submit safety is stronger and better proven than cancel/reconcile lifecycle safety.
- No dedicated exchange-native amend/edit path was found in `services/execution`; replace behavior is currently cancel-then-resubmit.
