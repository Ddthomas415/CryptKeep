# Root Runtime Next Actions

Status: OPEN

## External-proof blockers
- [ ] Configure one supported and reachable sandbox/testnet venue locally
- [x] Prove private authenticated connectivity for one supported venue
- [ ] Prove private lifecycle runtime flow

Notes:
- Coinbase private authenticated read-only proof is complete through the keyring-backed path with `sandbox=False`
- Binance testnet is blocked from the current location/network by HTTP `451`
- Gate.io is not currently usable from the operator environment

## High-risk implementation blockers
- [ ] Remove or fence hidden defaults on launch-capable paths

Recent landed fix:
- docs/checkpoints/coinbase_portfolio_quote_guard_note.md
- docs/checkpoints/live_lifecycle_gap_note.md
- docs/checkpoints/live_mode_source_of_truth_note.md

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
