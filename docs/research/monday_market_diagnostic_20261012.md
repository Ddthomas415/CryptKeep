# Monday market diagnostic

Observed October12 08:50Eastern. AUDITOR; exploratory public market analysis.
No orders, portfolio changes, strategy tuning or frozen-study changes.

Source: research/monday_market_diagnostic_20261012_1.json contains public candles
and the GTC depth snapshot. Current top8 returned USD quote-volume proxies plus
BTC/GTC yielded9 unique products, includingUSDT. Universe is current, not historical.
Do not present this convenience universe as every listed coin or survivorship-free.

Each complete UTC Monday is measured from its open to Tuesday's open. Today is
excluded from historical statistics. Model fees0.5%per side; no spread/slippage or
real fill proof. Request182days; subsequent read-only assertions verified183unique
daily candles perproduct, exactgrid, positivefiniteOHLC and26completedMondays.

| Product | Today's partial UTC-open move | Monday mean after modeled fees | Monday median after modeled fees | Positive Mondays |
| --- | ---: | ---: | ---: | ---: |
| GTC | +66.78% | +2.44% | -0.37% |12/26|
| NEAR | -4.02% | +1.24% | +1.04% |17/26|
| BTC | -0.98% | -0.53% | -0.49% |10/26|
| ETH | approximately0.00% | -0.23% | -0.30% |11/26|

GTC's best historical Monday was+71.95%fee-adjusted. Excluding that one observation
reduces the mean to-0.34%; this is a concentration diagnostic, not permission to
discard it or optimize a new rule. Today's GTC spike is not part of that history.
NEAR is a candidate for further preregistered testing, not a demonstrated edge:
only26Mondays,9markets examined,currentlisting/volumebias,noholdout,noformal
multiple-testing or dependence-adjusted interval. Do not promote or trade this scan.

User explicitly requested theirGTC holding. A separate private read-only account
check succeeded; no account IDs, credential values or unrelatedholdings saved here.
GTC-only fillhistory returned no rows, so actualcostbasis/PnL remainsUNVERIFIED.
The public GTC snapshot shows0.3017reportedprice,0.2998bid/0.3013ask,about49.91bps
spread. Historical book-walk valuation isCF-MODELLED, not executable assurance.

At inspection the US9:30Eastern equityopen was future. NYSE listsOctober12 as an
ordinary stocktradingday; no claim about its subsequently observed opening move.
https://www.nyse.com/trade/hours-calendars
Gitcoin's Octoberreboot update is relevantcontext but not proof of today's rallycause:
https://gov.gitcoin.co/t/october-2026-gitcoin-reboot-update-techne-gets-a-name-a-pilot-and-a-launch-date/25394

Two targetedtests passed; separateGATE ACCEPTED_WITH_RISK for exploratory public
collection/arithmetic only. Profitability/edgeapproval not granted.

## All-weekday spike follow-up

User specifically requested recurring weekday spikes rather than only day-end
returns. Reused the preserved183dailycandles, excluding today's incomplete day;
no new downloads or changed studies. UTC April13 throughOctober11,26observations
perweekday. "Spike" here means dailyhigh relative to that day'sopen, not an
achievable roundtrip. 5%/10% thresholds are exploratory descriptive choices, not
registered entry/exit rules. Dailybars cannot locate the exact spikehour or prove
the sequence of stops/targets, fills or a tradable peak.

| GTC weekday | Median open-to-high move | Days reaching+5% | Days reaching+10% |
| --- | ---: | ---: | ---: |
| Monday |3.20%|10/26|4/26|
| Tuesday |1.23%|6/26|2/26|
| Wednesday |2.41%|9/26|3/26|
| Thursday |3.72%|11/26|6/26|
| Friday |4.18%|11/26|4/26|
| Saturday |2.96%|7/26|2/26|
| Sunday |1.92%|5/26|2/26|

The observed GTCspikes cluster more onThursday/Friday thanSunday in this window,
but are not present everyweek. Thursday5%counts split6/13 and5/13 across the two
halves; Friday4/13 and7/13. GTCFriday fee-adjusted open-to-next-open median remains
-0.29%, illustrating that an intraday spike can reverse before dayend.
NEARWednesday reached5% in13/26days, split6/13 and7/13. BTC5%spikes were rare;
day-level seasonality is coin-specific, not a universal Mondaybuyrule.

Relevant primaryresearch finds weekday/hourly volume and volatility periodicity:
https://arxiv.org/abs/2109.12142
Other studies report mixed dailyreturn results; intradaywindow and regime matter.
This literature motivates a hypothesis but does not establish currentGTC causality.
This added descriptive scan has no dependence-adjusted significance/holdout or
independent validation; economicweekdayedge remainsINCOMPLETE. Next useful test
is hourlyspiketime/reversal analysis with rules frozen before prospective evaluation,
not buying solely because the calendar saysThursday orFriday.
