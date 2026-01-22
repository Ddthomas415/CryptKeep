# Phase 341 — Precise SYNC_POSITION (No Guessing)

Changes:
- Drift is computed per configured `symbols` + `symbol_maps[exchange]` mapping.
- Drift records now include:
  - canonical_symbol
  - exchange_symbol
  - base, quote
  - exchange_qty, internal_qty, abs_drift
- Untracked assets held on exchange are listed separately (informational).

Runbook safety:
- SYNC_POSITION requires `params.exchange_symbol`.
- Executor refuses SYNC_POSITION without exchange_symbol (no base/symbol guessing).
