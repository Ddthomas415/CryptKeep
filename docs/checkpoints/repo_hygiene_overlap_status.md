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
