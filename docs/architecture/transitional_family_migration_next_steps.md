# Transitional Family Migration — Next Steps

## Canonical
- services/strategies
- services/market_data
- services/paper_trader

## Transitional
- services/strategy
- services/strategy_runner

## Retired
- services/paper: retired on 2026-07-01 after test-only callers were migrated
  or removed.
- services/marketdata: retired on 2026-07-01 after import/reference checks
  confirmed no tracked source files or active callers remained.

## Deadline
- Removal deadline: 2026-08-01
- Extension decision:
  `docs/strategies/decision_record_2026-07-01_transitional_family_deadline.md`

## Execution Order
1. services/strategy
   - migrate live service callers to services/strategies
2. services/strategy_runner
   - treat as runtime adapter until run_trader path is migrated

## Rule
- No deletion before caller migration or explicit compatibility shim.
