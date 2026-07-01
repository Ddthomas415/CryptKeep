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
- `services/execution/strategy_runner.py` = active runner/runtime module
- `services/strategy_runner` = retired compatibility family as of 2026-07-01
- `services/strategy` = retired compatibility family as of 2026-07-01
- Plan:
  1. Keep `services/strategies` as canonical definitions layer
  2. Keep `services/execution/strategy_runner.py` as runtime/runner layer
  3. Do not reintroduce `services/strategy`
  4. Do not reintroduce `services/strategy_runner`

### storage family
- `services/storage` = retired compatibility family as of 2026-07-01
- `storage/` = canonical live storage package
- Plan:
  1. Do not reintroduce `services/storage`
  2. Use top-level `storage/` for future storage work

## Immediate next actions
1. Continue monitoring retired-family guard coverage
2. Move on to non-overlap production hardening work

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
- `services/execution/strategy_runner.py` is the active runtime/runner module.
- `services/strategy_runner` is retired
- `services/strategy` is retired
- Action: do not reintroduce `services/strategy` or `services/strategy_runner`

## Next retirement candidate
- none currently identified in this overlap track

### storage status update
- No remaining live-code imports of `services.storage` in `dashboard`,
  `services`, or `scripts`
- No tracked source files remain under `services/storage`
- `services.storage` is retired
- Action: do not reintroduce `services.storage`
