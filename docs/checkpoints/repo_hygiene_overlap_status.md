# Repo hygiene and overlap status

## Completed
- Removed active `__pycache__` directories
- Removed active `.pyc` files
- Fresh audit completes with no failed checks

## Remaining non-blocking issue
- `overlap_dirs => 11 hits`

## Current overlap families
- services/paper_trader
- services/market_data
- services/strategies
- services/strategy_runner
- services/storage

## Interpretation
- Cache warnings are regenerated during audit execution and are not currently a tracked repo-artifact problem
- Overlap families remain architecture debt to review in a separate cleanup track

## Next track
- classify canonical vs legacy/compat packages for the overlap families

## Overlap classification progress

### market_data family
- `services/market_data` = canonical package candidate
- `services/marketdata` = retired compatibility family as of 2026-07-01
- Action: do not reintroduce `services/marketdata`; use `services/market_data`

### paper family
- `services/paper` = retired compatibility family as of 2026-07-01
- `services/paper_trader` = active paper execution package
- Action: do not reintroduce `services/paper`; use canonical paper paths

### strategy family
- `services/strategies` = active canonical strategy-definition package
- `services/execution/strategy_runner.py` = active runner/runtime module
- `services/strategy_runner` = frozen compatibility wrapper package
- `services/strategy` = retired compatibility family as of 2026-07-01
- Action: do not reintroduce `services/strategy`

### storage family
- `services/storage` = likely inactive/legacy overlap relative to top-level `storage`
- Action: later cleanup candidate, not safe to delete blindly without a removal pass

### storage family
- `storage/` = canonical live storage package
- `services/storage` = compatibility wrapper layer over top-level `storage`
- Action: retain for now, later deprecate/remove after wrapper consumers are eliminated
