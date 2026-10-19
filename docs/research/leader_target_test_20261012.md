# Fixed target test: result first

All eight variants have negative mean gross AND modeled net closed-event returns.
All eight have negative modeled net averages in each of the two 91-day segments.
This is evidence against these tested daily-proxy rules, not all mean reversion.
Status: READY_FOR_INDEPENDENT_REVIEW, separate reviewer requested.

## Frozen rules and data

Plan leader_target_plan_20261012.json was written before executing these variants.
403 current eligible Coinbase USD products; daily candles Apr13-Oct12 cutoff.
No delisted-market archive or historical eligibility flags available in this
dataset. Leaders use completed UTC daily close changes; not a live-hourly
leaderboard. Running peaks use closes; dips trigger at10/20% below those peaks.
Entry is next open; target5/10% above spread-adjusted entry requires completed
close; exit is next open. Maximum holds7/14days. Wait up to30days after leadership
for a dip. Segments are Apr13-Jul13 and Jul13-Oct12, each end exclusive. Positions
still open at boundaries are retained separately, not forced into wins/losses.
This segmentation is diagnostic, not untouched validation or the existing campaign.

Cost model:50bps fee each side plus25bps adverse price adjustment each side.
The adverse adjustment is an assumed spread/execution sensitivity, not measured
historical spread. USD1000 includes entry fee. No account/campaign changes.

## Combined closed-event results

| Dip | Target | Max days | Closed | Net winners | Mean net USD | Worst net USD | Sum net USD | Matched BTC sum USD |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
|10%|5%|7|165|73|-46.37|-640.94|-7651.87|-2613.52|
|10%|5%|14|157|87|-45.36|-707.09|-7120.79|-1989.58|
|10%|10%|7|162|63|-48.04|-640.94|-7782.71|-2271.44|
|10%|10%|14|153|78|-44.17|-707.09|-6757.42|-1575.34|
|20%|5%|7|156|85|-18.71|-568.45|-2918.69|-3356.80|
|20%|5%|14|151|92|-24.47|-707.09|-3694.58|-2139.86|
|20%|10%|7|153|72|-27.52|-568.45|-4209.99|-3014.78|
|20%|10%|14|145|76|-31.44|-707.09|-4559.32|-1629.88|

Each sum is over USD1000 independent event exposures, which overlap and repeat
coins. It is NOT a single USD1000 account return, reinvestment or executable
portfolio. Matched BTC invests the same event budget at the same entry/exit
times with the same cost assumptions. No matched rows were missing here.
The20%/5%/7day variant outperformed matched BTC in total but still lost money.

There are175 entries per10%arm and167 per20%arm. Depending on target/timeout,
10-22 and11-22 entered events remain open or exit-pending at segment boundaries.
These are excluded from closed-only sums, so those sums are NOT all-position PnL.
Their last available liquidation marks are preserved in the full event output.
Worst individual CLOSE-based drawdown varies58.16%-71.09%; this is neither
intrabar drawdown nor portfolio max drawdown. No portfolio max drawdown proven.

Mean net USD by first/second segment:
10%/5%/7:-38.71/-53.76;10%/5%/14:-42.25/-48.27;
10%/10%/7:-46.12/-49.92;10%/10%/14:-48.40/-40.20;
20%/5%/7:-12.16/-25.09;20%/5%/14:-30.68/-18.34;
20%/10%/7:-25.32/-29.75;20%/10%/14:-42.01/-20.73.

Separate full-segment BTC USD1000 buy/hold control: modeled net -112.56 first
segment,+293.25 second, terminal-close liquidation assumed. Those single-hold
figures have a different capital/time basis from overlapping event sums and
must not be directly compared as portfolio totals.

## Proof and limitations

Source/dataset hashes checked before run; dataset checked again after run.
Three targeted tests passed: target not green, timeout/open retention,
cost-inclusive budget, and later gaps not removing completed exits.
No full suite run for this isolated research addition. Statistical inference,
multiple-comparison correction, historical spreads, delisted coverage, exact
live ranking and a non-overlapping repeated-trade portfolio remain unverified.
Different halves do not automatically imply luck; regimes can genuinely differ.
Original studies preserved. Artifacts in research/leader_target_results_20261012.json
and research/leader_target_btc_control_20261012.json. Separate review pending.

## Reporting correction after separate GATE review

Original frozen source/results remain unchanged. New append-only report
research/leader_target_results_corrected_20261012.json restores the two omitted
terminal leader events (181 per variant instead of179). Closed trades and closed
net sums remain exactly unchanged. Average/worst/winners now explicitly identify
closed events. Unresolved last-observed marks are separately summed, NOT realized
or portfolio PnL. Their inclusion makes all eight averages more negative:
10%/5%/7:-47.67;10%/5%/14:-51.57;10%/10%/7:-50.46;
10%/10%/14:-52.34;20%/5%/7:-20.32;20%/5%/14:-29.20;
20%/10%/7:-29.80;20%/10%/14:-37.20 USD per marked entry event.
Two correction tests passed, including unchanged closed results across all eight
variants. Correction source: scripts/research/correct_leader_target_report.py.
Final separate re-review requested; READY_FOR_INDEPENDENT_REVIEW.
