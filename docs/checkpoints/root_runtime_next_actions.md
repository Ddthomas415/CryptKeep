# Root Runtime Next Actions

Status: OPEN

## External-proof blockers
- [ ] Configure one supported sandbox venue locally
- [ ] Prove private authenticated connectivity
- [ ] Prove private lifecycle runtime flow

## High-risk implementation blockers
- [ ] Resolve active live lifecycle authority gap
- [ ] Collapse live-mode source of truth
- [ ] Remove or fence hidden defaults on launch-capable paths

Recent landed fix:
- docs/checkpoints/coinbase_portfolio_quote_guard_note.md

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
