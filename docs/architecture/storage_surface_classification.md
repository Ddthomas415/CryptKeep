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
| `storage/fill_reconciler_store_sqlite.py` | `unwired_candidate` | No visible current source importer from static grep |
| `storage/order_idempotency_sqlite.py` | `unwired_candidate` | No visible current source importer from static grep |
| `storage/order_tracker_store_sqlite.py` | `unwired_candidate` | No visible current source importer from static grep |

## Policy

- Do not delete the `unwired_candidate` stores until an explicit caller audit
  confirms they are not needed for migration or incident recovery.
- Do not build new reconciliation logic on an unwired candidate store without
  first deciding whether it should replace, delegate to, or remain separate
  from the core stores.
- Prefer one canonical store for each live-money concept before capped live.

## Open Follow-Up

Run a targeted current-master caller audit for the three `unwired_candidate`
stores before the next reconciliation implementation.
