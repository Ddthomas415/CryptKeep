# Audit Failure Ledger

BRANCH: fix/live-queue-atomic-claim
COMMIT: 9592d5b8a3bd414fefa9e90a6054e8f4c2288afa

## Failures

| Audit | ID | Title | Status | Proof Command | Notes |
|---|---|---|---|---|---|
| 1 | A1-F1 | TBD | UNVERIFIED | TBD | TBD |
| 2 | A2-F1 | live queue update_status result ignored by state_authority callers | RESOLVED | pytest tests/test_live_intent_consumer_order_store_gating.py tests/test_live_reconciler_order_store_gating.py tests/test_live_reconciler_submit_unknown_recovery.py tests/test_live_state_authority_write_result.py -q && python3 -m py_compile services/execution/intent_consumer.py services/execution/live_intent_consumer.py services/execution/live_reconciler.py services/execution/state_authority.py | 14 focused tests pass. Order-store writes, risk-rejection counters, queued marker, and live_reconciler canceled/rejected transitions now require persisted queue state. |
| 3 | A3-F1 | live-intent path lacks durable dedupe claim before submit | RESOLVED | pytest tests/test_live_intent_consumer_duplicate_prevention.py -q | Durable pre-submit dedupe claim added; restart duplicate-submit regression passes. |
| 4 | A4-F1 | live_reconciler misattributes same-symbol fills | RESOLVED | pytest tests/test_live_reconciler_fill_attribution.py tests/test_live_reconciler_order_store_gating.py tests/test_live_reconciler_submit_unknown_recovery.py tests/test_live_state_authority_write_result.py -q | Same-symbol fill attribution now requires trade order/client ID match. Cursor safety remains separate/unverified. |
| 5 | A5-F1 | TBD | UNVERIFIED | TBD | TBD |
| 6 | A6-F1 | TBD | UNVERIFIED | TBD | TBD |

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
