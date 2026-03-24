# marketdata deprecation checkpoint

## Target
- `services.marketdata`

## Current state
- No remaining live-code imports in `dashboard`, `services`, or `scripts`
- Remaining references are compat-test coverage only
- Canonical replacement is:
  - `services.market_data`

## Deprecation decision
- `services.marketdata` is deprecated
- It remains temporarily for compatibility coverage only
- No new code should import `services.marketdata`

## Removal preconditions
1. `tests/test_compat_wrappers.py` is removed or replaced
2. import grep confirms zero references:
   - `services.marketdata`
   - `from services.marketdata`
   - `import services.marketdata`
3. focused market-data tests pass after removal
4. wrapper package directory is removed in one dedicated commit

## Removal validation commands

grep -RniE --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.cbp_state \
  'services\.marketdata|from services\.marketdata|import services\.marketdata' \
  dashboard services scripts tests 2>/dev/null

./.venv/bin/python -m pytest -q tests/test_dashboard_view_data.py

## Current decision
- Deprecated now
- Removal deferred until compat-test replacement/removal
