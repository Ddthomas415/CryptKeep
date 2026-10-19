# Lessons from October 12 market observations

AUDITOR. Observation window ends09:11Eastern, before09:30US equityopen.
This is an intraday diagnostic, not a completed-day review or validated strategy.
No frozenstudy, tradingrule, order or risklimit changed.

## What is shown

- GTC fell from0.3017 at08:50 to0.2868 at09:11,about4.94%, despite remaining
  the Coinbase rolling24hleader. Quotes are distinct observations, not fills.
- Between09:08 and09:11,7of the savedtop10lostprice;3rose. Three minutes is
  not enough to establish a stable market/regime rule.
- RSR rose0.95% in that short interval. With provisional0.50%fees on each
  side, the price-proxy roundtrip is about-0.05% before spread/slippage.
  Formula:P1/P0*(1-.005)/(1+.005)-1. No actualentry/exit is claimed.
- ALEPH rose2.08% between observations despite not being the rolling24hleader.
- Earlier GTCbook spread was about49.91bps; displayedprice alone overstates
  immediate executable value. A historical depthwalk is not a guaranteed fill.

## Reusable research lessons

1. Rank rolling24hperformance separately from returns AFTER the signal was observed.
   Being the biggest pastgainer does not establish futurecontinuation.
2. Measure retracement from observed prices, not an unknowable intradaypeak. Preserve
   both the spike and reversal; never backdate an alert to its most favorable entry.
3. Evaluate incremental opportunity after fees and spread before describing it as
   profit. RSR's observed0.95%move illustrates that grossmovement can be insufficient.
4. Treat GTCweekdayfrequency as an opportunitycontext hypothesis, not a tradeentry.
   Exacthour,liquidity,execution and reversalpath need their own forwardtest.
5. An hourlywatch can miss rapidspikes/reversals. Do not represent it as real-time
   protection or assume it would have captured these three-minute changes.

## Evidence and limits

Public baselines: research/monday_market_diagnostic_20261012_1.json;
research/coinbase_gainers_watch_initial_20261012.json;
research/todays_market_learning_20261012T131127Z.json.
Lastsnapshothasfullavailablepagination coverage. Current-universe selection,
price-proxy execution, shortwindow and noholdout prevent profitabilityapproval.
No causalclaim about theUSopen: it had not occurred at inspection.
Marketobservations areSHOWN; repeatability/economicedge remainUNVERIFIED.

## Listing catalyst correction

October12 reporting identifies expanded Upbit GTC/KRW and GTC/USDT support;
Upbit's own asset page describes new-market support. Treat listing-related demand
as a plausible rally hypothesis, not established causality or guaranteed continuation.
The Gitcoin October1 Techne forum update is older background, not fresh news today.
Do not attribute this event-driven observation to Monday seasonality or use it as
independent validation of the historical weekday scan. Preserve earlier observations
and examine subsequent momentum, volume, liquidity and retracement separately.

Sources:
https://datalab.upbit.com/assets/GTC/summary
https://en.bloomingbit.io/feed/news/122023
https://gov.gitcoin.co/t/october-2026-gitcoin-reboot-update-techne-gets-a-name-a-pilot-and-a-launch-date/25394
No trade, strategy change or profitable forecast is implied.
