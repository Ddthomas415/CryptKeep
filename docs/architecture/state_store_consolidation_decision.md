# State Store Consolidation Decision

Date: 2026-07-04

Status: Accepted direction, implementation deferred

## Scope

This decision covers fills, positions, cash, PnL, intents, order lifecycle, and
evidence/history stores for the current paper/research path and the future
capped-live path.

It does not migrate data, delete stores, or change runtime behavior.

## Evidence

- SHOWN: `storage/paper_trading_sqlite.py` owns paper orders, paper fills,
  paper positions, cash, and realized PnL in `paper_trading.sqlite`.
- SHOWN: `storage/trade_journal_sqlite.py` owns the paper/history journal in
  `trade_journal.sqlite`, which is consumed by strategy feedback and promotion
  evidence paths.
- SHOWN: `storage/execution_store_sqlite.py` owns legacy/current execution
  intents and fills in `execution.sqlite`.
- SHOWN: `storage/live_position_store_sqlite.py` tracks live spot position and
  realized PnL by venue/fill id in the execution DB.
- SHOWN: `docs/architecture/storage_surface_classification.md` classifies core
  and candidate storage modules and preserves unwired stores for a separate
  caller/migration audit.
- UNVERIFIED: a complete end-to-end crash/fault-injection proof across submit,
  fill, reconcile, and restart does not yet exist.

## Decision

Do not migrate or merge state stores during the active paper evidence campaign.
The near-term policy is to freeze store ownership, add invariants, and prevent
new state surfaces without an owner.

Current authorities:

- Paper orders/fills/positions/cash/PnL:
  `PaperTradingSQLite` / `paper_trading.sqlite` is canonical for paper
  execution accounting.
- Paper/history evidence:
  JSONL evidence plus `TradeJournalSQLite` / `trade_journal.sqlite` are
  evidence/history surfaces derived from execution events, not cash authority.
- Execution intents/fills:
  `execution.sqlite` stores such as `ExecutionStore`, intent queues, and
  live/paper consumers remain compatibility surfaces until migration is proven.
- Live spot position/PnL:
  `LivePositionStore` plus risk/fill ledgers in `execution.sqlite` remain the
  existing live accounting authority until capped-live migration proof.
- Research and market data:
  market/archive/edge stores remain read-only inputs to execution decisions
  unless separately promoted.

Long-term target:

- One transactional execution-accounting boundary per environment.
- Order lifecycle, fill application, position updates, cash/PnL updates, and
  risk-accounting writes either commit together or fail closed with an explicit
  repair/reconcile path.
- Evidence records remain derivative artifacts. They may qualify or summarize
  state, but they must not become a second accounting authority.

## Implementation Consequences

- New stores that touch money-adjacent state must be added to
  `docs/architecture/storage_surface_classification.md` with an owner and
  classification.
- New paper execution features must use `PaperTradingSQLite` unless a separate
  migration decision is accepted.
- New live/capped-live features must state which execution DB tables they read
  and write, and must include reconciliation behavior for partial failure.
- Migration work must start with tests and adapters, not broad data movement:
  first facade, then dual-read invariant checks, then paper/shadow dual-write
  proof, then capped-live cutover only after backup/restore and crash tests.

## Accepted Risk

The current multi-store architecture is acceptable for paper and research while
promotion remains gated and live execution is blocked.

It is not accepted for capped-live without one of these outcomes:

- a transactional consolidation migration is implemented and proven, or
- the remaining split-store design is explicitly accepted with fault-injection,
  reconciliation, backup/restore, and operator alerting evidence.

## Follow-Up

1. Run the targeted caller/migration audit for the unwired candidate stores in
   `docs/architecture/storage_surface_classification.md`.
2. Add crash-consistency tests for submit, fill, reconcile, and restart.
3. Add backup/restore drill evidence before capped-live exposure.
4. Revisit this decision after the paper gate clears and before any shadow to
   capped-live transition.

## Executable Guard

`tests/test_state_store_consolidation_decision_guard.py` pins the no-migration
boundary, current store authorities, long-term transactional target,
implementation consequences, capped-live accepted-risk boundary, and follow-up
requirements so storage consolidation cannot silently become a runtime migration.
