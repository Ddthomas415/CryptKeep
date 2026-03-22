# Transitional Family Migration — Next Steps

## Canonical
- services/strategies
- services/market_data
- services/paper_trader

## Transitional
- services/strategy
- services/strategy_runner
- services/marketdata
- services/paper

## Execution Order
1. services/paper
   - keep as test-compat until tests are migrated or shimmed
2. services/marketdata
   - migrate script/test callers to services/market_data where equivalent exists
3. services/strategy
   - migrate live service callers to services/strategies
4. services/strategy_runner
   - treat as runtime adapter until run_trader path is migrated

## Rule
- No deletion before caller migration or explicit compatibility shim.
