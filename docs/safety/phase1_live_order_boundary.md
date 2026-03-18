# Phase 1 Live Order Boundary

This note captures the current Phase 1 safety posture around the live-order chokepoint.

## Helper Classification

| Helper | Role | Failure mode | Safety classification | Notes |
| --- | --- | --- | --- | --- |
| `services/execution/place_order.py::_killswitch_state()` | Kill switch and cooldown probe before any live order submit | Import, `is_on()`, snapshot, or cooldown parse failure | Fail-closed | Now logs probe failures and blocks with an explicit source-specific reason |
| `services/execution/place_order.py::_is_armed()` | Explicit live arming gate | Missing arming env | Fail-closed | Returns `not_armed`; caller blocks |
| `services/execution/place_order.py::_require_env_float()` | Required live risk limit loading | Missing, invalid, or non-finite env limit | Fail-closed | Rejects `nan`/`inf` as invalid |
| `services/execution/place_order.py::_exec_db_path()` | Execution DB location for risk and market-rules checks | Path resolution/setup issues | Best-effort helper behind fail-closed callers | Later checks block if risk snapshot or market prereqs cannot load |
| `services/execution/place_order.py::_venue_norm_for_market_rules()` | Normalize exchange ID for market-rules validation | Exchange ID read failure | Best-effort helper behind fail-closed callers | Unknown venue still flows into market-rules validation; Binance guard can still raise |
| `services/execution/place_order.py::_parse_order_amount()` | Finite positive amount validation | Bad numeric, non-finite, non-positive | Fail-closed | Added in Phase 1 |
| `services/execution/place_order.py::_parse_order_price()` | Finite positive price validation for limit orders | Missing limit price, bad numeric, non-finite, non-positive | Fail-closed | Added in Phase 1 |
| `services/execution/place_order.py::_load_latest_ops_risk_gate()` | Load optional ops risk-gate snapshot | Read/import failure | Best-effort or fail-closed depending on env policy | Enforced by `_enforce_ops_risk_gate()` using `CBP_OPS_RISK_GATE_FAIL_CLOSED` |

## Order-Path Coverage Matrix

| Path | Order capable | Hits `place_order.py` | Notes | Safe? |
| --- | --- | --- | --- | --- |
| `services/execution/exchange_client.py::submit_order()` | Yes | Yes | Uses `place_order(...)` directly before exchange submit | Yes |
| `services/execution/live_exchange_adapter.py::submit_order()` | Yes | Yes | Uses `place_order(...)` directly | Yes |
| `services/execution/live_exchange_adapter.py::create_order()` | Yes | Yes | Compatibility alias that delegates to `submit_order()` | Yes |
| `services/execution/order_manager.py::submit_limit()` | Yes | Yes | Uses `place_order_async(...)` | Yes |
| `services/execution/order_manager.py::cancel_and_replace()` | Replace path | Yes for replacement leg | Cancel bypasses chokepoint, replacement leg uses `submit_limit()` -> `place_order_async(...)` | Yes for new order creation |
| `services/execution/order_router.py::place_order_idempotent()` | Yes | Yes | Routes dry-run/live submit through `_place_order_ccxt()` -> `place_order(...)` | Yes |
| `services/execution/intent_consumer.py` | Yes | Indirect yes | Uses `LiveExchangeAdapter.submit_order(...)`, which routes through `place_order.py` | Yes, based on current adapter wiring |
| `services/execution/live_intent_consumer.py` | Yes | Indirect yes | Uses `LiveExchangeAdapter.submit_order(...)`, which routes through `place_order.py` | Yes, based on current adapter wiring |
| `services/execution/intent_executor.py::execute_one()` | Yes | Indirect yes | Delegates to adapter `place_order(req)`; live adapter paths route through `place_order.py` | Yes, based on current adapter wiring |
| `scripts/cancel_intent.py` | Cancel only | No | Uses `ExchangeClient(..., sandbox=False)` for cancel flow, not order creation | Not in scope for create-order chokepoint |
| `scripts/reconcile_order_dedupe.py` | Reconcile/fetch only | No | Uses `ExchangeClient(..., sandbox=False)` for reconciliation | Not in scope for create-order chokepoint |
| `services/execution/live_executor.py` | Live client creation | Indirect | Builds `ExchangeClient(..., sandbox=False)`; actual order creation still flows through exchange client submit path | Yes, based on current exchange-client wiring |

## Enforcement

- Raw exchange `create_order` is still only allowed in `services/execution/place_order.py`.
- `scripts/verify_no_direct_create_order.py` is the repo-level guard.
- `tests/test_no_direct_create_order.py` mirrors the same guard in test form.
- `tests/test_live_script_contracts.py` locks the current `sandbox=False` scripts to the approved read-only/cancel set.

## Scripts Using `sandbox=False`

| Script | Classification | Reason |
| --- | --- | --- |
| `scripts/cancel_intent.py` | Cancel flow | Uses `ExchangeClient.cancel_intent(...)`; does not submit new orders |
| `scripts/reconcile_order_dedupe.py` | Read-only reconcile | Uses `fetch_open_orders(...)` and `fetch_order(...)`; does not submit new orders |

## Remaining Phase 1 Risks

1. Cancel/edit/replace safety is not governed by the same final-order chokepoint because the critical rule here is specific to raw order creation.
2. `services/execution/intent_executor.py::_live_allowed()` still uses a best-effort kill/cooldown probe separate from `place_order.py`; it is an outer gate, not the final authority.
3. Any future adapter or recovery path that can create an order must keep routing into `services/execution/place_order.py` or the guard script/test will need to be updated immediately.
