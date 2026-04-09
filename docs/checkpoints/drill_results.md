# Drill Results

## 1. Restart drill
Result:
Notes:

## 2. Tick publisher stale-data drill
Result:
Notes:

## 3. disable_live_now drill
Result:
Notes:

## 4. resume_if_safe drill
Result:
Notes:

## 5. preflight failure / restore drill
Result:
Notes:

## 6. stale intent drill
Result:
Notes:

## 7. market_quality_block drill
Result:
Notes:

## 6. Stale intent drill
Result: FAIL
Notes: Synthetic stale live intent remained `submitted` despite being stale, armed, and having an invalid exchange_order_id. Verified `fetch_order()` raises BadRequest. Verified DB write path works manually. Reconciler did not transition row to `error`. This is a code-path bug in live_reconciler, not operator error.

## 7. Market quality block drill
Result: PASS (guard-level)
Notes: market_quality_guard.check() returned ok=False / reason=stale_tick at age_sec=610. Gate confirmed working. Stricter proof (pending intents with block reason) not collected.

## 6. Stale intent drill
Result: FAIL
Root cause at the time: live_enabled_and_armed() accepted multiple legacy env signals while resume_if_safe() restored only persisted arm state, not the canonical execution arming env. The reconciler looped 8 times but never passed the actual execution arming contract, so the inner fetch_order path never executed. Stale intent remained submitted throughout. This exposed a mismatch between resume flow and final execution arming.

## 7. Market quality block drill
Result: PASS (guard-level)
Notes: market_quality_guard.check() returned ok=False / reason=stale_tick at age_sec=610. Gate confirmed working. Strict proof not collected.
