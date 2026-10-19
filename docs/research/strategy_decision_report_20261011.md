# Strategy decision report - 2026-10-11

Author: Claude (cloud session). Purpose: one economic answer from work already completed. No new simulation,
strategy, campaign change, rule change or profitability claim. Every figure is copied from an existing corrected
artifact (sources at the end). All results are simulated marked balances on historical data at the observed
0.50%/side Coinbase taker fee unless stated: sample results, not forward-confirmed or realized profit.

## 1. The answer in four lines
1. Nothing tested has a trustworthy, repeatable edge over simply holding BTC.
2. One candidate earns further testing: the BTC+ETH 28-day trend rule (vol-sized, weekly). It made money in all
   three historical windows, roughly matched BTC's return in 2024-26 with a much smaller worst drop, and its forward
   paper test already runs at no added cost.
3. At $1,000 of capital the ~$240/year infrastructure cost cancels its 2024-26 return; it only makes economic sense
   at several thousand dollars or more, and even then mainly as a lower-drawdown way to hold BTC/ETH.
4. Everything else is rejected or inconclusive (table 3). Stop adding machinery; let the running forward tests age.

## 2. Candidate results after costs, against cash ($1,000 kept = $1,000) and buy-and-hold

| Candidate | Window | End value from $1,000 | Hold BTC same window | Worst drop: rule / BTC | vs cash | vs BTC |
|---|---|---:|---:|---|---|---|
| BTC+ETH 28d trend (primary) | 2016-07 to 2019-12 | $5,308.83 | $10,509.68 | 51.9% / 83.8% | gain | behind |
| BTC+ETH 28d trend (primary) | 2020-01 to 2023-12 | $9,919.59 | $5,862.10 | 32.8% / 76.7% | gain | ahead |
| BTC+ETH 28d trend (primary) | 2024-01 to 2026-10-08 | $1,779.58 | $1,837.28 | 32.0% / 53.1% | gain | ~3% behind |
| Top-10 coin trend | 2020-23 / 2024-26 | $3,216.04 / $1,204.80 | $5,839.96 / $1,840.38 | 36.6% / 30.0% (rule) | gain | behind |
| Coinbase breakout, 15% trail | recent ~53 days / prior 10 months | $1,566.14 / $126.88 | $1,292.32 / $581.76 | 24.0% vs 7.8% (recent) | gain / large loss | ahead / behind |
| Coinbase 7-day top-3 daily rotation | recent / prior 10 months | $1,145.96 / $1.78 | $1,292.32 / $581.76 | - | gain / wiped out | behind |
| Short-hold top gainers (14 variants) | both windows | $0 to $737 recent, $0 to $2 prior | - | - | all lose | behind |
| Daily altcoin event rules (4 complete) | 2024-26 test | $129.51 to $601.00 | $1,840.38 | 55.8% to 92.8% | lose | behind |
| Binance hybrid momentum (7 complete) | test segment | best +8.0% segment return | +93.3% | - | small gain at best | far behind |
| SMA-200 BTC trend (ES, one asset) | in-sample archive | +854.4% | +674.6% | 64.3% / 76.7% | gain | ahead (one in-sample path) |

Annual view of the lead candidate, 2024-01 to 2026-10-08: rule 23.1%/yr at 0.50% fees (12.4%/yr at the 1.20%
stress fee), BTC 24.6%/yr. Return per unit of worst drop: rule 0.72, BTC 0.46. The rule was invested ~48% of the time.

## 3. How much to trust each conclusion

| Candidate | Verdict | Why |
|---|---|---|
| BTC+ETH 28d trend | INCONCLUSIVE - keep testing | Positive in every window and lower drawdown every window, but beat BTC in only one of three; its own registered stress test REJECTED it because only 5 of 13 nearby settings beat a fixed BTC/ETH/cash mix at the same exposure, so the exact settings may be lucky. Rule chosen after a search (selection bias). |
| Coinbase breakout 15% | NOT TRUSTWORTHY | +56.6% recent vs -87.3% earlier under the same rule; one trade (USELESS, +150%) carries the recent result; picked in hindsight as the winner. |
| Top-10 trend | REJECT as a separate candidate | Positive vs cash but dominated by the BTC+ETH rule in both comparable windows. |
| Short-hold, rotations, altcoin events | REJECT | Lose money after 0.50% costs in nearly every window. |
| Hybrid momentum | REJECT / partly INCOMPLETE | Trails BTC; 4 of 12 paths stop at the LUNA identity break. |
| SMA-200 BTC trend (ES) | INCONCLUSIVE | One in-sample path; its prospective paper trial (ends 2026-10-13 00:00 UTC) has made no trades since July. |
| CMC trending list | BLOCKED by missing data | No mature outcomes; first cohort Nov 10, earliest one-time analysis Feb 15, 2027; no certified statistical method. |
| Coinbase USD confirmation (3 default strategies x 5 coins) | BLOCKED by time | Evaluation runs 2026-10-10 to 2027-04-08; checkpoint 2027-01-08. |

## 4. Infrastructure: does the lead candidate pay for itself?
$20/month = $240/year (shared flat cost; replace with the real bill if different). Using the 2024-26 rate of 23.1%/yr:

| Capital | Expected yearly gain at 23.1% | Infrastructure | Left over | Holding BTC instead (24.6%, no bot cost) |
|---:|---:|---:|---:|---:|
| $1,000 | $231 | $240 | -$9 | $246 |
| $5,000 | $1,155 | $240 | $915 | $1,230 |
| $10,000 | $2,310 | $240 | $2,070 | $2,460 |
These are what-if arithmetic on a past rate, not forecasts. On return alone the bot never beats holding BTC in this
window; its only case is the smaller drawdown (32% vs 53%), which a simple fixed BTC/ETH-plus-cash split may also deliver.

## 5. Decision and the one next step
- Further testing: BTC+ETH 28-day trend only, through the weekly paper test that already exists (first scheduled run
  Monday 2026-10-12 00:47 UTC). No new code, campaign or rule change.
- Compare it at each review against two controls: holding BTC, and a fixed mix holding BTC/ETH at the rule's own
  average exposure (~48%) with the rest in cash. Suggested decision point for Damian: after 6 months, keep it only if
  it beats the fixed mix after costs with a smaller worst drop than BTC; otherwise the honest answer is a fixed
  allocation with no bot.
- Do not deploy real money on any candidate now. Do not promote the recent breakout winner.

## Sources (all previously reviewed or accepted with risk)
research/research_corrections_20261009/majors_next_open_v2.json (sha256 71e10660...), stress_corrected_v1.json
(18033c9b...), dynamic_corrected_v1.json / v2 (84e54be0... / 550972e9...), altcoins_frozen_reviewed_v2_merged.json,
hybrid_corrected_v1.json, short_hold_corrected_v1.json; docs/research/consolidated_economic_summary_20261010.md and
profit_scorecard_corrected_20261010.md (ACCEPTED_WITH_RISK); docs/research/es_buy_and_hold_risk_20261008.md;
docs/research/cmc_trending_log/primary_analysis_schedule_20261010.md; coinbase_confirmation_usd_v1/plan.json.
