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

Multi-quote cash ledger (MB8):
- Internal cash storage now includes `portfolio_cash_v2(exchange, quote_ccy, cash, updated_ts)`.
- Reconciliation compares exchange vs internal cash for all configured `reconciliation.quote_ccys`.
- Primary quote drift keeps legacy fallback for older single-row `portfolio_cash` installs.
