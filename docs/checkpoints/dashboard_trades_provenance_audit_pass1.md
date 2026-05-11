# Trades Page Provenance Audit — Pass 1

**Date:** 2026-05-10  
**Section:** 6. Dashboard and Operator UI  
**Scope:** Trades page source and mode provenance  
**Status:** COMPLETE

## Status update — 2026-05-11

- A remediation branch now exists for the provenance gaps described here:
  - `codex/trades-provenance-truth` @ `fba06b3c3`
- That branch is `READY_FOR_REVIEW`, not independently accepted yet.
- It has **not** been landed into the active soak checkout.
- Current blocker status is tracked in:
  - [audit_findings_status_2026_05_11.md](./audit_findings_status_2026_05_11.md)

---

## Scope

- `dashboard/pages/40_Trades.py`
- `dashboard/services/views/execution_view.py` — `get_trades_view()`
- `dashboard/services/views/_shared_execution.py` — all local loaders
- `dashboard/components/tables.py` — `render_table_section()`

## Evidence reviewed

- Full read of `dashboard/pages/40_Trades.py`
- Full read of `dashboard/services/views/_shared_execution.py`
- `get_trades_view()` at `dashboard/services/views/execution_view.py:101`
- `render_table_section()` at `dashboard/components/tables.py:10`

## Checklist status

- [x] Verified which columns local loaders include in each row dict.
- [x] Verified which fallback paths exist and what provenance they carry.
- [x] Verified how `render_table_section` renders rows.
- [x] Verified open orders and failed orders source labeling.
- [x] Verified pending approvals and recent fills fallback behavior.
- [ ] Manual browser smoke not performed in this pass.

---

## SHOWN findings

### Finding 1 — Synthetic fallback rows carry no provenance fields (High)

**Evidence:**

`get_trades_view()` (`execution_view.py:101`) has a two-level fallback for
`pending_approvals`:

```python
# level 1: local queue (has mode, source, venue)
pending_approvals = vd._load_local_pending_approvals(limit=20)

# level 2: API recommendations (no mode, no source)
if not pending_approvals:
    pending_approvals = [
        {"id": ..., "asset": ..., "side": ..., "risk_size_pct": ..., "status": ...}
        for item in recommendations ...
    ]

# level 3: hardcoded synthetic default (no mode, no source, no venue)
if not pending_approvals:
    pending_approvals = [
        {"id": "rec_1", "asset": "SOL", "side": "buy",
         "risk_size_pct": 1.5, "status": "pending_review"}
    ]
```

`render_table_section()` renders via `st.dataframe(rows)` showing only the
columns present in each row dict. Level-3 fallback rows show only `id`, `asset`,
`side`, `risk_size_pct`, `status`. The `mode`, `source`, and `venue` columns are
absent. An operator cannot tell this is synthetic data.

The same applies to `recent_fills`. When `_load_local_recent_fills()` returns
empty, `get_trades_view()` falls back to `_default_recent_fills()` which returns
hardcoded BTC and ETH fills with no `venue`, `source`, or `mode` fields.

**Impact:** Operators cannot distinguish synthetic placeholder data from real
execution data for pending approvals or recent fills when local stores are empty.

---

### Finding 2 — Recent fills carry `venue` but not `source` (Medium)

**Evidence:**

`_load_local_recent_fills()` normalizes each row to:
`ts`, `asset`, `side`, `qty`, `price`, `venue`. No `source` field.

The function reads from three stores in priority order:
`PnLStoreSQLite` → `LiveTradingSQLite` → `execution_audit_reader`.
Whichever store returns data, the row does not record which store it came from.

**Contrast:** `_load_local_open_orders()` and `_load_local_failed_orders()` both
include an explicit `source` field: `live_orders`, `paper_orders`, or
`execution_audit`. Recent fills do not follow this pattern.

**Impact:** In a mixed paper/live environment, operators cannot tell whether a
fill row came from the paper trading store, the live trading store, or the audit
reader.

---

### Finding 3 — Pending approvals from local queue have strong provenance (Strength)

When `_load_local_pending_approvals()` returns data, each row includes explicit
`mode` (paper/live) and `source` fields. `IntentQueueSQLite` rows: `mode="paper"`,
`LiveIntentQueueSQLite` rows: `mode="live"`.

---

### Finding 4 — Open orders and failed orders have explicit mode and source (Strength)

`_load_local_open_orders()`: `live_orders`, `paper_orders`, `execution_audit`.
`_load_local_failed_orders()`: same plus `live_intents`, `paper_intents`.
These are the strongest provenance surfaces on the Trades page.

---

## UNVERIFIED points

- Whether operators are currently seeing synthetic fallback data in practice.
- Whether the synthetic SOL default is reached during active soak or only on
  fresh/empty runtime.
- Whether the missing `source` field on recent fills is noticed as an absence.

---

## Summary

| Surface | mode | source | Fallback provenance |
|---|---|---|---|
| Pending approvals (local) | yes | yes | — |
| Pending approvals (API fallback) | no | no | Weak |
| Pending approvals (hardcoded default) | no | no | None |
| Open orders | yes | yes | No fallback |
| Failed orders | yes | yes | No fallback |
| Recent fills (local) | no | no | venue only |
| Recent fills (hardcoded default) | no | no | None |

---

## Highest-leverage next evidence action

1. Add `"source": "synthetic_default"` to fallback rows so operators can identify
   placeholder data (one-line change per fallback path).
2. Add `source` field to `_load_local_recent_fills()` rows matching the pattern
   already used by open orders and failed orders.

Both are doc-or-fix candidates. Per current audit scope: record as findings,
do not remediate unless the operator changes direction.

---

## Handoff

**Active role:** AUDITOR  
**Acceptance state:** COMPLETE for Trades page  
**Next target:** Automation and Settings runtime-truth framing
