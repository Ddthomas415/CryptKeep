# No direct create_order policy (Phase 209)

Rule:
- `ex.create_order(...)` MUST ONLY appear in:
  - services/execution/place_order.py

Why:
- Ensures order_guards + idempotency + audit logging are always applied.

Verify:
- CLI:
  python scripts/verify_no_direct_create_order.py --print
- Tests:
  python -m unittest
