# Pass 3C — Storage Layer Batch 2

**Date:** 2026-05-10
**Pass:** 3C
**Status:** COMPLETE

---

## SHOWN findings

### Finding 1 — intent_queue_sqlite uses intent_lifecycle state machine (Strength)

Imports live_queue_transition_allowed from intent_lifecycle.
State machine enforced at storage layer, not just service layer.

---

### Finding 2 — signal_inbox_sqlite idempotent by signal_id (Strength)

signal_id TEXT PRIMARY KEY. DB-level dedup for webhook signals.
WAL mode. Three indexes on (ts), (symbol, ts), (status).

---

### Finding 3 — daily_limits_sqlite explicit ownership docs (Strength)

OWNERSHIP comment: 'This is NOT the same store used by LiveGateDB.
Use DailyLimitsSQLite for: standalone paper-mode daily tracking.
Use LiveGateDB for: live-mode gate enforcement.'

Exemplary documentation that prevents the store confusion found in the
intent tracking layer (3 stores, no canonical).

---

### Finding 4 — fill_reconciler correct cursor + seen_trades dedup (Strength)

PRIMARY KEY (venue, symbol) for cursors -- one cursor per venue+symbol.
PRIMARY KEY (venue, symbol, trade_id) for seen_trades -- dedup by trade ID.
Cursor-based reconciliation correctly prevents double-processing.

---

### Finding 5 — Two separate idempotency stores (Noted)

idempotency_sqlite.py -> generic k TEXT PRIMARY KEY dedup.
order_idempotency_sqlite.py -> per-intent intent_id TEXT PRIMARY KEY.
Two stores for two different purposes. Fragmentation pattern.

---

### Finding 6 — execution_guard env-var DB path (Noted)

EXEC_GUARD_DB_PATH env var overrides path. Misconfiguration could write
to wrong location, causing consumer to read an empty/stale file.

---

### Finding 7 — risk_blocks UUID PK for audit trail (Strength)

All risk blocks for an intent are preserved. No dedup expected.
Correct for audit trail purposes. WAL mode.

---

## Clean batch. No new High or Medium findings.

---

## storage/ coverage: 20 of 46 (43%)

Remaining ~26 files:
crypto_edge_store_sqlite, decision_audit_store_sqlite, event_store_sqlite,
evidence_signals_sqlite, exec_metrics_sqlite, execution_audit_load/reader,
execution_report_sqlite, journal_store_sqlite, latency_metrics_sqlite,
market_data_store_sqlite, market_store_sqlite, meta_decisions_sqlite,
ops_event/signal_store_sqlite, order_manager/tracker_store_sqlite,
portfolio_store_sqlite, reconciliation_store_sqlite, repair_runbook_store_sqlite,
signal_reliability_sqlite, signals_store_sqlite, strategy_state_sqlite,
trade_history_sqlite.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 3C
**Next:** Continue storage/ remaining 26 files or compile findings list
