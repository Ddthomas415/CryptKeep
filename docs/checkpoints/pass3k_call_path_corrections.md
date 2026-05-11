# Pass 3K — Call Path Verification and Corrections

**Date:** 2026-05-11
**Pass:** 3K — re-verification of assertions made without tracing call paths
**Status:** COMPLETE

---

## Correction 1 — H6 scope: FOUR files not three

evidence_shared.py:110 was missed. It has its own _normalize_strategy_name,
identical to evidence_cycle.py, same blind spot.

Full correct list:
1. services/backtest/evidence_cycle.py:110 — own copy, must fix
2. services/backtest/evidence_shared.py:110 — own copy, **MISSED, must fix**
3. services/analytics/strategy_feedback.py:28 — own copy, must fix
4. services/backtest/leaderboard.py — default_strategy_candidates() missing sma_200_trend
5. services/backtest/evidence_paper.py:25 — imports from evidence_cycle, fixed transitively

Verified: grep for 'sma_200|es_daily_trend' in evidence_shared.py returns nothing.

---

## Correction 2 — intent_queue autocommit assertion was wrong

Previous claim: intent_queue_sqlite.py autocommit = multi-step writes not atomic.

Corrected: upsert_intent and update_status both use explicit
BEGIN IMMEDIATE / COMMIT / ROLLBACK (lines 101, 128, 252, 279, 283).

The isolation_level=None connection default is overridden by explicit transactions.
Writes ARE atomic. Remove intent_queue_sqlite from autocommit-gap list.

Actual autocommit-gap stores (no explicit transactions confirmed):
position_state_sqlite, strategy_state_sqlite, reconciliation_store_sqlite,
portfolio_store_sqlite.

---

## Correction 3 — Stub functions have no production callers (safe)

Previous claim: implied risk from stubs returning empty.

Verified:
- exit_rules.evaluate_exit() — grep across services/: ZERO production callers
- live_fill_mapper.map_order_to_fills() — grep across services/: ZERO production callers

Both are dead code. No silent dependency. Risk drops from Medium to Low.

---

## Correction 4 — IntentQueueSQLite is canonical for the active soak path

Pipeline -> IntentWriter.create_intent() -> IntentQueueSQLite().upsert_intent()
Paper mode executor reads from IntentQueueSQLite.
execution_store_sqlite.py tracks execution state separately.
LiveIntentQueueSQLite is live mode only.

---

## Correction 5 — Paper mode uses executor not intent_consumer

desired_services() in run_bot_runner.py:
- mode='paper', live_enabled=False -> appends 'executor'
- mode='live' or live_enabled=True -> appends 'intent_consumer'

Current soak: executor service. intent_consumer not running.

---

## Corrections summary

| Assertion | Original | Corrected |
|---|---|---|
| H6 scope | 3 files | **4 files** (evidence_shared missed) |
| intent_queue autocommit | Medium risk | Low (explicit transactions present) |
| exit_rules stub risk | Medium | Low (no callers) |
| live_fill_mapper stub risk | Medium | Low (no callers) |
| H9 priority | P0 | P3 (wrong supervisor module) |
| Canonical intent store | Unclear | IntentQueueSQLite |
| Paper soak service | Not traced | executor (not intent_consumer) |
