# Dip recovery screen - 2026-10-12

Status: READY_FOR_INDEPENDENT_REVIEW. Exploratory historical simulation only.

## Question and fixed rules

Does a negative candle, or a rolling24h crossing into negative territory,
precede a recoverable rise from a next-open purchase? This differs from merely
counting colour changes. No production strategy or campaign was changed.

Daily screen covers the 23 grid-verified markets in the existing public archive.
Hourly screen covers GTC and RSR in the existing hourly archive. There are 54
market/rule/target comparisons, not independent confirmations. Targets are fixed
at 3% and 5%, not fitted after seeing the results. Daily timeout is seven days;
hourly timeout is 48 hours. Negative daily/hourly returns permit an entry after
a down candle; rolling24h entries require a crossing from nonnegative to negative.
Entries fill at next open. A target requires a completed close above the target;
the sale fills at the following open, so an achieved target can still exit at a
loss. No perfect-low purchase, high-price sale or intrabar target fill is assumed.
Trades within each run do not overlap. Separate runs reuse the same data.

## Preliminary observations

GTC hourly 24h-red crossings, 3% target: five events, five target closes reached,
average successful holding time 16.2 hours. Modeled fully reinvested USD1000
ends at USD1286.46 gross, USD1223.72 with illustrative 50bps fees each side.
RSR same rule: five events, four targets reached, successful mean 17.25 hours;
gross end USD1009.44, fee-only USD960.21. One failure matters economically.

GTC negative-hourly-return, 3% target: 12 of 14 targets reached; mean successful
holding time 10.83 hours. Worst exit return was -26.73%. Gross compounded end
USD1805.96; illustrative fee-only USD1570.03. This is not a safe repeated cycle.

Daily 3% targets: PUMP reached 24/32, NEAR 17/28, ZEC 19/29. Their gross
compounded ending values were USD2507.83, USD1930.93, USD1798.52 respectively.
Worst single exit returns were -18.79%, -14.21%, -17.69%. These historical
selection winners need benchmark and separate-period tests, not immediate buys.

## Limits and preserved evidence

Inputs are already explored and current-universe selected. No untouched holdout,
multiple-search correction, benchmark comparison or confidence intervals yet.
These are positive samples, not established predictive edges. Five hourly events
are particularly weak evidence. Window-end entries lacking a full maximum holding
window are excluded even if they might have recovered sooner; this censoring can
bias results. Zeros and gaps do not permit fabricated data. The hourly windows
are short and include unusually active recent markets. Full reinvestment is a
scenario, not the user's actual account. No spread, slippage or fill feasibility
is included; fee-only figures are sensitivities, not actual retail exit costs.

Original archives and previous analyses remain unchanged. Full event details and
input hashes are in research/dip_recovery_screen_20261012.json. Source is
scripts/research/dip_recovery_screen.py. Three targeted tests passed. Separate
review is pending. Next proof: correctness review, benchmark and time-split
replication with the same rules; do not optimize thresholds on these results.
