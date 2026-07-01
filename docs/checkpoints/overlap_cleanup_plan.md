# Overlap cleanup plan

## Goal
Reduce architecture debt from overlapping module families without breaking active imports or runtime paths.

## Families already classified

### market family
- `services/market_data` = canonical candidate
- `services/marketdata` = retired compatibility family as of 2026-07-01
- Plan:
  1. Do not reintroduce `services/marketdata`
  2. Use `services/market_data` for future market-data work
  3. Continue resolving remaining non-marketdata overlap families separately

### paper family
- `services/paper` = retired compatibility family as of 2026-07-01
- `services/paper_trader` = active parallel execution-venue path
- Plan:
  1. Do not reintroduce `services/paper`
  2. Use `services/paper_trader` or `services/execution/paper_engine.py`
     for future paper execution work
  3. Continue resolving remaining non-paper overlap families separately

### strategy family
- `services/strategies` = active canonical strategy-definition package
- `services/strategy_runner` = active runner/runtime package
- `services/strategy` = legacy/compat/parallel overlap debt
- Plan:
  1. Keep `services/strategies` as canonical definitions layer
  2. Keep `services/strategy_runner` as runtime/runner layer
  3. Reduce `services/strategy` to compat-only or retire module-by-module
  4. Remove legacy files only after import/reference audit per module

### storage family
- `services/storage` = likely inactive/legacy overlap relative to top-level `storage`
- Plan:
  1. Audit imports and runtime usage
  2. Confirm whether files are dead or only test-only
  3. Remove or archive only after explicit verification

## Immediate next actions
1. Inventory direct imports for `services/storage`
2. Inventory remaining references to `services/strategy`
3. Draft one ADR for paper/strategy ownership boundaries

## Stop conditions
- No deletions without import/reference proof
- No behavior changes in this planning phase

## Progress
- Migrated `dashboard/services/view_data.py` from `services.marketdata` to canonical `services.market_data`
- Retired `services.marketdata` after reference checks found no tracked source
  files or active callers.

### marketdata status update
- No remaining live-code imports of `services.marketdata` in `dashboard`, `services`, or `scripts`
- No tracked source files remain under `services/marketdata`
- `services.marketdata` is retired
- Action: do not reintroduce it

### strategy compat modules
- `services/strategy/ema_crossover_runner.py` is a pure compatibility re-export to `services.strategy_runner.ema_crossover_runner`
- `services/strategy_runner` remains an active runtime/runner package
- `services/strategy` still contains legacy real code in `registry.py`, `filters/*`, and `strategies/*`
- Action: keep compat wrapper for now; do not delete `services/strategy` wholesale

## Next retirement candidate
- `services/storage`
- Reason: top-level `storage` is the canonical live package; `services/storage` appears to be wrapper-only
- Preconditions before removal:
  1. verify no live imports remain
  2. remove/replace wrapper tests
  3. verify zero live imports again


## Deprecation priority
1. `services.storage` — next deprecation target after wrapper test replacement

### storage status update
- No remaining live-code imports of `services.storage` in `dashboard`, `services`, or `scripts`
- Remaining references are wrapper-test coverage only:
  - `tests/test_service_storage_wrappers.py`
- `services.storage` is now wrapper-only / compat-only debt
- Action: retain for now; later removal can be planned once wrapper-test coverage is intentionally removed or replaced
