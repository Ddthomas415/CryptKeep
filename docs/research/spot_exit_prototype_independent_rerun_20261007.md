# Spot-exit account prototype: independent rerun and two findings - 2026-10-07

Reviewer: Claude (AUDITOR), independent of the session that wrote the package. Done in a
cloud clone, in isolated worktrees that were removed afterwards. Nothing in the package, the
laptop checkout, any state, config or campaign was changed. Nothing pushed.

Package: `docs/review_artifacts/spot_exit_account_prototype_20261007/`. Its handoff says the
reviewer did not rerun tests and that the full suite was not run. This note fills those two
gaps and reports two defects found by probing.

## Rerun

| Check | Result |
|---|---|
| `prototype_sources.tar.gz` SHA256 | `b192c3f6...402f`, as the handoff states |
| 13 files against `SHA256SUMS`; 2 files against `LIFECYCLE_SHA256SUMS` | All OK |
| Base `381bd477` vs master `be34a18a` | Identical trees |
| The handoff's eight test files on base `381bd477` | 81 passed (as claimed) |
| `tests/test_coinbase_receipt_lifecycle.py` (lifecycle delta) | 8 passed |
| Full suite, base + 15 package files | 3966 passed, 33 skipped, 0 failed (base alone: 3877) |
| Full suite, review series `claude/series-rev34` + 15 package files | 5078 passed, 33 skipped, 0 failed (series alone: 4989) |
| Production callers of the new modules | None: no existing module imports them |

Environment: Linux, Python 3.12.3. The package does not conflict with the review series.

## Finding 1: two exits that exactly equal the holding cannot both be reserved

`SpotExitReservations.reserve` compares a float sum against the holding:
`qty + reserved + outstanding > held`. With a holding of 0.3 and pending exits of 0.1 and
0.2, the first reserves and the second is refused with "insufficient unreserved holdings",
because 0.1 + 0.2 is 0.30000000000000004 in binary floating point.

## Finding 2: a terminal order filled in several parts may never settle

`SpotExitReservations.settle` requires `total == filled`, where `total` is a float sum of
the fills. A receipt of 0.3 delivered as three fills of 0.1 raises "terminal fill coverage
mismatch". The same total as one fill settles. A reservation that cannot settle is never
released, so its quantity stays reserved and later exits on that symbol are refused.

Both are SHOWN by `spot_exit_prototype_independent_rerun_20261007/probe_float_quantities.py`
(2 failed, 1 control passed), using the package's own fixtures.

Both fail closed: neither can oversell. The cost is the opposite one, a legitimate reducing
exit refused or capacity stuck, on the path this prototype exists to keep open. The same
exact-equality pattern is in `record_reconciliation` (`position != qty`) and in `reserve`
(`held != proof`); those compare one stored value with another and I did not find a failing
case for them.

Nothing is wired to these modules, so there is no exposure today.

## Not a fix

I have not changed the package or written a patch: it is the other session's work in
progress. The treatment (integer base units, Decimal, or a venue-step tolerance) is a
design choice for its author and the operator, and it needs the venue's quantity step.

## Not covered

- No review of the Coinbase transport modules beyond running their tests.
- No concurrency, restart or power-loss proof. No venue call, no credentials.
- The laptop Keychain observation in the handoff was not repeated.
