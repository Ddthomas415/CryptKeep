# Overlap cleanup plan

## Goal
Reduce architecture debt from overlapping module families without breaking active imports or runtime paths.

## Families already classified

### market family
- `services/market_data` = canonical candidate
- `services/marketdata` = compatibility alias/wrapper family
- Plan:
  1. Keep `services/marketdata` as compat for now
  2. Add deprecation note in package/module headers later
  3. Migrate any remaining references to `services/market_data`
  4. Remove compat layer only after reference count reaches zero

### paper family
- `services/paper` = active legacy/current paper-engine path
- `services/paper_trader` = active parallel execution-venue path
- Plan:
  1. Inventory which runtime paths use each family
  2. Define target ownership boundary
  3. Avoid deletion until migration plan exists
  4. Convert overlap into explicit architecture decision record later

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
2. Inventory remaining references to `services/marketdata`
3. Inventory remaining references to `services/strategy`
4. Draft one ADR for paper/strategy ownership boundaries

## Stop conditions
- No deletions without import/reference proof
- No behavior changes in this planning phase
