# storage retirement readiness

## Current status
- `storage/` is the canonical live package
- `services/storage` is wrapper-only
- no live imports should remain in `dashboard`, `services`, or `scripts`
- remaining references should be wrapper/compat test coverage only

## Wrapper files
- enumerate all files under `services/storage/`

## Preconditions before removal
1. verify no live imports remain
2. remove or replace wrapper tests
3. re-run import grep to confirm zero references
4. remove `services/storage`
5. run focused tests for storage consumers

## Current decision
- ready for future retirement planning
- not removing in this checkpoint
