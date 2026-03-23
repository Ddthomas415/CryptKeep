# marketdata retirement readiness

## Current status
- `services.market_data` is the canonical live package
- `services.marketdata` is compat-only
- no live imports remain in `dashboard`, `services`, or `scripts`
- remaining references are compat-test coverage only

## Wrapper files
- enumerate all files under `services/marketdata/`

## Preconditions before removal
1. decide compat support end date
2. remove or replace compat-wrapper tests
3. re-run import grep to confirm zero references
4. remove `services/marketdata`
5. run focused tests for market-data consumers

## Current decision
- ready for future retirement planning
- not removing in this checkpoint
