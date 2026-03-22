# Transitional Service Families

## Canonical
- services/strategies
- services/market_data
- services/paper_trader

## Transitional / Compatibility
- services/strategy
- services/strategy_runner
- services/marketdata
- services/paper

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

### services/marketdata
- internal self-reference:
  - services/marketdata/ws_ticker_feed.py
- script caller:
  - scripts/run_ws_ticker_feed.py
- test callers:
  - tests/test_placeholder_recovery_phase5.py
  - tests/test_ws_ticker_feed.py
  - tests/test_marketdata_ohlcv_fetcher.py

### services/paper
- test-only callers:
  - tests/test_paper_main_mode_gate.py
  - tests/test_placeholder_recovery_phase3.py

## Migration Priority
1. services/paper
2. services/marketdata
3. services/strategy
4. services/strategy_runner

## Approved review decision: services/paper
- status: transitional / compatibility
- current callers: test-only unless a non-test caller is found during review
- cleanup rule: do not delete yet; migrate tests or keep thin shim first

## Approved review decision: services/paper implementation shape
- services/paper/main.py: compatibility paper-mode loop over canonical safety/storage components
- services/paper/paper_state.py: compatibility wrapper over storage.paper_trading_sqlite.PaperTradingSQLite
- services/paper/paper_broker.py: compatibility wrapper over services.execution.paper_engine.PaperEngine
- decision: keep frozen as transitional compatibility layer
- rule: no new direct imports; migrate callers only if needed

## Approved review decision: services/paper implementation shape
- services/paper/main.py: compatibility paper-mode loop over canonical safety/storage components
- services/paper/paper_state.py: compatibility wrapper over storage.paper_trading_sqlite.PaperTradingSQLite
- services/paper/paper_broker.py: compatibility wrapper over services.execution.paper_engine.PaperEngine
- decision: keep frozen as transitional compatibility layer
- rule: no new direct imports; migrate callers only if needed

## Approved review decision: services/strategy implementation shape
- services/strategy/registry.py: legacy internal registry of old strategy compute functions
- services/strategy/strategies/*: legacy compute implementations returning services.strategy.signals.Signal
- decision: keep frozen as transitional internal compatibility island
- rule: no new direct imports; migrate external callers to services/strategies where canonical equivalents exist
