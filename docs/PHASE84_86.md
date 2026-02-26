# Phases 84–86

## Phase 84 — Idempotent cancel/retry + strict order param validation
- Added `services/execution/order_params.py`:
  - allowlists per-exchange params
  - validates `timeInForce` + `postOnly`
  - injects venue idempotency key (client order id)
- Patched `ExchangeClient.submit_order()` to call `prepare_ccxt_params(...)`.
- Added `ExchangeClient.cancel_intent(...)` + `scripts/cancel_intent.py`.
- Patched `OrderDedupeStore.claim_before_submit()` to allow **bounded** resubmit when a prior submit is `unknown`:
  - `CBP_UNKNOWN_RESUBMIT_AFTER_S` (default 45s)
  - `CBP_UNKNOWN_RESUBMIT_MAX` (default 1)

## Phase 85 — Resolve unknown submissions by scanning open orders
- Added `reconcile_open_orders(...)` and call it at the start of `reconcile_live()` to attach `remote_order_id` for unknown rows.

## Phase 86 — Script import bootstrap
- Patched key scripts to insert repo root into `sys.path` (prevents `No module named 'services'`).

## Notes
- LIVE remains wizard-gated + risk-gated.
- If market rules fetch fails, orders fail closed (safe).
