# Transitional Service Families

## Canonical
- services/strategies
- services/execution
- services/market_data
- services/paper_trader

## Transitional / Compatibility
- none currently tracked

## Retired
- services/strategy: retired on 2026-07-01 after the final startup-guard shim
  was replaced by the canonical `services/execution/startup_guard.py`.
- services/strategy_runner: retired on 2026-07-01 after runtime ownership moved
  to `services/execution/strategy_runner.py` and active import checks showed no
  internal callers remained.
- services/paper: retired on 2026-07-01 after test-only callers were migrated
  or removed.
- services/marketdata: retired on 2026-07-01 after import/reference checks
  confirmed no tracked source files or active callers remained.
- services/storage: retired on 2026-07-01 after import/reference checks
  confirmed no tracked source files or active callers remained.

## Current Caller Classification

No tracked transitional compatibility family remains active.

## Migration Priority
- none currently tracked

## Approved review decision: services/paper
- status: retired on 2026-07-01
- final caller state: test-only callers migrated or removed
- cleanup rule: do not reintroduce `services/paper`; use `services/paper_trader`
  or `services/execution/paper_engine.py`.

## Approved review decision: services/paper implementation shape
- services/paper/main.py: compatibility paper-mode loop over canonical safety/storage components
- services/paper/paper_state.py: compatibility wrapper over storage.paper_trading_sqlite.PaperTradingSQLite
- services/paper/paper_broker.py: compatibility wrapper over services.execution.paper_engine.PaperEngine
- decision: deleted after callers were proven test-only
- rule: no new direct imports; use canonical replacements

## Approved review decision: services/strategy implementation shape
- final tracked file: `services/strategy/startup_guard.py`
- canonical replacement: `services/execution/startup_guard.py`
- decision: deleted after callers were proven to use the canonical path
- rule: do not reintroduce `services/strategy`

## Approved review decision: services/strategy_runner implementation shape
- final tracked files:
  - `services/strategy_runner/ema_crossover_runner.py`
  - `services/strategy_runner/strategies/ema_crossover.py`
- canonical replacements:
  - `services/execution/strategy_runner.py`
  - `services/strategies/ema_cross.py`
- decision: deleted after active internal callers were migrated and import
  guards proved no tracked `services/` or `scripts/` caller remained
- rule: do not reintroduce `services/strategy_runner`

## Approved review decision: services/storage implementation shape
- final tracked files: none remained when reconciled
- canonical replacement: top-level `storage/`
- decision: mark retired after `git ls-files services/storage`, active import
  grep, and non-cache file checks confirmed no tracked source remained
- rule: do not reintroduce `services/storage`
