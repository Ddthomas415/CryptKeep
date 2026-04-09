# Root Runtime Next Actions

Status: FROZEN_WITH_EXTERNAL_EXCEPTION

## Current state
- [x] Freeze canonical root-runtime launch scope
- [x] Prove private authenticated connectivity for one supported venue
- [ ] Prove private lifecycle runtime flow in a reachable sandbox/testnet environment

Notes:
- Coinbase private authenticated read-only proof is complete through the keyring-backed path with `sandbox=False`
- Binance testnet is blocked from the current location/network by HTTP `451`
- Gate.io is not currently usable from the operator environment
- The remaining lifecycle proof is deferred in this environment until a reachable supported sandbox/testnet venue exists, or a human launch decision accepts the exception

Recent landed fix:
- docs/checkpoints/coinbase_portfolio_quote_guard_note.md
- docs/checkpoints/hidden_defaults_note.md
- docs/checkpoints/live_lifecycle_gap_note.md
- docs/checkpoints/live_mode_source_of_truth_note.md
- docs/checkpoints/root_runtime_scope_record.md

## Already documented
- [x] Scope record created
- [x] Launch blocker list created
- [x] Live lifecycle gap note created
- [x] Live-mode source-of-truth note created
- [x] Hidden defaults note created
- [x] Trading config comment aligned with current repo truth

## Review rule
Any runtime change touching live execution, lifecycle authority, or arming behavior stops at:
- READY_FOR_INDEPENDENT_REVIEW
