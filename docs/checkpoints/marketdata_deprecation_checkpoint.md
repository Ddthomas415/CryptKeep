Status: RETIRED

# marketdata deprecation checkpoint

## Target
- `services.marketdata`

## Current state
- No remaining live-code imports in `dashboard`, `services`, or `scripts`
- No tracked source files remain under `services/marketdata`
- Canonical replacement is:
  - `services.market_data`

## Deprecation decision
- `services.marketdata` is retired
- No new code should import or recreate `services.marketdata`

## Removal validation
1. import grep confirms zero active references:
   - `services.marketdata`
   - `from services.marketdata`
   - `import services.marketdata`
2. `git ls-files services/marketdata` confirms no tracked files
3. focused market-data tests pass against `services.market_data`

## Removal validation commands

grep -RniE --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.cbp_state \
  'services\.marketdata|from services\.marketdata|import services\.marketdata' \
  dashboard services scripts tests 2>/dev/null

./.venv/bin/python -m pytest -q tests/test_dashboard_view_data.py

## Current decision
- Retired now
- Do not reintroduce the compatibility package
