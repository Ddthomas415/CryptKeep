# Repo hygiene and overlap status

## Completed
- Removed active `__pycache__` directories
- Removed active `.pyc` files
- Fresh audit completes with no failed checks

## Remaining non-blocking issue
- `overlap_dirs => 11 hits`

## Current overlap families
- services/paper
- services/paper_trader
- services/market_data
- services/marketdata
- services/strategies
- services/strategy_runner
- services/storage
- services/strategy

## Interpretation
- Cache warnings are regenerated during audit execution and are not currently a tracked repo-artifact problem
- Overlap families remain architecture debt to review in a separate cleanup track

## Next track
- classify canonical vs legacy/compat packages for the overlap families

## Overlap classification progress

### market_data family
- `services/market_data` = canonical package candidate
- `services/marketdata` = compatibility alias/wrapper family
- Action: retain for now, do not delete blindly

### paper family
- `services/paper` = active legacy/current paper-engine path
- `services/paper_trader` = active parallel execution-venue path
- Action: architecture debt, not safe to delete blindly

### strategy family
- `services/strategies` = active canonical strategy-definition package
- `services/strategy_runner` = active runner/runtime package
- `services/strategy` = legacy/compat/parallel overlap debt
- Action: not safe to delete blindly

### storage family
- `services/storage` = likely inactive/legacy overlap relative to top-level `storage`
- Action: later cleanup candidate, not safe to delete blindly without a removal pass
