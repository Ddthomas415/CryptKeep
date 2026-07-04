# Storage Surface Classification

Date: 2026-07-03

## Scope

This classifies the storage surfaces previously flagged as possible orphans.
It is a documentation pass only; no store is deleted or rewired here.

## Classification

| Store | Classification | Evidence |
|---|---|---|
| `storage/order_dedupe_store_sqlite.py` | `core_live_boundary` | Imported by live executor, reconciler, exchange client, and tests |
| `storage/execution_guard_store_sqlite.py` | `core_execution_guard` | Imported by safety, live router/traders, and paper engine |
| `storage/reconciliation_store_sqlite.py` | `compatibility_or_reconcile` | Imported by exchange reconciler and compatibility tests |
| `storage/idempotency_sqlite.py` | `legacy_or_low_level` | Imported by order router; also defines compatibility `OrderDedupeStore` |
| `storage/fill_reconciler_store_sqlite.py` | `quarantined_retained_schema` | 2026-07-04 audit: only self/docs/audit hits |
| `storage/order_idempotency_sqlite.py` | `quarantined_retained_schema` | 2026-07-04 audit: only self/docs/audit hits |
| `storage/order_tracker_store_sqlite.py` | `quarantined_retained_schema` | 2026-07-04 audit: only self/docs/audit hits |

## Policy

- Do not build new reconciliation logic on a quarantined retained schema without
  first deciding whether it should replace, delegate to, or remain separate
  from the core stores.
- Prefer one canonical store for each live-money concept before capped live.

## 2026-07-04 Caller Audit

Command:

```bash
pattern='fill_reconciler_store_sqlite|order_idempotency_sqlite|order_tracker_store_sqlite'
pattern="$pattern|FillReconciler|OrderIdempotency|OrderTracker"
rg -n "$pattern" services scripts storage tests docs REMAINING_TASKS.md -g '*.*'
```

Result:

- SHOWN: the three `unwired_candidate` stores have no visible current
  production source importers.
- SHOWN: matches are limited to the modules themselves and prior docs/audit
  artifacts.
- UNVERIFIED: whether any archived/migration data still needs these schemas.

## Open Follow-Up

Closed 2026-07-04.

Decision:

- explicitly retain the three schemas as quarantined retained schemas during
  the current paper/research phase;
- do not wire new callers to them;
- do not delete them until the state-store consolidation migration packet
  decides whether any schema/data is needed for comparison, migration, or
  incident recovery.

Implementation consequence:

- new reconciliation, idempotency, and order-tracking work must use the current
  core stores or include a separate reviewed migration decision;
- these retained schemas are not production authorities and must not be treated
  as evidence that the corresponding runtime path is active.
