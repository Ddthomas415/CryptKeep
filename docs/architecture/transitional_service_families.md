# Transitional Service Families

## Canonical
- services/strategies
- services/market_data
- services/paper_trader

## Transitional / Compatibility
- services/strategy_runner

## Retired
- services/strategy: retired on 2026-07-01 after the final startup-guard shim
  was replaced by the canonical `services/execution/startup_guard.py`.
- services/paper: retired on 2026-07-01 after test-only callers were migrated
  or removed.
- services/marketdata: retired on 2026-07-01 after import/reference checks
  confirmed no tracked source files or active callers remained.

## Current Caller Classification

### services/strategy_runner
- live runtime caller:
  - services/trading_runner/run_trader.py
- script caller:
  - scripts/run_strategy_runner.py

## Migration Priority
1. services/strategy_runner

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
