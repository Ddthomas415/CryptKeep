# Volume and BTC context hypothesis: negative account result

Status: READY_FOR_INDEPENDENT_REVIEW. No production or holdings changes.

## Economic answer

The fixed combined filter improved the modeled ending value but did not make
the rule profitable. USD1,000 ended at USD618.50 (-38.15%), all cash; 21 closed
trades, 11 net winners. Maximum close-based drawdown: 72.98%.
Unfiltered control reproduced USD493.06 and 80.73% drawdown exactly. Same-period
BTC holding estimate: USD1,270.19 and 7.80% drawdown. These are historical models
with assumed costs and current-listed, partially rankable market coverage.
For accounting context only, removing fees and adverse-price adjustments from
the SAME executed entry/exit sequence gives USD847.51 gross. That is not a new
zero-cost strategy rerun (execution-cost changes could change trigger dates),
but shows the recorded sequence also lost capital before those deductions.

## Separately fixed hypothesis

At the already-defined 20% closing-peak dip, buy only if BOTH conditions hold:
BTC completed 24-hour return > 0; the coin's summed base-unit trading volume in
the last six completed hours exceeds the preceding six hours. No alternative
thresholds, lengths or market filters were searched. Increased turnover does not
mean net buying or prove demand; the hypothesis is only about activity context.
Missing BTC/volume history refuses the entry. A refused watch is retired; later
leader observations can create new watches. This is not a retry-until-pass rule.

Everything else stays fixed: next-open purchase, entry-relative 5% close target,
next-open sale or 48-hour timeout, 72-hour leader-watch expiry, one USD1,000 account
with all cash carried forward. First qualifying trigger while flat; oldest leader
then product ID for simultaneous triggers. No new signals while held. Execution
assumptions remain 50-bps fees plus 25-bps adverse price each side.

The new fork also fixes the disclosed cancellation path: unrelated watches remain
until the selected entry actually executes. The unfiltered real-data regression
matches the original exactly; neither control nor filtered run had skipped entries.
Original source, plans and results remain unchanged.

## Was the filter exercised?

358 watch refusals, representing 79 distinct symbol/decision-time pairs, all
because a condition was not met; zero unknown-history refusals. Repeated watches
are not independent samples. Portfolio paths change when signals are refused,
so the USD125.45 ending-value difference is not proof of a causal, durable edge.
No parameter tuning followed the observed result. Historical data was already
explored, not untouched validation; no statistical significance is claimed.

## Verification and artifacts

Four targeted tests passed: both gate conditions; unknown history refusal;
future-bar independence; exact unfiltered real-data replay; unrelated-watch
retention after failed entry. Full suite not run for this isolated research fork.
Source and input hashes are frozen in leader_context_plan_20261012.json;
results are in research/leader_context_results_20261012.json. Runtime verified
input hashes before and after. New source: scripts/research/leader_context_hypothesis.py.
Separate reviewer Newton requested. No live orders, account, risk, campaign,
collector or scheduling changes. Gainers watch remains paused.
