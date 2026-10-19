# Recent Coinbase opportunity: bounded retrospective

Universe: the existing five USD coins, not all Coinbase products or the global
top-gainer universe. Public hourly data fetched into a separate retrospective
archive; five markets each have 492 contiguous bars from September 18 12:00 to
October 9 00:00 UTC exclusive. Each evaluated window uses 300 prior warmup bars.

Month-to-date means October 1-9; week-to-date means Monday October 5-9,
UTC boundaries and October 9 end-exclusive. Returns use first open to last close.

| Coin | Month price change | Week price change |
| --- | ---: | ---: |
| BTC | -2.2301% | -5.5604% |
| ETH | -7.8628% | -9.2947% |
| SOL | -7.2009% | -9.8807% |
| ADA | -5.8053% | -10.5930% |
| XRP | -7.3539% | -9.2374% |

There is no positive-price winner in this basket. BTC is least negative.
ADA falls most this week; ETH falls most this month. These are retrospective
rankings, not evidence the system could have identified the winner beforehand.

## Existing strategy counterfactual

Frozen breakout, EMA and mean-reversion presets; signal-only next-open replay,
not the campaign exit stack. Independent fresh $1,000 simulated accounts per
arm/window, fixed $100 entries, 50 bps taker fees and 5 bps slippage per side,
terminal exit costs included. Fresh windows answer this separate retrospective
question; they do not replace registered carry-forward confirmation accounts.

Month: ADA EMA +$5.8744 (+0.5874% of $1,000 account), the only positive arm.
Week: no positive arm; best arms stay in cash at $0. All outcomes, costs and
hashes are saved in `research/coinbase_retrospective_20261009/results.json`.
Shared approximately $20/month infrastructure is excluded; allocations are not
a combined portfolio, and the outcome-selected best arm is hindsight-biased.

These are CF-MODELLED, not live results or confirmation evidence. Actual live
gain cannot be established without orders/fills and actual execution conditions.
Shorts are absent from this simulator, so no captured short profit is claimed.
The registered prospective USD experiment and archive were not modified.

Reproduce with the isolated report module; its main output refuses overwrite.
Independent GATE ACCEPTED_WITH_RISK: exact report recomputation and all30
strategy/window cost, next-open and final-cash checks passed. Buy-and-hold dollar
figures in the JSON use $1,000 all-in, unlike $100 strategy entries; they are not
exposure-matched comparisons. No full-suite run: no production
code changed; existing strict archive and frozen simulator paths were executed.
