# Audit Failure Ledger

BRANCH: fix/live-queue-atomic-claim
COMMIT: 9592d5b8a3bd414fefa9e90a6054e8f4c2288afa

## Failures

| Audit | ID | Title | Status | Proof Command | Notes |
|---|---|---|---|---|---|
| 1 | A1-F1 | direct create_order authority must remain centralized in place_order.py | VERIFIED_PASS_WITH_SCANNER_LIMITATION | python3 scripts/verify_no_direct_create_order.py --print && python3 -m unittest tests/test_no_direct_create_order.py tests/test_verify_no_direct_create_order_script.py | No runtime create_order bypass found. Direct exchange order authority remains centralized in services/execution/place_order.py. Known bypass patterns are covered by scanner/tests. Residual limitation: static analysis cannot prove arbitrary runtime dispatch. |
| 2 | A2-F1 | live queue update_status result ignored by state_authority callers | RESOLVED | pytest tests/test_live_intent_consumer_order_store_gating.py tests/test_live_reconciler_order_store_gating.py tests/test_live_reconciler_submit_unknown_recovery.py tests/test_live_state_authority_write_result.py -q && python3 -m py_compile services/execution/intent_consumer.py services/execution/live_intent_consumer.py services/execution/live_reconciler.py services/execution/state_authority.py | 14 focused tests pass. Order-store writes, risk-rejection counters, queued marker, and live_reconciler canceled/rejected transitions now require persisted queue state. |
| 3 | A3-F1 | live-intent path lacks durable dedupe claim before submit | RESOLVED | pytest tests/test_live_intent_consumer_duplicate_prevention.py -q | Durable pre-submit dedupe claim added; restart duplicate-submit regression passes. |
| 4 | A4-F1 | live_reconciler misattributes same-symbol fills | RESOLVED | pytest tests/test_live_reconciler_fill_attribution.py tests/test_live_reconciler_order_store_gating.py tests/test_live_reconciler_submit_unknown_recovery.py tests/test_live_state_authority_write_result.py -q | Same-symbol fill attribution now requires trade order/client ID match. Cursor safety remains separate/unverified. |
| 5 | A5-F1 | live_reconciler trade cursor may skip late same-symbol fills | NOT_REPRODUCED | pytest tests/test_live_reconciler_cursor_safety.py -q | Cursor does not advance for unmatched same-symbol trades after A4 attribution filter; focused proof passes. |
| 6 | A6-F1 | paper submit_order can fill in same call | CLASSIFIED_HONESTY_GAP | pytest tests/test_paper_engine_honesty.py -q | PaperEngine.submit_order immediately evaluates open orders; same-call fills are proven and should not be treated as live-equivalent. |

## A2-F1 remaining caller classification

### Order-store write gated
- services/execution/intent_consumer.py:197
- services/execution/intent_consumer.py:214
- services/execution/live_reconciler.py:156
- services/execution/live_reconciler.py:246
- services/execution/live_reconciler.py:264
- services/execution/live_reconciler.py:296
- services/execution/live_reconciler.py:347
- services/execution/live_intent_consumer.py:166
- services/execution/live_intent_consumer.py:196
- services/execution/live_intent_consumer.py:231
- services/execution/live_intent_consumer.py:254
- services/execution/live_intent_consumer.py:282
- services/execution/live_intent_consumer.py:307

### Non-order-store transition still ignored
N/A

### Tests only
- tests/test_live_queue_submit_owner_authority.py
- tests/test_live_state_authority_write_result.py
- tests/test_live_reconciler_state_authority.py

## A1-F1 remaining authority classification

### Verified pass
- `python3 scripts/verify_no_direct_create_order.py --print` returned `{'ok': True, 'violations': 0}`.
- `python3 -m unittest tests/test_no_direct_create_order.py tests/test_verify_no_direct_create_order_script.py` passed.

### Allowed direct authority
- `services/execution/place_order.py` is the only allowed direct `.create_order(...)` authority.

### Classified non-runtime / skipped
- `tools/phase83_apply.py` contains direct create_order strings inside patch-template text and is skipped by the verifier via `SKIP_DIRS`.

### Tests-only wrapper surface
- `tests/test_live_execution_wiring.py` uses `getattr(ad, "create_order")`; this is test coverage of the adapter surface, not runtime exchange placement.

### Remaining status
- No runtime direct `create_order` violation reproduced.
- Read-only trace performed: `grep` for `getattr(..., "create_order")` in services hit only test classification.
- `grep` for `create_order` in services showed direct exchange call only in `services/execution/place_order.py`.
- Scanner covers: literal `.create_order(`, `getattr(..., "create_order")`, `createOrder`, constant alias / concat test cases.
- Residual limitation: static analysis cannot prove arbitrary runtime dispatch in every possible form.
- Current residual risk is acceptable for this phase.
