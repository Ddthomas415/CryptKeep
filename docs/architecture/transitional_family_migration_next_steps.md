# Transitional Family Migration — Next Steps

## Canonical
- services/strategies
- services/execution
- services/market_data
- services/paper_trader

## Transitional
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

## Deadline
- Removal deadline: 2026-08-01
- Extension decision:
  `docs/strategies/decision_record_2026-07-01_transitional_family_deadline.md`

## Execution Order
- no tracked transitional family remains

## Rule
- Do not reintroduce retired compatibility families without a new accepted
  architecture decision.
