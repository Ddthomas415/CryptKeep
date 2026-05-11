# Pass 2V — Execution Layer Batch 5

**Date:** 2026-05-10
**Pass:** 2V — sizing, position_math, ccxt_fills, order_reconciliation, intent_reconciler, outcome_logger
**Status:** COMPLETE

---

## SHOWN findings

### Finding 1 — sizing qty_step truncation correct (Strength)

```python
steps = math.floor(qty / float(qty_step))
qty = steps * float(qty_step)
```

Floors to lot size. Rounding up could violate position limits. Returns 0.0
when below min_qty (fail-safe, no partial order).

---

### Finding 2 — position_math 1e-12 guard + correct WACC (Strength)

```python
new_avg = ((avg * qty) + (px * qty_delta)) / max(new_qty, 1e-12)
```

Guards division by zero. Correct weighted average cost calculation.
Distinguishes four position events: open, add, reduce, close.

---

### Finding 3 — ccxt_fills handles both fee formats (Strength)

Handles `fee` (dict) and `fees` (list) from CCXT. Different exchanges return
different formats. Both handled correctly with fallback defaults.

---

### Finding 4 — SafeToRetryAfterReconciliation typed exception-as-signal (Strength)

Post-ambiguous-ACK reconciliation confirms order NOT placed -> raises this
exception to signal safe-to-retry to caller. Named exception as typed signal.
Orders confirmed via lifecycle_boundary (logged).

---

### Finding 5 — intent_reconciler atomic_write + file-lock single-instance (Strength)

Status file: atomic_write. Lock file: open('x') exclusive create on POSIX.
clean_stale_lock_file for crashed-process recovery. Correct pattern.

---

### Finding 6 — outcome_logger non-atomic append (Low)

Plain open('a') append. Safe in single-process context (intent_reconciler has
single-instance lock). Could interleave if called concurrently.

---

## Clean pass. No new High or Medium findings.

All six files show correct implementation. Execution utility functions
(sizing, position math, fill extraction, reconciliation) are well-implemented.

---

## services/execution/ coverage: 40 of 80 (50%)

Batch | Files | Total
2S | 9 | 21/80
2T | 7 | 28/80
2U | 6 | 34/80
2V | 6 | 40/80

Remaining ~40 files: audit_monitor, ccxt_private_factory, event_hooks,
event_log, exec_metrics, fill_confirmation, held_intents, intent_consumer,
intent_lifecycle, intent_store, live_event_executor, live_trader_loop,
paper_fees, paper_reconciliation, plan_price_resolver, state_authority,
strategy_runner, and others.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2V
**Next:** Continue services/execution/ remaining ~40 files
