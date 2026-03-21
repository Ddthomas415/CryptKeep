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
