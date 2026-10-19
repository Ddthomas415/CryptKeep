# Corrected historical dynamic-strategy scorecard

Role: ENGINEER. Status: READY_FOR_INDEPENDENT_REVIEW.
Scope: all eight frozen dynamic strategies, two historical windows, primary50bps per-side fees. Original reports preserved. These are marked simulated balances from $1000, not realized/live profit or independent holdout evidence. No rerun or parameter selection performed.

| Frozen strategy | Recent-window balance | Earlier-window balance |
|---|---:|---:|
| Breakout, 15% trailing stop | $1566.14 | $126.88 |
| Breakout, 8% trailing stop | $1025.18 | $270.44 |
| Hold BTC | $1292.32 | $581.76 |
| Hold ETH | $1311.63 | $475.94 |
| 24-hour gain, top3, daily rotation | $578.85 | $1.86 |
| 7-day gain, top1, daily rotation | $304.13 | $0.00 rounded |
| 7-day gain, top3, daily rotation | $1145.96 | $1.78 |
| 7-day gain, top3, weekly rotation | $558.43 | $15.27 |

## Profit and risk, without hiding positive results

Recent breakout15 marked gain is $566.14 (56.614%), versus BTC $292.32 (29.232%): $273.82 more, or27.382 percentage points. ETH also outperformed BTC by $19.31 in that window. Therefore the older interim claim that no tested rule beat BTC is false across the reported windows.

Recent breakout15 observed drawdown was24.02%, versus BTC7.8%. It had23 closed trades and one position still open; its largest reported trade was USELESS at150.2%. The earlier window lost87.312% under the same breakout rule. Do not call the recent gain robust, low-risk, terminal-liquidated or repeatable, and do not average the two balances as one continuous account.

Recent top3 daily7-day rotation and breakout8 were positive versus cash before infrastructure, but trailed BTC. Every earlier-window strategy lost versus cash; BTC itself lost41.824%. These distinctions matter: losing to BTC and losing money are different claims.

## Infrastructure sensitivity

Shared infrastructure estimate is $20/month, not a separately measured incremental bill for each strategy. Do not charge every hypothetical arm the full bill and sum them as a portfolio. Dollar balances above already include modeled trading costs, but exclude infrastructure and terminal liquidation of remaining positions.

Illustrative30-day-month allocation over1272 reported recent strategy hours is $35.33. Under that convention breakout15 profit after assigned infrastructure is $530.81, top3 daily7-day rotation $110.63, and breakout8 -$10.15. This is a cost-allocation scenario, not exact calendar billing; breakout rows have1271 hours and source data windows include warm-up. Allocating the full nominal60-day data window instead costs $40 and gives breakout15 $526.14. Do not mix those conventions or annualize either gain as a forecast.

## Coverage and evidence limits

Recent paths report1271/1272 hours with zero unknown NAV hours. Earlier paths report7151/7152 hours under the explicitly labeled outage policy, with5-21 unknown valuation hours. Earlier drawdown is therefore observed-path drawdown, not complete hourly drawdown. All rows retain open positions. No liquidated net-profit comparison is asserted.

Recent rows and invariant-exempt hold controls use dynamic_corrected_v1.json; corrected earlier non-hold rows use dynamic_corrected_v2.json. The historical coverage map separately accounts for these paths; this scorecard is not a new simulation or blanket validation of every original result.

Source SHA256:
- dynamic_corrected_v1.json: `84e54be010d946199ca81b7de0b7756df5e59e19f1b5e26017eb6c7ca1b0e0d3`
- dynamic_corrected_v2.json: `550972e9ec3f5e32a0f3de40ed394735878225f31f29e826dfd2bcf119c4f6df`

## Recommendation

Keep the positive recent breakout result in the evidence ledger as hypothesis-generating, alongside its earlier failure and higher drawdown. Do not promote it from retrospective winner selection. Continue the registered forward studies without changing their rules. CMC primary scoring remains blocked by negative statistical confirmation; forward collection is not blocked. Other research families remain in the original interim report with the separate independent-review corrections; this document closes only the omitted dynamic-window comparison.
