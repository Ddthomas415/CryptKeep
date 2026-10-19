# Shared rev88 and economic evidence review

Date: 2026-10-07
Role: AUDITOR
Objective: review the six supplied artifacts and pasted handoff; advise without deployment.

## Coverage and limits

Read all nonempty cells, formulas and cached values in the four supplied workbooks:
ES exit policy matrix, series rebase check, trade qualification/fee reconciliation,
and paper evidence standing. Read the pasted handoff and archive review manifests,
guidance, patch map and patch 0076. Inspected the affected source and research scripts.
This is not an independent line-by-line review of all 72 commits or 168 changed files.
Workbook visual layout was not reviewed. No full suite or research matrix rerun.

## Findings

1. The October 5 standing workbook retains the explicitly withdrawn ES confidence
   interval (-1.053 to -0.087). Its eight records combine development, mispriced and
   legacy strategy records. Mark it superseded; do not use this interval as evidence
   against the strategy. Three June-July legacy records have reconciled net PnL
   -4.316305995, but do not represent the corrected SMA200/declared-exit policy.
   The later identity correction reports zero qualified corrected-policy laptop
   records. Neither cohort establishes sustainable profitability or its absence.
2. The newer breakout reconciliation supersedes the old fee calculation: gross
   3.6798422225, fees 1.166284, net 2.5135582225, versus recorded 3.0698.
   Break-even is about 23.6639 bps per side for these fills, not 27.305 bps.
   These paper fills are not evidence of executable live economics. The largest
   result contributes 8.6742; all other trades total -6.1607.
3. The ES SMA200 declared-exit replay reports +854.35% with 64.29% maximum
   drawdown and 31 trades. Buy-and-hold reports +674.64%, but its drawdown is not
   supplied in the matrix. No risk-matched superiority or prospective edge follows.
   The permanent-lockout scenario explicitly imposes a permanent lock in its replay;
   it is not a measured execution of the current runner. The performance policy's
   cumulative percentage-loss measure must not be called portfolio drawdown.
4. The rebase workbook describes an earlier state (73 commits and unresolved
   conflicts). Rev88 contains 72 commits and supersedes that status. Preserve it as
   history, not the current integration ledger. Prior acceptance, rebased review,
   merge and deployment are separate states.

## Patch 0076 verification

SHOWN: verified Git bundle and fetched its exact prerequisite into an isolated
checkout. Base be34a18a3f7b78941cddb4eabe373b33788526ce; supplied head
5b4ebb29c2c4e8bee33096aba64966ee6f40c25f; 72 commits. Original checkout untouched
by Git operations.

VERIFIED_ENV: isolated supplied-series checkout, repository Python 3.12 environment.
Command: python -m pytest -q -p no:cacheprovider
tests/test_symbol_loss_lock_counts_closing_fills.py tests/test_symbol_loss_fill_once.py
tests/test_reconcile_accounting_delivery.py
tests/test_repair_risk_sink_failed_clears_only_verified_causes.py
tests/test_place_order_symbol_loss_lock.py
Result: 107 passed, 98 deprecation warnings, 2.61 seconds.

Separate reviewer Hume: ACCEPTED_WITH_RISK for bounded static patch logic; no new
blocker. Reviewer did not execute tests or verify exact base. This audit independently
verified base and ran the tests above. Counting remains per negative-PnL fill, not
completed trade; exact zero is neutral, not fee-net neutrality. Replay does not clear
the blocking flag. Durable ledger presence does not independently prove matching
amounts or rollup integrity. Disk failure/concurrent flag writers remain outside proof.

CLAIMED: supplied full-suite total 4,989 passed, 33 skipped, zero failed.
UNVERIFIED here: full-suite reproduction, whole-series acceptance, CI, deployment,
host behavior and profitability. No authorization to deploy is inferred.

## Recommended next action

Correct the evidence/status ledger first, then perform one bounded paper evaluation
of the documented SMA200 crossover and declared exits with effective kill policy,
costs, cash/buy-and-hold benchmarks and policy-block counts reported. Do not select
kill settings from the best retrospective return or disable controls on this evidence.
Use a coherent independently reviewed patch subset; do not merge the whole series
on the strength of patch 0076 tests. Preserve held patch 0011.

No source, workbook, account, config, credential, collector or deployment changed.
Disposition: ACCEPTED_WITH_RISK for bounded 0076 review; whole series INCOMPLETE.
