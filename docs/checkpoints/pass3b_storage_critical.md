# Pass 3B — Storage Layer Critical Files

**Date:** 2026-05-10
**Pass:** 3B
**Status:** COMPLETE for critical live-path stores

---

## Corrected coverage numbers (exact count)

| Directory | Total | Reviewed | NOT_AUDITED |
|---|---|---|---|
| storage/ | 46 | 7 | **39** (was stated 41) |
| services/market_data/ | 29 | 8 | **21** (was stated 22) |
| Zero-coverage service dirs | ~30 dirs | 0 | ~110 files |

---

## SHOWN findings

### Finding 1 — live_position_store safety rules, all fail-closed (Strength)

Docstring explicitly states:
- Duplicate fills ignored (idempotent by venue, fill_id)
- Sell without known position fails closed -> LivePositionAccountingError
- Oversell fails closed -> LivePositionAccountingError
- Unknown side fails closed

PRIMARY KEY (venue, fill_id). WAL mode, timeout=30.
Most safety-conscious storage module in the codebase.

---

### Finding 2 — execution_store enforces intent_lifecycle state machine (Strength)

Imports and calls execution_store_transition_allowed() before every status
update. INSERT OR IGNORE for fill dedup. Most rigorously gated of the three
intent tracking stores.

---

### Finding 3 — pnl_store NULL fill_id not deduplicated (Medium)

```sql
CREATE UNIQUE INDEX ON fills(venue, fill_id) WHERE fill_id IS NOT NULL;
```

Partial unique index. fill_id=NULL allows duplicate rows.
Fills from exchanges that don't provide fill IDs can be duplicated.
P&L totals could be inflated.

---

### Finding 4 — position_state autocommit, no atomic multi-step (Noted)

isolation_level=None -> autocommit. Multi-step position updates cannot be
atomic. Crash between two writes leaves partial state.

---

### Finding 5 — risk_ledger correct composite primary keys (Strength)

PRIMARY KEY (venue, symbol) for positions.
PRIMARY KEY (day, venue) for daily risk.
WAL mode.

---

## Summary

| Finding | Severity |
|---|---|
| live_position_store fail-closed safety | **Strength** |
| execution_store state machine enforcement | **Strength** |
| pnl_store NULL fill_id not deduplicated | Medium |
| position_state autocommit mode | Noted |
| risk_ledger composite PKs correct | **Strength** |

---

## storage/ coverage: 12 of 46 (26%)

34 files still NOT_AUDITED.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 3B
**Next:** Continue storage/ or compile complete findings list
