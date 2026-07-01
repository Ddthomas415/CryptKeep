# Transitional Family Migration — Next Steps

## Canonical
- services/strategies
- services/market_data
- services/paper_trader

## Transitional
- services/strategy
- services/strategy_runner
- services/marketdata

## Retired
- services/paper: retired on 2026-07-01 after test-only callers were migrated
  or removed.

## Deadline
- Removal deadline: 2026-08-01
- Extension decision:
  `docs/strategies/decision_record_2026-07-01_transitional_family_deadline.md`

## Execution Order
1. services/marketdata
   - migrate script/test callers to services/market_data where equivalent exists
2. services/strategy
   - migrate live service callers to services/strategies
3. services/strategy_runner
   - treat as runtime adapter until run_trader path is migrated

## Rule
- No deletion before caller migration or explicit compatibility shim.
