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
Root cause: live_enabled_and_armed() requires one of CBP_LIVE_ARMED / CBP_LIVE_ENABLED / ENABLE_LIVE_TRADING / CBP_EXECUTION_ARMED / LIVE_TRADING env vars to be set. resume_if_safe() does not set any of them. The reconciler looped 8 times but never passed the arming gate, so the inner fetch_order path never executed. Stale intent remained submitted throughout. This is a gap between the resume_if_safe arming flow and the env-var arming gate in live_reconciler.

## 7. Market quality block drill
Result: PASS (guard-level)
Notes: market_quality_guard.check() returned ok=False / reason=stale_tick at age_sec=610. Gate confirmed working. Strict proof not collected.
