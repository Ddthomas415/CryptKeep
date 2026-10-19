# Single-account test: negative economic result

Status: READY_FOR_INDEPENDENT_REVIEW. Historical research only, no actual account.

Starting cash: USD1,000. At most one position, with proceeds carried forward
from August 11 00:00 UTC through October 12 17:00 UTC. Cash and positions carry
across the September 30 source boundary without a reset.
43 closed trades, 31 net winners. Final estimated liquidation NAV: USD493.06
(-50.69%). Ending cash is USD0 because a STRK position remains open; this is a
simulation, not the user's account. That position is marked at the final completed
close with assumed selling costs, not sold. Maximum close-based drawdown: 80.73%.
BTC holding with the same budget and costs ends at USD1,270.19 (+27.02%), with
maximum close-based drawdown of 7.80%.

## Allocation and causality

This is a newly frozen allocation rule, not a reinterpretation of the earlier
overlapping event study as a portfolio. While flat, observe the rolling-24-hour
leader among markets with 25 contiguous hourly bars and positive current volume.
Leader-return ties choose the lexically largest product ID. Track each leader
for up to 72 hours using a running closing-price peak. The first 20% closing
pullback schedules a next-open purchase using all cash, including a 50-bps entry
fee and 25-bps adverse price adjustment. Simultaneous triggers choose the oldest
leader observation, then the lexically smallest product ID.
Clear watches on entry and ignore new signals while invested. After an exit,
a new watch may begin at that hour's completed close. No same-open exit/reentry.
A completed close 5% above modeled entry schedules a next-open exit; otherwise
the 48-hour timeout does. The same assumed costs apply on selling.

Missing held-position or exit prices halt with INCOMPLETE and no endpoint NAV,
rather than skipping bad trades. A missing pending-entry open spends no cash.
Earlier raw bars are used strictly before September 30 17:00 UTC; recent bars
from then onward. Recent warm-up bars do not overwrite the earlier archive.
Original source, data and results remain preserved.

## What changed economically

Per-event positives cannot be summed into capital profit. Taking one signal at
a time changes available opportunities, while full-cash compounding magnifies
large losses. Worst closed percentage loss: BASECAT 32.12%. Other large losses:
ALEO 30.41%, FORTH 30.08%, PRCL 27.60%, G 27.46%. Winning 31/43 did not offset them.
The September 30 checkpoint was USD311.77 while holding KAIO; the account then
finished at USD493.06 without fresh capital. This is not independent train/test
or untouched-holdout evidence.

## Proof and limits

The plan was saved before execution with source/input hashes. Runtime checks
verified input hashes before and after. Five targeted tests passed for next-open
execution, cost-inclusive budget, held-gap halt, terminal valuation, cash carry
without deposits, and missing-entry handling. No full suite: isolated research.
Separate reviewer Hilbert was requested; outcome pending. Risk: HIGH.
This is not live production, actual holdings, operating proof or optimized rules.
Current-listed/rankable-universe and assumed-cost limits remain. The reconstructed
leaderboard is not exact live history. Drawdown uses liquidation estimates at
completed closes, not intrabar execution quotes. No parameter or sizing search.

Artifacts: research/leader_single_account_plan_20261012.json and
research/leader_single_account_results_20261012.json. Public watch remains paused.

## Closure

Separate reviewer Hilbert: ACCEPTED_WITH_RISK for this frozen replay only.
Every trade, NAV observation, boundary holding and BTC control independently
matched; five targeted tests passed. The economic result is unchanged.
A missing entry open would discard unrelated watches because watches clear when
an entry is scheduled. No skipped entries occurred in this run, so this defect
does not affect its result. General cancellation correctness is not accepted.
The study objective is complete. Do not tune, rerun or repair this losing branch
without a distinct research reason; preserve the negative result. No deployment
or live trading authorization follows from this diagnostic acceptance.
