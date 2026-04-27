# Audit Failure Ledger

BRANCH: fix/live-queue-atomic-claim
COMMIT: 9592d5b8a3bd414fefa9e90a6054e8f4c2288afa

## Failures

| Audit | ID | Title | Status | Proof Command | Notes |
|---|---|---|---|---|---|
| 1 | A1-F1 | TBD | UNVERIFIED | TBD | TBD |
| 2 | A2-F1 | live queue update_status result ignored by state_authority callers | PARTIAL | pytest tests/test_live_intent_consumer_order_store_gating.py tests/test_live_reconciler_order_store_gating.py tests/test_live_reconciler_submit_unknown_recovery.py tests/test_live_state_authority_write_result.py -q && python3 -m py_compile services/execution/intent_consumer.py | 14 focused tests pass. live_reconciler and live_intent_consumer order-store writes are gated. legacy intent_consumer order-store writes patched and compile, but focused regressions are still missing. Non-order-store transition callers remain unresolved. |
| 3 | A3-F1 | TBD | UNVERIFIED | TBD | TBD |
| 4 | A4-F1 | TBD | UNVERIFIED | TBD | TBD |
| 5 | A5-F1 | TBD | UNVERIFIED | TBD | TBD |
| 6 | A6-F1 | TBD | UNVERIFIED | TBD | TBD |
