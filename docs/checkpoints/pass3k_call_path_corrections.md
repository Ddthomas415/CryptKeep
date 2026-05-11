# Pass 3K — Call Path Verification and Corrections

**Date:** 2026-05-11
**Pass:** 3K — systematic re-verification of all High finding assertions
**Status:** COMPLETE

---

## What this pass does

Every High finding and key Medium finding was re-verified by grep on the soak
branch before this document was written. Results are recorded with the exact
evidence command and output.

---

## Correction 1 — H6 scope: FOUR independent files

evidence_shared.py:110 was missed in earlier passes. It has its own
_normalize_strategy_name, identical to evidence_cycle.py, same blind spot.

Full correct scope:
1. services/backtest/evidence_cycle.py:110 — own copy, must fix
2. services/backtest/evidence_shared.py:110 — own copy, MISSED, must fix
3. services/analytics/strategy_feedback.py:28 — own copy, must fix
4. services/backtest/leaderboard.py — default_strategy_candidates() missing sma_200_trend
5. services/backtest/evidence_paper.py:25 — imports from evidence_cycle, fixed transitively

Verified: grep "sma_200|es_daily_trend" evidence_shared.py returns nothing.

---

## Correction 2 — strategy_registry.py is NOT a normalization (overcounted)

Previous claim: 4 strategy name normalizations including strategy_registry.py.

Corrected: strategy_registry.py is a dispatch registry mapping strategy name
to signal function. Line 22 already has: "sma_200_trend": es_daily_trend_signal.

It is NOT a normalization and is NOT part of the H6 problem.
It already correctly handles sma_200_trend.

Correct count: 3 independent normalization implementations:
1. evidence_cycle.py:110
2. evidence_shared.py:110 (missed)
3. strategy_feedback.py:28

P2-1 should consolidate these 3, not strategy_registry.

---

## Correction 3 — intent_queue autocommit assertion was wrong

Previous claim: intent_queue_sqlite.py autocommit means writes not atomic.

Corrected: upsert_intent uses explicit BEGIN IMMEDIATE/COMMIT/ROLLBACK
(lines 101, 128, 201, 252, 279, 283). Writes ARE atomic despite isolation_level=None.

Remaining autocommit-gap stores (no explicit transactions confirmed by grep):
position_state_sqlite, strategy_state_sqlite, reconciliation_store_sqlite,
portfolio_store_sqlite.

---

## Correction 4 — Stub functions have no production callers (safe)

Verified by grep across all of services/:
- exit_rules.evaluate_exit() — ZERO production callers. Dead code.
- live_fill_mapper.map_order_to_fills() — ZERO production callers. Dead code.

Risk drops from Medium to Low. Nothing silently depends on either stub.

---

## Correction 5 — IntentQueueSQLite is canonical for active soak path

Pipeline: es_daily_trend_pipeline -> IntentWriter.create_intent()
IntentWriter -> IntentQueueSQLite().upsert_intent() (line 95)
Paper executor reads from IntentQueueSQLite.
execution_store_sqlite.py tracks execution state separately.
LiveIntentQueueSQLite is live mode only (intent_consumer not running in paper).

---

## Correction 6 — Paper mode uses executor not intent_consumer

desired_services() in run_bot_runner.py line 108-113:
- paper mode (not live_enabled) -> appends "executor"
- live mode or live_enabled -> appends "intent_consumer"

Current soak is paper mode. intent_consumer not running.

---

## Correction 7 — H9 supervisor (operator-confirmed)

services/supervisor/supervisor.py is NOT the active soak control path.
Active soak uses run_bot_runner.py + services/runtime/process_supervisor.py.
run_bot_runner.py MANAGED_SERVICES includes pipeline, executor, intent_consumer.
bot_status.py:14 reads from services/runtime/process_supervisor.
H9 reclassified P0 -> P3 (legacy supervisor cleanup).

---

## Verified findings (all confirmed by grep on soak branch)

| Finding | Claim | Verification |
|---|---|---|
| H4 governance dead code | can_transition/decide/should_invalidate never called | CONFIRMED zero callers |
| H5 resume_if_safe | Sets arming but not live_enabled config | CONFIRMED no config write |
| H7 direct_origin_block | Never called in production | CONFIRMED test file only |
| H8 live_safety_state | Returns kill_switch:False when absent | CONFIRMED line 22 |
| P1-6 ohlcv timeout | No explicit timeout | CONFIRMED signal_replay->make_exchange no timeout |
| Autocommit stores (4) | No explicit transactions | CONFIRMED all 4 stores |
| exit_rules stub | No callers | CONFIRMED zero production callers |
| live_fill_mapper stub | No callers | CONFIRMED zero production callers |

---

## Corrections summary

| Assertion | Original | Corrected |
|---|---|---|
| H6 scope | 3 files | 4 files (evidence_shared missed) |
| Strategy name normalizations | 4 (incl strategy_registry) | 3 (registry is dispatch not normalization) |
| intent_queue autocommit | Medium risk | Low (explicit transactions present) |
| exit_rules stub risk | Medium | Low (no callers) |
| live_fill_mapper stub risk | Medium | Low (no callers) |
| H9 priority | P0 soak blocker | P3 legacy cleanup |
| Canonical intent store | Unclear | IntentQueueSQLite (soak path) |
| Paper soak service | Not traced | executor not intent_consumer |
| H4/H5/H7/H8/P1-6 | Claimed without grep | All confirmed by grep |
