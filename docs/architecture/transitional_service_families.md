# Transitional Service Families

## Canonical
- services/strategies
- services/market_data
- services/paper_trader

## Transitional / Compatibility
- services/strategy
- services/strategy_runner

## Retired
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

### services/strategy
- live service caller:
  - services/analytics/paper_strategy_evidence_service.py
- internal legacy family:
  - services/strategy/filters/*
  - services/strategy/registry.py
  - services/strategy/strategies/*
- test caller:
  - tests/test_strategy_runtime_runner.py

## Migration Priority
1. services/strategy
2. services/strategy_runner

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
- services/strategy/registry.py: legacy internal registry of old strategy compute functions
- services/strategy/strategies/*: legacy compute implementations returning services.strategy.signals.Signal
- decision: keep frozen as transitional internal compatibility island
- rule: no new direct imports; migrate external callers to services/strategies where canonical equivalents exist
