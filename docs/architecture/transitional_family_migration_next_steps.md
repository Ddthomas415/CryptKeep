# Transitional Family Migration — Next Steps

## Canonical
- services/strategies
- services/market_data
- services/paper_trader

## Transitional
- services/strategy_runner

## Retired
- services/strategy: retired on 2026-07-01 after the final startup-guard shim
  was replaced by the canonical `services/execution/startup_guard.py`.
- services/paper: retired on 2026-07-01 after test-only callers were migrated
  or removed.
- services/marketdata: retired on 2026-07-01 after import/reference checks
  confirmed no tracked source files or active callers remained.

## Deadline
- Removal deadline: 2026-08-01
- Extension decision:
  `docs/strategies/decision_record_2026-07-01_transitional_family_deadline.md`

## Execution Order
1. services/strategy_runner
   - treat as runtime adapter until run_trader path is migrated

## Rule
- No deletion before caller migration or explicit compatibility shim.
