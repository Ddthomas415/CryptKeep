# marketdata retirement readiness

## Current status
- `services.market_data` is the canonical live package
- `services.marketdata` is retired
- no live imports remain in `dashboard`, `services`, or `scripts`
- no tracked source files remain under `services/marketdata`

## Wrapper files
- none tracked

## Removal proof
1. `git ls-files services/marketdata` returns no tracked files
2. strict import grep finds no active `services.marketdata` imports
3. `services.market_data` remains the canonical replacement

## Current decision
- retired
- do not reintroduce `services.marketdata`
